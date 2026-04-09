"""
Command Channel Routing — Hard-locked defaults with dashboard override.
Integrated with the Cerberus Aggression System.

Priority
─────────
1. Dashboard config (command_routing table in PostgreSQL), if a row exists
2. Bot-hardcoded default channel
3. If neither is configured → command is unrestricted (allowed everywhere)

Violation behavior
───────────────────
- Immediately return immersive ephemeral Cerberus denial embed
- Log the violation (with full context) + record aggression escalation
- At Level 4 → execute punitive financial seizure (rank-scaled)
- Never execute any command logic
- Never redirect automatically
- Never allow partial execution
"""

import logging
from typing import Optional

import discord

from ..utils.embeds import EmbedFactory

logger = logging.getLogger("kingdom_treasury")


# ── Hard-locked default channel assignments ────────────────────────────────────
# These are the ONLY channels where each command may run by default.
# The dashboard may override per guild via the command_routing table.

DEFAULT_CHANNEL_ROUTING: dict[str, str] = {
    # Identity
    "identity":    "1488255553170837565",   # #🪪┃identity
    "wealth":      "1488255553170837565",   # #🪪┃identity
    # Economy
    "grind":       "1488360369364926586",   # #⛏️┃grind
    "tribute":     "1488255003574534274",   # #🎗️┃tribute
    "transfer":    "1491893908840648724",   # #💸┃transferts
    "ascend":      "1488240921572282368",   # #⛩️┃ascension
    # Market / cosmetics
    "market":      "1290512527238631509",   # #⚓┃underworld-exchange
    "equip-skin":  "1290512527238631509",   # #⚓┃underworld-exchange
    "equip-title": "1290512527238631509",   # #⚓┃underworld-exchange
    # Investments
    "invest":      "1491892584786825266",   # #🪙┃hell-bourse
    "portfolio":   "1491892584786825266",   # #🪙┃hell-bourse
    "collect":     "1491892584786825266",   # #🪙┃hell-bourse
    "withdraw":    "1491892584786825266",   # #🪙┃hell-bourse
    # Black market
    "blackmarket": "1491894676268257502",   # #🕴️┃blackmarket
}


# ── Public helper ──────────────────────────────────────────────────────────────

async def check_routing(
    interaction:    discord.Interaction,
    command_name:   str,
    config_service  = None,     # ConfigService — for dashboard override lookup
) -> bool:
    """
    Enforce channel routing for `command_name`.

    Returns True  → command is allowed in this channel, proceed normally.
    Returns False → command is denied; a Cerberus embed has already been sent
                    to the user (ephemeral).  Caller must return immediately.

    Sends via followup if the interaction is already deferred,
    otherwise via response.send_message.
    """
    guild_id   = str(interaction.guild_id)
    channel_id = str(interaction.channel_id)

    # ── 1. Dashboard override ───────────────────────────────────────────────
    allowed_channel: Optional[str] = None
    if config_service is not None:
        try:
            routing = await config_service.get_command_routing(guild_id)
            allowed_channel = routing.get(command_name)
        except Exception as exc:
            logger.warning(f"[Routing] failed to fetch dashboard routing: {exc}")

    # ── 2. Fall back to hardcoded default ──────────────────────────────────
    if not allowed_channel:
        allowed_channel = DEFAULT_CHANNEL_ROUTING.get(command_name)

    # ── 3. No routing rule → unrestricted ──────────────────────────────────
    if not allowed_channel:
        return True

    # ── 4. Channel match → allowed ─────────────────────────────────────────
    if channel_id == str(allowed_channel):
        return True

    # ── 5. Violation ───────────────────────────────────────────────────────
    discord_id = str(interaction.user.id)

    logger.warning(
        f"[ROUTING DENIED] user={discord_id} ({interaction.user.display_name}) "
        f"command=/{command_name} "
        f"used_channel={channel_id} "
        f"expected_channel={allowed_channel}"
    )

    # Grab Cerberus aggression service from the bot (zero extra parameters)
    bot = interaction.client
    cerberus = getattr(bot, "cerberus_aggression", None)

    level   = 1
    seizure = 0

    if cerberus is not None:
        level = cerberus.record_violation(guild_id, discord_id)

        # ── Level 4: punitive tax ─────────────────────────────────────────
        if level >= 4 and cerberus.should_tax(guild_id, discord_id):
            db = getattr(bot, "db", None)
            if db is not None:
                # Fetch user rank for tier calculation
                rank = "Forsaken"
                try:
                    user = await db.get_user(guild_id, discord_id)
                    rank = user.get("rank", "Forsaken") if user else "Forsaken"
                except Exception:
                    pass

                seizure = await cerberus.execute_seizure(db, guild_id, discord_id, rank)

    # ── Build and send the immersive embed ─────────────────────────────────
    embed = EmbedFactory.cerberus_routing_deny(level, seizure)

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as exc:
        logger.error(f"[Routing] failed to send denial embed: {exc}")

    return False
