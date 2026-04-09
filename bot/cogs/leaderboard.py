"""
LeaderboardCog — bot-first, dashboard-override scheduled leaderboard posting.

Channel resolution — strict priority
──────────────────────────────────────
1. Dashboard config channel_id (if row exists AND channel_id is non-null/non-empty)
2. Hard-default channel: DEFAULT_LEADERBOARD_CHANNEL_ID
3. If resolved channel cannot be used → log error, abort. NO random fallback.

The bot NEVER walks guild channels or guesses. If neither the dashboard channel
nor the default channel is reachable, the post is suppressed and logged.

Ranking rule (identical to /identity)
──────────────────────────────────────
  PRIMARY:   rank hierarchy (Duke=14 … Forsaken=0)
  SECONDARY: balance descending

Leaderboard type: FIXED → Kingdom Rank Top 10 (no other modes).
"""

import asyncio
import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
import discord
from discord.ext import commands, tasks

from bot.utils.leaderboard_card import generate_leaderboard_image

logger = logging.getLogger("kingdom_treasury")


# ─── Hard-locked default channel ─────────────────────────────────────────────
# Used when the dashboard has no explicit override.
# Changed only when the dashboard saves a valid non-null channel_id.

DEFAULT_LEADERBOARD_CHANNEL_ID = "1488243375579861012"   # #📊┃leaderboard


# ─── Fallback schedule defaults ───────────────────────────────────────────────

FALLBACK_FREQUENCY    = "weekly"
FALLBACK_POST_HOUR    = 20
FALLBACK_POST_MINUTE  = 0
FALLBACK_TIMEZONE     = "UTC"
LEADERBOARD_TYPE      = "kingdom_rank_top_10"   # fixed — never changes


# ─── Effective config dataclass ───────────────────────────────────────────────

@dataclass
class EffectiveLeaderboardConfig:
    source:             str             # "dashboard" | "fallback"
    enabled:            bool
    leaderboard_type:   str             # always LEADERBOARD_TYPE
    post_channel_id:    str             # always a non-None channel ID string
    channel_source:     str             # "dashboard" | "default"
    post_frequency:     str             # "daily" | "weekly" | "monthly"
    post_hour:          int
    post_minute:        int
    post_day_of_week:   Optional[int]
    post_day_of_month:  Optional[int]
    timezone:           str
    last_posted_at:     Optional[datetime]
    resolved_strategy:  str


# ─── Config resolver ──────────────────────────────────────────────────────────

async def resolve_leaderboard_config(
    guild_id:       str,
    config_service,
) -> EffectiveLeaderboardConfig:
    """
    Load the dashboard config from PostgreSQL.
    Return an EffectiveLeaderboardConfig for this guild.

    Dashboard channel is used ONLY when the DB row exists AND post_channel_id
    is non-null and non-empty.  Every other case uses DEFAULT_LEADERBOARD_CHANNEL_ID.
    """
    rows = await config_service.get_leaderboard_settings_for_guild(guild_id)

    if rows and rows.get("enabled") is not None:
        r   = rows
        lpa = r.get("last_posted_at")
        if lpa is not None and isinstance(lpa, str):
            try:
                lpa = datetime.fromisoformat(lpa)
            except Exception:
                lpa = None
        if lpa is not None and lpa.tzinfo is None:
            lpa = lpa.replace(tzinfo=timezone.utc)

        # Dashboard has an explicit, non-null channel_id → use it.
        # Otherwise fall through to the hard-locked default.
        db_channel_id = (r.get("post_channel_id") or "").strip() or None
        if db_channel_id:
            post_channel_id = db_channel_id
            channel_source  = "dashboard"
        else:
            post_channel_id = DEFAULT_LEADERBOARD_CHANNEL_ID
            channel_source  = "default"

        return EffectiveLeaderboardConfig(
            source            = "dashboard",
            enabled           = bool(r["enabled"]),
            leaderboard_type  = LEADERBOARD_TYPE,
            post_channel_id   = post_channel_id,
            channel_source    = channel_source,
            post_frequency    = r.get("post_frequency") or FALLBACK_FREQUENCY,
            post_hour         = int(r.get("post_hour") or FALLBACK_POST_HOUR),
            post_minute       = int(r.get("post_minute") or FALLBACK_POST_MINUTE),
            post_day_of_week  = r.get("post_day_of_week"),
            post_day_of_month = r.get("post_day_of_month"),
            timezone          = r.get("timezone") or FALLBACK_TIMEZONE,
            last_posted_at    = lpa,
            resolved_strategy = (
                f"dashboard: enabled={r['enabled']} "
                f"channel_source={channel_source} "
                f"channel={post_channel_id} "
                f"freq={r.get('post_frequency')}"
            ),
        )

    # ── Fallback: no valid dashboard row — use hard-locked default ─────────────
    return EffectiveLeaderboardConfig(
        source            = "fallback",
        enabled           = True,
        leaderboard_type  = LEADERBOARD_TYPE,
        post_channel_id   = DEFAULT_LEADERBOARD_CHANNEL_ID,
        channel_source    = "default",
        post_frequency    = FALLBACK_FREQUENCY,
        post_hour         = FALLBACK_POST_HOUR,
        post_minute       = FALLBACK_POST_MINUTE,
        post_day_of_week  = None,
        post_day_of_month = None,
        timezone          = FALLBACK_TIMEZONE,
        last_posted_at    = None,
        resolved_strategy = f"fallback: no valid dashboard config — using default channel={DEFAULT_LEADERBOARD_CHANNEL_ID}",
    )


