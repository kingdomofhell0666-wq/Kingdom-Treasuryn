"""
LeaderboardCog — Weekly Kingdom Ranks: Top 10

Schedule: every Monday at 10:00 AM (timezone-aware, configurable via dashboard).

Ranking logic:
  PRIMARY  — weekly_active_seconds DESC   (most active in voice/activity)
  SECONDARY — weekly_dc_earned DESC       (most DevilCoins earned this week)
  TERTIARY — eligible rank hierarchy      (Duke > … > Forsaken, tiebreaker only)
  FALLBACK  — discord_id ASC             (stable, never random)

Eligible groups: Nobility + Members only.
Excluded: Owners, Royal Family, Council, Legion (verified against live roles).

After a successful post, weekly stats are immediately reset for the new week.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks

from bot.utils.identity_variant import resolve_identity_card_variant

logger = logging.getLogger("kingdom_treasury")

# ─── Hard-locked defaults ─────────────────────────────────────────────────────

DEFAULT_LEADERBOARD_CHANNEL_ID = "1488243375579861012"   # #📊┃leaderboard

FALLBACK_FREQUENCY       = "weekly"
FALLBACK_POST_HOUR       = 10       # 10 AM
FALLBACK_POST_MINUTE     = 0
FALLBACK_POST_DAY_OF_WEEK = 0      # Monday (Python weekday)
FALLBACK_TIMEZONE        = "UTC"

LEADERBOARD_TYPE = "kingdom_rank_top_10"

# ─── DevilCoin emoji ──────────────────────────────────────────────────────────

_DC = "<:devilcoinStack:1492184333392412692>"

# ─── Top-3 display data ───────────────────────────────────────────────────────

_TOP3_MEDAL = ["👑", "⚔️", "🩸"]
_TOP3_TITLE = ["Sovereign of the Week", "Warlord Ascendant", "Blooded Challenger"]


# ─── Effective config dataclass ───────────────────────────────────────────────

@dataclass
class EffectiveLeaderboardConfig:
    source:             str
    enabled:            bool
    leaderboard_type:   str
    post_channel_id:    str
    channel_source:     str
    post_frequency:     str
    post_hour:          int
    post_minute:        int
    post_day_of_week:   Optional[int]
    post_day_of_month:  Optional[int]
    timezone:           str
    last_posted_at:     Optional[datetime]
    resolved_strategy:  str


# ─── Config resolver ──────────────────────────────────────────────────────────

async def resolve_leaderboard_config(
    guild_id: str,
    config_service,
) -> EffectiveLeaderboardConfig:
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

        db_channel_id = (r.get("post_channel_id") or "").strip() or None
        post_channel_id = db_channel_id or DEFAULT_LEADERBOARD_CHANNEL_ID
        channel_source  = "dashboard" if db_channel_id else "default"

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

    return EffectiveLeaderboardConfig(
        source            = "fallback",
        enabled           = True,
        leaderboard_type  = LEADERBOARD_TYPE,
        post_channel_id   = DEFAULT_LEADERBOARD_CHANNEL_ID,
        channel_source    = "default",
        post_frequency    = FALLBACK_FREQUENCY,
        post_hour         = FALLBACK_POST_HOUR,
        post_minute       = FALLBACK_POST_MINUTE,
        post_day_of_week  = FALLBACK_POST_DAY_OF_WEEK,
        post_day_of_month = None,
        timezone          = FALLBACK_TIMEZONE,
        last_posted_at    = None,
        resolved_strategy = f"fallback: default channel={DEFAULT_LEADERBOARD_CHANNEL_ID}",
    )


# ─── Timezone helper ──────────────────────────────────────────────────────────

def _parse_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except (ZoneInfoNotFoundError, Exception):
        return ZoneInfo("UTC")


# ─── Schedule check ───────────────────────────────────────────────────────────

def _is_due(cfg: EffectiveLeaderboardConfig, now_utc: datetime) -> bool:
    """Return True if the leaderboard should fire during this minute."""
    tz        = _parse_tz(cfg.timezone)
    now_local = now_utc.astimezone(tz)

    if now_local.hour != cfg.post_hour or now_local.minute != cfg.post_minute:
        return False

    last_posted = cfg.last_posted_at
    frequency   = cfg.post_frequency

    if frequency == "weekly":
        day_of_week = cfg.post_day_of_week
        if day_of_week is not None and now_local.weekday() != int(day_of_week):
            return False
        if last_posted is not None:
            elapsed = now_utc - last_posted
            if elapsed < timedelta(days=6, hours=23):
                return False

    elif frequency == "daily":
        if last_posted is not None and (now_utc - last_posted) < timedelta(hours=23):
            return False

    elif frequency == "monthly":
        if cfg.post_day_of_month is not None and now_local.day != int(cfg.post_day_of_month):
            return False
        if last_posted is not None and (now_utc - last_posted) < timedelta(days=27):
            return False

    return True


# ─── Channel resolution ───────────────────────────────────────────────────────

async def _resolve_channel(
    guild: discord.Guild,
    channel_id: str,
) -> Optional[discord.abc.Messageable]:
    try:
        raw = int(channel_id)
    except (ValueError, TypeError):
        logger.warning(f"[Leaderboard] channel_id {channel_id!r} is not a valid integer")
        return None

    ch = guild.get_channel(raw)
    if ch is None:
        try:
            ch = await guild.fetch_channel(raw)
        except discord.NotFound:
            logger.warning(f"[Leaderboard] channel {raw} not found")
            return None
        except discord.Forbidden:
            logger.warning(f"[Leaderboard] channel {raw} fetch forbidden")
            return None
        except Exception as exc:
            logger.warning(f"[Leaderboard] fetch_channel({raw}) failed: {exc}")
            return None

    if ch is not None and hasattr(ch, "send"):
        return ch
    return None


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _fmt_duration(seconds: int) -> str:
    """Convert seconds to a compact 'Xh Ym' string."""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m      = rem // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def _build_leaderboard_message(rows: List[dict]) -> str:
    """Build the full leaderboard text in Kingdom of Hell style."""
    sep = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    intro = (
        f"## 📊  Kingdom Ranks — Weekly Top 10\n"
        f"{sep}\n\n"
        "*The Kingdom has judged the week.*\n\n"
        "*Time has been counted.\n"
        "Wealth has been measured.\n"
        "Only the most active have risen.*\n\n"
        "*Ten names stand above the rest.*\n\n"
        "*The weak disappear.\n"
        "The relentless remain.*\n\n"
        f"{sep}\n"
    )

    lines: List[str] = [intro]

    for i, row in enumerate(rows[:10], start=1):
        discord_id = row.get("discord_id")
        rank       = row.get("rank", "Forsaken")
        active_s   = int(row.get("weekly_active_seconds", 0))
        dc_earned  = int(row.get("weekly_dc_earned", 0))
        mention    = f"<@{discord_id}>" if discord_id else f"**{row.get('username', 'Unknown')}**"
        activity   = _fmt_duration(active_s)

        if i <= 3:
            medal      = _TOP3_MEDAL[i - 1]
            title_line = _TOP3_TITLE[i - 1]
            block = (
                f"{medal} **#{i} — {mention}**\n"
                f"*{title_line}*\n"
                f"Activity: **{activity}** · "
                f"Weekly Earned: **{dc_earned:,}** {_DC} · "
                f"Rank: **{rank}**\n"
            )
            lines.append(block)
        else:
            line = (
                f"**#{i}** — {mention} — "
                f"{activity} — "
                f"{dc_earned:,} {_DC} — "
                f"**{rank}**"
            )
            lines.append(line)

    lines.append(f"\n{sep}")
    lines.append(
        '-# *"The Abyss remembers those who move… and forgets those who idle."*'
    )

    return "\n".join(lines)


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

    # ── Per-minute tick ───────────────────────────────────────────────────────

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
        cfg      = await resolve_leaderboard_config(guild_id, config_svc)

        logger.debug(
            f"[Leaderboard] config_source={cfg.source} enabled={cfg.enabled} "
            f"channel={cfg.post_channel_id} freq={cfg.post_frequency} "
            f"day_of_week={cfg.post_day_of_week} hour={cfg.post_hour} "
            f"tz={cfg.timezone} guild={guild_id}"
        )

        if not cfg.enabled:
            return
        if not _is_due(cfg, now_utc):
            return

        logger.info(
            f"[Leaderboard] schedule due — guild={guild_id} "
            f"source={cfg.source} freq={cfg.post_frequency}"
        )

        channel = await _resolve_channel(guild, cfg.post_channel_id)
        if channel is None:
            logger.warning(
                f"[Leaderboard ERROR] guild={guild_id} channel={cfg.post_channel_id} "
                f"unreachable — post suppressed"
            )
            return

        success = await self._post_leaderboard(
            channel  = channel,
            guild    = guild,
            guild_id = guild_id,
        )

        if success:
            await config_svc.upsert_last_posted_at(guild_id)
            # Immediately reset weekly stats after a successful post
            await self.bot.db.reset_weekly_stats(guild_id)
            logger.info(
                f"[Leaderboard] weekly stats reset for guild={guild_id} "
                f"after successful post"
            )

    # ── Build + send ──────────────────────────────────────────────────────────

    async def _post_leaderboard(
        self,
        channel:  discord.abc.Messageable,
        guild:    discord.Guild,
        guild_id: str,
    ) -> bool:
        logger.info(f"[Leaderboard] building weekly top 10 for guild={guild_id}")

        # 1. Fetch candidates from DB (returns up to 25 eligible-rank rows)
        try:
            candidates = await self.bot.db.get_weekly_kingdom_leaderboard(
                guild_id, limit=25
            )
        except Exception as exc:
            logger.warning(f"[Leaderboard] DB fetch failed for guild={guild_id}: {exc}")
            candidates = []

        # 2. Filter by live Discord role eligibility
        rows = await self._filter_eligible(guild, candidates, limit=10)

        if not rows:
            logger.info(
                f"[Leaderboard] no eligible data for guild={guild_id} — skipping"
            )
            return False

        # 3. Build and send the message
        message_text = _build_leaderboard_message(rows)

        try:
            sent = await channel.send(content=message_text)
            logger.info(
                f"[Leaderboard] posted message_id={sent.id} "
                f"guild={guild_id} channel={channel.id} users={len(rows)}"
            )
            return True
        except discord.Forbidden:
            logger.warning(
                f"[Leaderboard ERROR] permission denied sending to "
                f"channel={channel.id} guild={guild_id}"
            )
        except Exception as exc:
            logger.error(
                f"[Leaderboard ERROR] send failed guild={guild_id}: {exc}",
                exc_info=True,
            )
        return False

    async def _filter_eligible(
        self,
        guild:      discord.Guild,
        candidates: List[dict],
        limit:      int = 10,
    ) -> List[dict]:
        """
        Cross-reference candidates against live Discord role data.
        Excludes members whose highest role is Owners / Royal Family /
        Council / Legion (i.e. kingdom_rank_eligible == False).
        """
        eligible: List[dict] = []

        for row in candidates:
            discord_id = row.get("discord_id")
            if not discord_id:
                continue

            try:
                member = guild.get_member(int(discord_id))
                if member is None:
                    member = await guild.fetch_member(int(discord_id))
            except (discord.NotFound, discord.HTTPException):
                member = None

            if member is None:
                continue

            role_ids = [str(r.id) for r in member.roles]
            variant  = resolve_identity_card_variant(role_ids, row.get("rank", "Forsaken"))

            if not variant.kingdom_rank_eligible:
                continue

            eligible.append(row)
            if len(eligible) >= limit:
                break

        return eligible

    # ── Admin: force post (bypasses schedule check) ───────────────────────────

    async def force_post(self, guild: discord.Guild) -> bool:
        """
        Force-post the weekly leaderboard immediately.
        Called by admin commands.  Does NOT reset weekly stats — staff use only.
        """
        config_svc = getattr(self.bot, "config_service", None)
        if config_svc is None:
            return False

        guild_id = str(guild.id)
        cfg      = await resolve_leaderboard_config(guild_id, config_svc)
        channel  = await _resolve_channel(guild, cfg.post_channel_id)

        if channel is None:
            logger.warning(
                f"[Leaderboard] force_post: channel={cfg.post_channel_id} "
                f"unreachable for guild={guild_id}"
            )
            return False

        success = await self._post_leaderboard(
            channel  = channel,
            guild    = guild,
            guild_id = guild_id,
        )
        if success:
            await config_svc.upsert_last_posted_at(guild_id)
        return success
