"""
LeaderboardCog — automatic scheduled leaderboard posting.

Each minute the scheduler checks whether any guild's leaderboard is due.
When triggered it:
  1. Queries the top-10 users (rank hierarchy → balance, identical to /identity)
  2. Fetches each member's avatar from Discord CDN
  3. Generates a premium vertical image table via leaderboard_card.py
  4. Posts to the configured channel:
       • A message with the real @user mentions (so they are clickable)
       • The premium image attached

Frequency types: daily | weekly | monthly
"""

import asyncio
import io
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
import discord
from discord.ext import commands, tasks

from bot.utils.leaderboard_card import generate_leaderboard_image

logger = logging.getLogger("kingdom_treasury")


# ─── Timezone helper ──────────────────────────────────────────────────────────

def _parse_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, Exception):
        return ZoneInfo("UTC")


# ─── Schedule check ───────────────────────────────────────────────────────────

def _is_due(settings: dict, now_utc: datetime) -> bool:
    """Return True if the leaderboard should post during this minute."""
    tz        = _parse_tz(settings.get("timezone") or "UTC")
    now_local = now_utc.astimezone(tz)

    post_hour   = int(settings.get("post_hour",   12))
    post_minute = int(settings.get("post_minute",  0))

    if now_local.hour != post_hour or now_local.minute != post_minute:
        return False

    last_posted = settings.get("last_posted_at")
    frequency   = settings.get("post_frequency", "daily")

    if last_posted is not None:
        if isinstance(last_posted, str):
            last_posted = datetime.fromisoformat(last_posted)
        if last_posted.tzinfo is None:
            last_posted = last_posted.replace(tzinfo=timezone.utc)

        elapsed = now_utc - last_posted

        if frequency == "daily" and elapsed < timedelta(hours=23):
            return False

        if frequency == "weekly":
            dow = settings.get("post_day_of_week")
            if dow is not None and now_local.weekday() != int(dow):
                return False
            if elapsed < timedelta(days=6, hours=23):
                return False

        if frequency == "monthly":
            dom = settings.get("post_day_of_month")
            if dom is not None and now_local.day != int(dom):
                return False
            if elapsed < timedelta(days=27):
                return False

    return True


# ─── Medal labels for mention block ───────────────────────────────────────────
MEDALS = ["🥇", "🥈", "🥉"]


# ─── Avatar fetcher ───────────────────────────────────────────────────────────