# ─── Timezone helper ──────────────────────────────────────────────────────────

def _parse_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except (ZoneInfoNotFoundError, Exception):
        return ZoneInfo("UTC")


# ─── Schedule check ───────────────────────────────────────────────────────────

def _is_due(cfg: EffectiveLeaderboardConfig, now_utc: datetime) -> bool:
    """Return True if the leaderboard should post during this minute."""
    tz        = _parse_tz(cfg.timezone)
    now_local = now_utc.astimezone(tz)

    if now_local.hour != cfg.post_hour or now_local.minute != cfg.post_minute:
        return False

    last_posted = cfg.last_posted_at
    frequency   = cfg.post_frequency

    if last_posted is not None:
        elapsed = now_utc - last_posted

        if frequency == "daily" and elapsed < timedelta(hours=23):
            return False

        if frequency == "weekly":
            if cfg.post_day_of_week is not None and now_local.weekday() != int(cfg.post_day_of_week):
                return False
            if elapsed < timedelta(days=6, hours=23):
                return False

        if frequency == "monthly":
            if cfg.post_day_of_month is not None and now_local.day != int(cfg.post_day_of_month):
                return False
            if elapsed < timedelta(days=27):
                return False

    return True


# ─── Channel resolution ───────────────────────────────────────────────────────

async def _resolve_channel(
    guild:      discord.Guild,
    channel_id: str,
) -> Optional[discord.abc.Messageable]:
    """
    Resolve a sendable channel from a specific ID.

    STRICT — no guild channel walk, no keyword guessing.
    Returns None only when the given ID is unreachable or unsendable.
    The caller must then abort and log; it must NOT pick a random fallback.
    """
    try:
        raw = int(channel_id)
    except (ValueError, TypeError):
        logger.warning(f"[Leaderboard ERROR] channel_id {channel_id!r} is not a valid integer — cannot resolve")
        return None

    ch = guild.get_channel(raw)
    if ch is None:
        logger.info(f"[Leaderboard] channel {raw} not in guild cache — calling fetch_channel()")
        try:
            ch = await guild.fetch_channel(raw)
        except discord.NotFound:
            logger.warning(f"[Leaderboard ERROR] channel {raw} not found (NotFound)")
            return None
        except discord.Forbidden:
            logger.warning(f"[Leaderboard ERROR] channel {raw} fetch forbidden (no permission)")
            return None
        except Exception as exc:
            logger.warning(f"[Leaderboard ERROR] fetch_channel({raw}) failed: {exc}")
            return None

    if ch is not None and hasattr(ch, "send"):
        return ch

    if ch is not None:
        logger.warning(
            f"[Leaderboard ERROR] channel {raw} resolved to {type(ch).__name__} "
            f"which has no send() — cannot use"
        )
    return None


# ─── Medal labels ─────────────────────────────────────────────────────────────

