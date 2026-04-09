"""
LeaderboardCog — automatic scheduled leaderboard posting.

Checks every minute whether any enabled guild's leaderboard is due to post,
generates the embed, and sends it to the configured channel.

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
    tz       = _parse_tz(settings.get("timezone") or "UTC")
    now_local = now_utc.astimezone(tz)

    post_hour   = settings.get("post_hour", 12)
    post_minute = settings.get("post_minute", 0)

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
            if dow is not None and now_local.weekday() != dow:
                return False
            if elapsed < timedelta(days=6, hours=23):
                return False
        if frequency == "monthly":
            dom = settings.get("post_day_of_month")
            if dom is not None and now_local.day != dom:
                return False
            if elapsed < timedelta(days=27):
                return False

    return True


LEADERBOARD_COLORS = {
    "wealth":  0xFFD700,
    "grind":   0xB22222,
    "tribute": 0x8B0000,
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

        now_utc = datetime.now(timezone.utc)
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
                continue

            await self._post_leaderboard(channel, guild_id, settings)
            await config_svc.update_last_posted_at(guild_id)

    async def _post_leaderboard(
        self,
        channel: discord.TextChannel,
        guild_id: str,
        settings: dict,
    ):
        board_type = settings.get("leaderboard_type", "wealth")

        try:
            rows = await self.bot.db.get_leaderboard(guild_id, limit=10)
        except Exception:
            rows = []

        if not rows:
            return

        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, row in enumerate(rows[:10]):
            prefix = medals[i] if i < 3 else f"**{i + 1}.**"
            name   = row.get("username", "Unknown")
            bal    = row.get("balance", 0)
            rank   = row.get("rank", "Forsaken")
            lines.append(f"{prefix} **{name}** — `{bal:,} DC` · *{rank}*")

        title = {
            "wealth":  "💰  Wealth Leaderboard",
            "grind":   "⛏  Grind Leaderboard",
            "tribute": "👑  Tribute Leaderboard",
        }.get(board_type, "🏆  Leaderboard")

        embed = discord.Embed(
            title       = title,
            description = "\n".join(lines) if lines else "*No data yet.*",
            color       = LEADERBOARD_COLORS.get(board_type, 0xFFD700),
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
            logger.info(f"Posted leaderboard to guild={guild_id} channel={channel.id}")
        except Exception as e:
            logger.warning(f"Failed to post leaderboard: {e}")
