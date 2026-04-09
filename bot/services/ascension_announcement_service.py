"""
AscensionAnnouncementService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bot-first, dashboard-override ascension announcement system.

Priority order
──────────────
1. Valid dashboard config (DB row exists, enabled is explicitly set)
2. Bot-native fallback (always enabled, uses origin channel)

The bot is NEVER silent just because the dashboard config is missing.
The dashboard only overrides/customises the default behaviour.

Channel resolution order (fallback path)
──────────────────────────────────────────
1. origin_channel_id  — the channel where /ascend was executed
2. Any sendable text channel found in the guild
3. No-send + warning log

Channel resolution order (dashboard path)
──────────────────────────────────────────
1. configured channel_id from DB
2. If not found/invalid → log warning, then fall back to origin_channel_id
3. If that also fails → no-send + warning log
"""

import logging
from dataclasses import dataclass
from typing import Optional

import discord

logger = logging.getLogger("kingdom_treasury")

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_TEMPLATE = "{user} has ascended to {rank} in the Kingdom of Hell! 🔥"
ANNOUNCE_COLOR   = 0xFFD700


# ── Resolved config dataclass ──────────────────────────────────────────────────

@dataclass
class EffectiveAscensionConfig:
    source:            str            # "dashboard" | "fallback"
    enabled:           bool
    channel_id:        Optional[str]  # raw string ID or None
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
        origin_channel_id: str,
        config_service,                # ConfigService instance (avoids circular import)
    ) -> EffectiveAscensionConfig:
        """
        Load the dashboard config from PostgreSQL.
        Return an EffectiveAscensionConfig describing what should happen.
        """
        # Always invalidate cache so we get the freshest saved settings.
        config_service.invalidate_guild(guild_id)
        ann = await config_service.get_ascension_announcement_settings(guild_id)

        # ── Dashboard config path ──────────────────────────────────────────────
        if ann is not None and ann.get("enabled") is not None:
            enabled   = bool(ann["enabled"])
            ch_id     = ann.get("channel_id") or None
            template  = (ann.get("message_template") or "").strip() or DEFAULT_TEMPLATE
            strategy  = "dashboard config: enabled={} channel_id={}".format(enabled, ch_id)

            return EffectiveAscensionConfig(
                source            = "dashboard",
                enabled           = enabled,
                channel_id        = ch_id,
                message_template  = template,
                resolved_strategy = strategy,
            )

        # ── Fallback path (no DB row or enabled field is NULL) ─────────────────
        logger.info(
            f"[Announce] no valid dashboard config for guild={guild_id} "
            f"— using bot-native fallback defaults"
        )
        return EffectiveAscensionConfig(
            source            = "fallback",
            enabled           = True,
            channel_id        = origin_channel_id,
            message_template  = DEFAULT_TEMPLATE,
            resolved_strategy = f"fallback: origin_channel_id={origin_channel_id}",
        )

    # ── Channel resolution ─────────────────────────────────────────────────────

    async def _resolve_channel(
        self,
        guild:    discord.Guild,
        ch_id:    Optional[str],
        fallback: Optional[str] = None,
    ) -> Optional[discord.abc.Messageable]:
        """
        Try to get a sendable channel by ID.
        Falls back to `fallback` ID if primary ID is missing/invalid.
        Returns None if nothing resolves.
        """
        for candidate_id in filter(None, [ch_id, fallback]):
            try:
                raw = int(candidate_id)
            except (TypeError, ValueError):
                logger.warning(f"[Announce] channel_id {candidate_id!r} is not a valid integer — skipping")
                continue

            # Try guild cache first
            ch = guild.get_channel(raw)
            if ch is None:
                logger.info(f"[Announce] channel {raw} not in guild cache — calling fetch_channel()")
                try:
                    ch = await guild.fetch_channel(raw)
                except discord.NotFound:
                    logger.warning(f"[Announce] channel {raw} not found (NotFound)")
                    ch = None
                except discord.Forbidden:
                    logger.warning(f"[Announce] channel {raw} fetch forbidden (no permission)")
                    ch = None
                except Exception as e:
                    logger.warning(f"[Announce] fetch_channel({raw}) failed: {e}")
                    ch = None

            if ch is not None and hasattr(ch, "send"):
                return ch

            if ch is not None:
                logger.warning(
                    f"[Announce] channel {raw} resolved to {type(ch).__name__} "
                    f"which has no send() — skipping"
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
            logger.warning(f"[Announce] template rendering failed ({e}) — using default")
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
        origin_channel_id: str,
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
            cfg = await self.resolve_config(guild_id, origin_channel_id, config_service)
            logger.info(
                f"[Announce] config_source={cfg.source} "
                f"enabled={cfg.enabled} "
                f"channel_id={cfg.channel_id} "
                f"template={cfg.message_template!r} "
                f"strategy={cfg.resolved_strategy}"
            )

            # ── 2. Respect explicit disable ────────────────────────────────────
            if not cfg.enabled:
                logger.info("[Announce] disabled by dashboard config — no message sent")
                return

            # ── 3. Need a guild object ─────────────────────────────────────────
            guild = inter.guild
            if guild is None:
                logger.warning("[Announce] inter.guild is None — cannot resolve channel, skipping")
                return

            # ── 4. Resolve channel ─────────────────────────────────────────────
            #    Dashboard path:  configured channel_id → origin channel (graceful fallback)
            #    Fallback path:   origin_channel_id (already set in cfg.channel_id)
            if cfg.source == "dashboard" and cfg.channel_id:
                channel = await self._resolve_channel(
                    guild,
                    ch_id    = cfg.channel_id,
                    fallback = origin_channel_id,
                )
            else:
                channel = await self._resolve_channel(
                    guild,
                    ch_id    = cfg.channel_id or origin_channel_id,
                    fallback = None,
                )

            if channel is None:
                # Last-resort: walk guild text channels and pick the first sendable one
                logger.info("[Announce] configured channels unavailable — scanning guild for any text channel")
                for gc in guild.text_channels:
                    if hasattr(gc, "send"):
                        channel = gc
                        logger.info(f"[Announce] using first available text channel #{gc.name} ({gc.id})")
                        break

            if channel is None:
                logger.warning(
                    f"[Announce] no sendable channel found in guild={guild_id} "
                    f"— announcement suppressed"
                )
                return

            # ── 5. Render message ──────────────────────────────────────────────
            message = self._render(cfg.message_template, discord_id, rank_name)
            logger.info(
                f"[Announce] resolved_channel_name=#{channel.name} ({channel.id}) "
                f"rendered_message={message!r}"
            )

            # ── 6. Build embed ─────────────────────────────────────────────────
            embed = discord.Embed(description=message, color=ANNOUNCE_COLOR)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

            # ── 7. Send ────────────────────────────────────────────────────────
            sent = await channel.send(embed=embed)
            logger.info(
                f"[Announce] success message_id={sent.id} "
                f"guild={guild_id} channel={channel.id} (#{channel.name})"
            )

        except Exception as exc:
            logger.warning(
                f"[Announce] ❌ unexpected exception — /ascend success is NOT affected: {exc}",
                exc_info=True,
            )