async def _fetch_avatar_bytes(
    session: aiohttp.ClientSession,
    url: str,
    size: int = 64,
) -> Optional[bytes]:
    """Download avatar PNG bytes from Discord CDN. Returns None on failure."""
    try:
        cdn_url = f"{url.split('?')[0]}?size={size}"
        async with session.get(cdn_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                return await resp.read()
    except Exception as exc:
        logger.debug(f"Avatar fetch failed for {url}: {exc}")
    return None


async def _none_bytes() -> None:
    """Dummy coroutine that resolves to None (for members not in cache)."""
    return None


async def _fetch_avatars(guild: discord.Guild, rows: list) -> list:
    """
    For each leaderboard row, resolve the guild member and fetch their avatar
    bytes from Discord CDN.  Returns a list parallel to rows.
    Members not found in cache, or failed fetches, resolve to None
    (the image renderer shows a placeholder circle in that case).
    """
    async with aiohttp.ClientSession() as session:
        coros = []
        for row in rows:
            discord_id = row.get("discord_id")
            member = guild.get_member(int(discord_id)) if discord_id else None
            if member:
                url = str(member.display_avatar.replace(format="png", size=64).url)
                coros.append(_fetch_avatar_bytes(session, url))
            else:
                coros.append(_none_bytes())

        results = await asyncio.gather(*coros, return_exceptions=True)

    # Swallow any exceptions — replace with None so the image still renders
    return [r if isinstance(r, bytes) else None for r in results]


# ─── Cog ─────────────────────────────────────────────────────────────────────

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.cancel()

    @tasks.loop(minutes=1)
    async def scheduler(self):
        try:
            await self._check_and_post()
        except Exception as e:
            logger.error(f"Leaderboard scheduler error: {e}", exc_info=True)

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    # ── Main scheduler tick ───────────────────────────────────────────────────

    async def _check_and_post(self):
        config_svc = getattr(self.bot, "config_service", None)
        if config_svc is None:
            return

        now_utc      = datetime.now(timezone.utc)
        all_settings = await config_svc.get_all_leaderboard_settings()

        for settings in all_settings:
            if not settings.get("enabled"):
                continue
            if not _is_due(settings, now_utc):
                continue

            guild_id   = settings["guild_id"]
            channel_id = settings.get("post_channel_id")
            if not channel_id:
                continue

            guild   = self.bot.get_guild(int(guild_id))
            channel = guild.get_channel(int(channel_id)) if guild else None

            if channel is None or not isinstance(channel, discord.TextChannel):
                logger.warning(
                    f"Leaderboard: channel {channel_id} not found or not text "
                    f"for guild {guild_id} — skipping."
                )
                continue

            guild_cfg = await config_svc.get_guild_config(guild_id)

            try:
                await self._post_leaderboard(channel, guild, guild_id, settings, guild_cfg)
                await config_svc.update_last_posted_at(guild_id)
            except Exception as exc:
                logger.error(
                    f"Leaderboard post failed for guild={guild_id}: {exc}",
                    exc_info=True,
                )

    # ── Build + send post ─────────────────────────────────────────────────────

    async def _post_leaderboard(
        self,
        channel: discord.TextChannel,
        guild: discord.Guild,
        guild_id: str,
        settings: dict,
        guild_cfg: dict,
    ):
        currency_name = guild_cfg.get("currency_name", "DevilCoins")
        currency_icon = guild_cfg.get("currency_icon", "🪙")

        # ── 1. Fetch ranking data (rank hierarchy → balance, same as /identity) ─
        try:
            rows = await self.bot.db.get_leaderboard(guild_id, limit=10)
        except Exception as exc:
            logger.warning(f"Leaderboard DB fetch failed for guild {guild_id}: {exc}")
            rows = []

        if not rows:
            logger.info(f"Leaderboard: no data for guild {guild_id} — skipping.")
            return

        # ── 2. Fetch member avatars ──────────────────────────────────────────
        try:
            avatar_data = await _fetch_avatars(guild, rows)
        except Exception as exc:
            logger.warning(f"Avatar fetch partial failure for guild {guild_id}: {exc}")
            avatar_data = [None] * len(rows)

        # ── 3. Generate premium image (CPU-bound → thread executor) ──────────
        freq_label = {
            "daily":   "Daily",
            "weekly":  "Weekly",
            "monthly": "Monthly",
        }.get(settings.get("post_frequency", "weekly"), "")

        tz        = _parse_tz(settings.get("timezone") or "UTC")
        now_local = datetime.now(timezone.utc).astimezone(tz)
        date_str  = now_local.strftime("%B %d, %Y  ·  %H:%M %Z")

        image_title    = f"{freq_label} Kingdom Leaderboard".strip()
        image_subtitle = "Ranked by hierarchy · then balance — mirrors /identity"

        loop = asyncio.get_event_loop()
        image_buf: io.BytesIO = await loop.run_in_executor(
            None,
            lambda: generate_leaderboard_image(
                rows          = rows,
                currency_name = currency_name,
                currency_icon = currency_icon,
                title         = image_title.upper(),
                subtitle      = image_subtitle,
                date_str      = date_str,
                avatar_data   = avatar_data,
            ),
        )

        # ── 4. Build the mention block ────────────────────────────────────────
        mention_lines = []
        for i, row in enumerate(rows[:10], start=1):
            discord_id = row.get("discord_id")
            rank       = row.get("rank", "Forsaken")
            balance    = int(row.get("balance", 0))

            medal  = MEDALS[i - 1] if i <= 3 else f"**#{i}**"
            mention = f"<@{discord_id}>" if discord_id else f"**{row.get('username', 'Unknown')}**"

            mention_lines.append(
                f"{medal}  {mention}  ·  **{rank}**  ·  "
                f"{currency_icon} `{balance:,}` {currency_name}"
            )

        mention_block = "\n".join(mention_lines)

        header_line = (
            f"## 🏆  {freq_label} Kingdom Leaderboard\n"
            f"-# Ranked by hierarchy, then balance — matches `/identity`"
        )

        message_text = f"{header_line}\n\n{mention_block}"

        # ── 5. Send: text message first, then image ───────────────────────────
        try:
            await channel.send(
                content = message_text,
                file    = discord.File(image_buf, filename="leaderboard.png"),
            )
            logger.info(
                f"Leaderboard posted → guild={guild_id}  channel={channel.id}  "
                f"users={len(rows)}"
            )
        except Exception as exc:
            logger.error(
                f"Failed to send leaderboard to channel {channel.id}: {exc}"
            )

