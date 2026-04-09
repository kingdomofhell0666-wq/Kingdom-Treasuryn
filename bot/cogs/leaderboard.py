"""
LeaderboardCog — automatic scheduled leaderboard posting.

Checks every minute whether any enabled guild's leaderboard is due to post,
generates the embed, and sends it to the configured channel.

The ranking uses the same balance-based ordering as /identity — position 1
has the highest balance, matching the Kingdom Identity Card exactly.

Frequency types: daily | weekly | monthly
"""

import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks

logger = logging.getLogger("kingdom_treasury")


def _parse_tz(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, Exception):
        return ZoneInfo("UTC")


def _is_due(settings: dict, now_utc: datetime) -> bool:
    """Return True if the leaderboard should be posted now (within this minute)."""
    tz        = _parse_tz(settings.get("timezone") or "UTC")
    now_local = now_utc.astimezone(tz)

    post_hour   = int(settings.get("post_hour", 12))
    post_minute = int(settings.get("post_minute", 0))

    if now_local.hour != post_hour or now_local.minute != post_minute:
        return False

    last_posted = settings.get("last_posted_at")
    frequency   = settings.get("post_frequency", "daily")

    if last_posted is None:
        pass  # Never posted — do it now
    else:
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


BOARD_META = {
    "wealth":  {"emoji": "💰", "label": "Wealth", "color": 0xFFD700},
    "grind":   {"emoji": "⛏",  "label": "Grind",   "color": 0xB22222},
    "tribute": {"emoji": "👑", "label": "Tribute", "color": 0x8B0000},
}

MEDALS = ["🥇", "🥈", "🥉"]

RANK_FLAVOR = {
    "Forsaken":    "the damned",
    "Vermin":      "a crawling wretch",
    "Corrupted":   "a tainted soul",
    "Mythology":   "a legend in shadow",
    "Folklore":    "a whispered name",
    "Eschatology": "a herald of endings",
    "Demonology":  "a student of darkness",
    "Archangel":   "a fallen light",
    "Archdemon":   "a lord of the abyss",
    "Knight":      "a blade of the realm",
    "Baron":       "a lord of the pit",
    "Viscount":    "a noble of shadow",
    "Count":       "a lord of many souls",
    "Marquis":     "a marquis of ruin",
    "Duke":        "a duke of hell",
    "Chancellor":  "the hand of the Kingdom",
}


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

    async def _check_and_post(self):
        config_svc = getattr(self.bot, "config_service", None)
        if config_svc is None:
            return

        now_utc      = datetime.now(timezone.utc)
        all_settings = await config_svc.get_all_leaderboard_settings()

        for settings in all_settings:
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
                    f"Leaderboard: channel {channel_id} not found or not a text channel "
                    f"for guild {guild_id} — skipping."
                )
                continue

            guild_cfg = await config_svc.get_guild_config(guild_id)
            await self._post_leaderboard(channel, guild_id, settings, guild_cfg)
            await config_svc.update_last_posted_at(guild_id)

    async def _post_leaderboard(
        self,
        channel: discord.TextChannel,
        guild_id: str,
        settings: dict,
        guild_cfg: dict,
    ):
        board_type    = settings.get("leaderboard_type", "wealth")
        currency_name = guild_cfg.get("currency_name", "DevilCoins")
        currency_icon = guild_cfg.get("currency_icon", "🪙")
        meta          = BOARD_META.get(board_type, BOARD_META["wealth"])

        # ── Fetch leaderboard data (same ORDER BY balance DESC as /identity) ──
        try:
            rows = await self.bot.db.get_leaderboard(guild_id, limit=10)
        except Exception as e:
            logger.warning(f"Leaderboard data fetch failed for guild {guild_id}: {e}")
            rows = []

        if not rows:
            logger.info(f"Leaderboard: no data yet for guild {guild_id} — skipping post.")
            return

        # ── Build lines ───────────────────────────────────────────────────────
        lines = []
        for i, row in enumerate(rows[:10]):
            prefix   = MEDALS[i] if i < 3 else f"**#{i + 1}**"
            name     = row.get("username", "Unknown Soul")
            bal      = int(row.get("balance", 0))
            kingdom_rank = row.get("rank", "Forsaken")
            flavor   = RANK_FLAVOR.get(kingdom_rank, kingdom_rank)
            lines.append(
                f"{prefix} **{name}**  ·  {currency_icon} `{bal:,}` {currency_name}\n"
                f"    *{flavor}* — {kingdom_rank}"
            )

        # ── Frequency label for the header ────────────────────────────────────
        freq_label = {
            "daily":   "Daily",
            "weekly":  "Weekly",
            "monthly": "Monthly",
        }.get(settings.get("post_frequency", "daily"), "")

        title = f"{meta['emoji']}  {freq_label} {meta['label']} Leaderboard".strip()

        tz        = _parse_tz(settings.get("timezone") or "UTC")
        now_local = datetime.now(timezone.utc).astimezone(tz)

        embed = discord.Embed(
            title       = title,
            description = "\n\n".join(lines),
            color       = meta["color"],
        )
        embed.set_author(name="Kingdom of Hell  ·  Kingdom Treasury")
        embed.set_footer(
            text=f"Ranked by {meta['label'].lower()}  ·  {now_local.strftime('%B %d, %Y')}"
        )
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
            logger.info(
                f"Posted {board_type} leaderboard to guild={guild_id} channel={channel.id}"
            )
        except Exception as e:
            logger.warning(f"Failed to post leaderboard to channel {channel.id}: {e}")
