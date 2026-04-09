"""
AscensionAnnouncementService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bot-first, dashboard-override ascension announcement system.

Channel resolution — strict priority
──────────────────────────────────────
1. Dashboard config channel_id (if DB row exists AND channel_id is non-null/non-empty)
2. Hard-default channel: DEFAULT_ANNOUNCE_CHANNEL_ID
3. If resolved channel cannot be used → log error, abort. NO random fallback.

The bot NEVER uses the /ascend origin channel, walks guild channels,
or guesses. If neither the dashboard channel nor the default channel
is reachable, the announcement is suppressed and logged.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import discord

logger = logging.getLogger("kingdom_treasury")

# ── Hard-locked default channel ───────────────────────────────────────────────
# Used when the dashboard has no explicit override.
# Changed only when the dashboard saves a valid non-null channel_id.

DEFAULT_ANNOUNCE_CHANNEL_ID = "1488244124992929802"   # #🏆┃domination

# ── Announcement defaults ─────────────────────────────────────────────────────

DEFAULT_TEMPLATE = "{user} has ascended to {rank} in the Kingdom of Hell! 🔥"
ANNOUNCE_COLOR   = 0xFFD700


# ── Resolved config dataclass ──────────────────────────────────────────────────

@dataclass
class EffectiveAscensionConfig:
    source:            str            # "dashboard" | "fallback"
    enabled:           bool
    channel_id:        str            # always a non-None channel ID string
    channel_source:    str            # "dashboard" | "default"
    message_template:  str
    resolved_strategy: str            # human-readable resolution note


# ── Service ────────────────────────────────────────────────────────────────────

class AscensionAnnouncementService:
    """
    Resolves the effective announcement config and fires the announcement
    embed on successful /ascend.  All failures are caught internally so
    the /ascend purchase result is never affected.
    """

    # ── Config resolution ──────────────────────────────────────────────────────

    async def resolve_config(
        self,
        guild_id:          str,
        config_service,                # ConfigService instance (avoids circular import)
    ) -> EffectiveAscensionConfig:
        """
        Load the dashboard config from PostgreSQL.
        Return an EffectiveAscensionConfig describing what should happen.

        Dashboard channel is used ONLY when the DB row exists AND channel_id
        is non-null and non-empty.  Every other case uses DEFAULT_ANNOUNCE_CHANNEL_ID.
        """
        config_service.invalidate_guild(guild_id)
        ann = await config_service.get_ascension_announcement_settings(guild_id)

        # ── Dashboard config path ──────────────────────────────────────────────
        if ann is not None and ann.get("enabled") is not None:
            enabled  = bool(ann["enabled"])
            template = (ann.get("message_template") or "").strip() or DEFAULT_TEMPLATE

            # Dashboard channel is an override ONLY if explicitly saved and non-null.
            db_channel_id = (ann.get("channel_id") or "").strip() or None
            if db_channel_id:
                channel_id     = db_channel_id
                channel_source = "dashboard"
            else:
                channel_id     = DEFAULT_ANNOUNCE_CHANNEL_ID
                channel_source = "default"

            return EffectiveAscensionConfig(
                source            = "dashboard",
                enabled           = enabled,
                channel_id        = channel_id,
                channel_source    = channel_source,
                message_template  = template,
                resolved_strategy = (
                    f"dashboard: enabled={enabled} "
                    f"channel_source={channel_source} "
                    f"channel_id={channel_id}"
                ),
            )

        # ── Fallback path (no DB row or enabled field is NULL) ─────────────────
        logger.info(
            f"[Ascend] no valid dashboard config for guild={guild_id} "
            f"— using hard-locked default channel={DEFAULT_ANNOUNCE_CHANNEL_ID}"
        )
        return EffectiveAscensionConfig(
            source            = "fallback",
            enabled           = True,
            channel_id        = DEFAULT_ANNOUNCE_CHANNEL_ID,
            channel_source    = "default",
            message_template  = DEFAULT_TEMPLATE,
            resolved_strategy = f"fallback: no valid dashboard config — using default channel={DEFAULT_ANNOUNCE_CHANNEL_ID}",
        )

    # ── Channel resolution ─────────────────────────────────────────────────────

    async def _resolve_channel(
        self,
        guild:    discord.Guild,
        ch_id:    str,
    ) -> Optional[discord.abc.Messageable]:
        """
        Resolve a sendable channel from a specific ID.

        STRICT — no guild channel walk, no origin-channel fallback.
        Returns None only when the given ID is unreachable or unsendable.
        """
        try:
            raw = int(ch_id)
        except (TypeError, ValueError):
            logger.warning(f"[Ascend ERROR] channel_id {ch_id!r} is not a valid integer — cannot resolve")
            return None

        ch = guild.get_channel(raw)
        if ch is None:
            logger.info(f"[Ascend] channel {raw} not in guild cache — calling fetch_channel()")
            try:
                ch = await guild.fetch_channel(raw)
            except discord.NotFound:
                logger.warning(f"[Ascend ERROR] channel {raw} not found (NotFound)")
                return None
            except discord.Forbidden:
                logger.warning(f"[Ascend ERROR] channel {raw} fetch forbidden (no permission)")
                return None
            except Exception as e:
                logger.warning(f"[Ascend ERROR] fetch_channel({raw}) failed: {e}")
                return None

        if ch is not None and hasattr(ch, "send"):
            return ch

        if ch is not None:
            logger.warning(
                f"[Ascend ERROR] channel {raw} resolved to {type(ch).__name__} "
                f"which has no send() — cannot use"
            )
        return None

    # ── Message rendering ──────────────────────────────────────────────────────

    @staticmethod
    def _render(template: str, discord_id: str, rank_name: str) -> str:
        try:
            return (
                template
                .replace("{user}", f"<@{discord_id}>")
                .replace("{rank}", rank_name)
            )
        except Exception as e:
            logger.warning(f"[Ascend] template rendering failed ({e}) — using default")
            return (
                DEFAULT_TEMPLATE
                .replace("{user}", f"<@{discord_id}>")
                .replace("{rank}", rank_name)
            )

    # ── Main announce pipeline ─────────────────────────────────────────────────

    async def announce(
        self,
        *,
        inter:             discord.Interaction,   # the /ascend interaction
        guild_id:          str,
        discord_id:        str,
        rank_name:         str,
        origin_channel_id: str,                   # kept for logging only
        config_service,
    ) -> None:
        """
        Full announcement pipeline.  Never raises — failures are logged only.
        """
        try:
            logger.info(
                f"[Ascend] purchase success guild={guild_id} "
                f"user={discord_id} rank={rank_name}"
            )

            # ── 1. Resolve config ──────────────────────────────────────────────
            cfg = await self.resolve_config(guild_id, config_service)
            logger.info(
                f"[Ascend] config_source={cfg.source} "
                f"enabled={cfg.enabled} "
                f"channel_source={cfg.channel_source} "
                f"channel_id={cfg.channel_id} "
                f"strategy={cfg.resolved_strategy}"
            )

            # ── 2. Respect explicit disable ────────────────────────────────────
            if not cfg.enabled:
                logger.info("[Ascend] disabled by dashboard config — no message sent")
                return

            # ── 3. Need a guild object ─────────────────────────────────────────
            guild = inter.guild
            if guild is None:
                logger.warning("[Ascend ERROR] inter.guild is None — cannot resolve channel, skipping")
                return

            # ── 4. Resolve channel (strict — no random fallback) ───────────────
            channel = await self._resolve_channel(guild, cfg.channel_id)

            if channel is None:
                logger.warning(
                    f"[Ascend ERROR] guild={guild_id} "
                    f"channel_source={cfg.channel_source} "
                    f"channel_id={cfg.channel_id} "
                    f"— channel unreachable, announcement suppressed"
                )
                return

            logger.info(
                f"[Ascend] channel_source={cfg.channel_source} "
                f"channel_id={channel.id}"
            )

            # ── 5. Render message ──────────────────────────────────────────────
            message = self._render(cfg.message_template, discord_id, rank_name)
            logger.info(
                f"[Ascend] resolved_channel_name=#{channel.name} ({channel.id}) "
                f"rendered_message={message!r}"
            )

            # ── 6. Build embed ─────────────────────────────────────────────────
            embed = discord.Embed(description=message, color=ANNOUNCE_COLOR)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

            # ── 7. Send ────────────────────────────────────────────────────────
            sent = await channel.send(embed=embed)
            logger.info(
                f"[Ascend] success message_id={sent.id} "
                f"guild={guild_id} channel={channel.id} (#{channel.name})"
            )

        except Exception as exc:
            logger.warning(
                f"[Ascend ERROR] unexpected exception — /ascend success is NOT affected: {exc}",
                exc_info=True,
            )