MEDALS = ["🥇", "🥈", "🥉"]


# ─── Avatar fetcher ───────────────────────────────────────────────────────────

async def _fetch_avatar_bytes(session: aiohttp.ClientSession, url: str, size: int = 64) -> Optional[bytes]:
    try:
        cdn_url = f"{url.split('?')[0]}?size={size}"
        async with session.get(cdn_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                return await resp.read()
    except Exception as exc:
        logger.debug(f"Avatar fetch failed for {url}: {exc}")
    return None


async def _none_bytes() -> None:
    return None


async def _fetch_avatars(guild: discord.Guild, rows: list) -> list:
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
            logger.error(f"[Leaderboard] scheduler tick error: {e}", exc_info=True)

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    # ── Per-minute scheduler tick ─────────────────────────────────────────────

    async def _check_and_post(self):
        config_svc = getattr(self.bot, "config_service", None)
        if config_svc is None:
            return

        now_utc = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            try:
                await self._process_guild(guild, config_svc, now_utc)
            except Exception as exc:
                logger.error(
                    f"[Leaderboard] unhandled error in guild={guild.id}: {exc}",
                    exc_info=True,
                )

    async def _process_guild(
        self,
        guild:      discord.Guild,
        config_svc,
        now_utc:    datetime,
    ):
        guild_id = str(guild.id)

        # ── 1. Resolve effective config ────────────────────────────────────────
        cfg = await resolve_leaderboard_config(guild_id, config_svc)

        logger.debug(
            f"[Leaderboard] config_source={cfg.source} "
            f"enabled={cfg.enabled} "
            f"channel_source={cfg.channel_source} "
            f"channel_id={cfg.post_channel_id} "
            f"frequency={cfg.post_frequency} "
            f"timezone={cfg.timezone} "
            f"guild={guild_id}"
        )

        # ── 2. Respect explicit disable ────────────────────────────────────────
        if not cfg.enabled:
            return

        # ── 3. Check schedule ─────────────────────────────────────────────────
        if not _is_due(cfg, now_utc):
            return

        logger.info(
            f"[Leaderboard] schedule due — guild={guild_id} "
            f"source={cfg.source} freq={cfg.post_frequency}"
        )

        # ── 4. Resolve channel (strict — no random fallback) ──────────────────
        channel = await _resolve_channel(guild, cfg.post_channel_id)

        if channel is None:
            logger.warning(
                f"[Leaderboard ERROR] guild={guild_id} "
                f"channel_source={cfg.channel_source} "
                f"channel_id={cfg.post_channel_id} "
                f"— channel unreachable, post suppressed"
            )
            return

        logger.info(
            f"[Leaderboard] channel_source={cfg.channel_source} "
            f"channel_id={channel.id}"
        )

        # ── 5. Fetch guild config (currency) ──────────────────────────────────
        guild_cfg     = await config_svc.get_guild_config(guild_id)
        currency_name = guild_cfg.get("currency_name", "DevilCoins")
        currency_icon = guild_cfg.get("currency_icon", "🪙")

        # ── 6. Post the leaderboard ───────────────────────────────────────────
        success = await self._post_leaderboard(
            channel       = channel,
            guild         = guild,
            guild_id      = guild_id,
            cfg           = cfg,
            currency_name = currency_name,
            currency_icon = currency_icon,
        )

        # ── 7. Update last_posted_at ──────────────────────────────────────────
        if success:
            await config_svc.upsert_last_posted_at(guild_id)

    # ── Build + send post ─────────────────────────────────────────────────────

    async def _post_leaderboard(
        self,
        channel:       discord.abc.Messageable,
        guild:         discord.Guild,
        guild_id:      str,
        cfg:           EffectiveLeaderboardConfig,
        currency_name: str,
        currency_icon: str,
    ) -> bool:
        """Generate and send the leaderboard.  Returns True on success."""
        logger.info(f"[Leaderboard] generating top 10 kingdom ranks for guild={guild_id}")

        # ── 1. Fetch ranking data (rank hierarchy → balance, same as /identity) ─
        try:
            rows = await self.bot.db.get_leaderboard(guild_id, limit=10)
        except Exception as exc:
            logger.warning(f"[Leaderboard] DB fetch failed for guild={guild_id}: {exc}")
            rows = []

        if not rows:
            logger.info(f"[Leaderboard] no data for guild={guild_id} — skipping")
            return False

        # ── 2. Fetch member avatars ───────────────────────────────────────────
        try:
            avatar_data = await _fetch_avatars(guild, rows)
        except Exception as exc:
            logger.warning(f"[Leaderboard] avatar fetch partial failure: {exc}")
            avatar_data = [None] * len(rows)

        # ── 3. Generate premium image ─────────────────────────────────────────
        freq_label = {
            "daily": "Daily", "weekly": "Weekly", "monthly": "Monthly",
        }.get(cfg.post_frequency, "")

        tz        = _parse_tz(cfg.timezone)
        now_local = datetime.now(timezone.utc).astimezone(tz)
        date_str  = now_local.strftime("%B %d, %Y  ·  %H:%M %Z")

        image_title    = f"{freq_label} Kingdom Leaderboard".strip()
        image_subtitle = "Ranked by hierarchy · then balance — mirrors /identity"

        loop      = asyncio.get_event_loop()
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

        # ── 4. Build mention block ────────────────────────────────────────────
        mention_lines = []
        for i, row in enumerate(rows[:10], start=1):
            discord_id = row.get("discord_id")
            rank       = row.get("rank", "Forsaken")
            balance    = int(row.get("balance", 0))
            medal      = MEDALS[i - 1] if i <= 3 else f"**#{i}**"
            mention    = f"<@{discord_id}>" if discord_id else f"**{row.get('username', 'Unknown')}**"
            mention_lines.append(
                f"{medal}  {mention}  ·  **{rank}**  ·  "
                f"{currency_icon} `{balance:,}` {currency_name}"
            )

        header = (
            f"## 🏆  {freq_label} Kingdom Leaderboard\n"
            f"-# Ranked by hierarchy, then balance — matches `/identity`"
        )
        message_text = f"{header}\n\n" + "\n".join(mention_lines)

        # ── 5. Send ───────────────────────────────────────────────────────────
        try:
            sent = await channel.send(
                content = message_text,
                file    = discord.File(image_buf, filename="leaderboard.png"),
            )
            logger.info(
                f"[Leaderboard] success message_id={sent.id} "
                f"guild={guild_id} channel={channel.id} (#{channel.name}) "
                f"users={len(rows)}"
            )
            return True
        except discord.Forbidden:
            logger.warning(
                f"[Leaderboard ERROR] permission denied sending to "
                f"#{channel.name} ({channel.id}) in guild={guild_id}"
            )
        except Exception as exc:
            logger.error(
                f"[Leaderboard ERROR] send failed for guild={guild_id} "
                f"channel={channel.id}: {exc}",
                exc_info=True,
            )
        return False

    # ── Admin: manual trigger via /post_leaderboard ───────────────────────────

    async def force_post(self, guild: discord.Guild):
        """
        Forcibly post the leaderboard for a guild right now (bypasses schedule check).
        Called by admin commands.  Returns True on success.
        """
        config_svc = getattr(self.bot, "config_service", None)
        if config_svc is None:
            return False

        guild_id = str(guild.id)
        cfg      = await resolve_leaderboard_config(guild_id, config_svc)

        channel = await _resolve_channel(guild, cfg.post_channel_id)
        if channel is None:
            logger.warning(
                f"[Leaderboard ERROR] force_post: guild={guild_id} "
                f"channel_source={cfg.channel_source} "
                f"channel_id={cfg.post_channel_id} "
                f"— channel unreachable, post suppressed"
            )
            return False

        logger.info(
            f"[Leaderboard] force_post channel_source={cfg.channel_source} "
            f"channel_id={channel.id}"
        )

        guild_cfg     = await config_svc.get_guild_config(guild_id)
        currency_name = guild_cfg.get("currency_name", "DevilCoins")
        currency_icon = guild_cfg.get("currency_icon", "🪙")

        success = await self._post_leaderboard(
            channel       = channel,
            guild         = guild,
            guild_id      = guild_id,
            cfg           = cfg,
            currency_name = currency_name,
            currency_icon = currency_icon,
        )
        if success:
            await config_svc.upsert_last_posted_at(guild_id)
        return success
