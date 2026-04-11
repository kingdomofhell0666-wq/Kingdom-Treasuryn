"""
Command Channel Routing — Hard-locked defaults with dashboard override.
Integrated with the Cerberus Aggression System + auto-delete enforcement.

Priority
─────────
1. Dashboard config (command_routing table in PostgreSQL), if a row exists
2. Bot-hardcoded default channel
3. If neither is configured → command is unrestricted (allowed everywhere)

Violation behavior
───────────────────
- Cerberus denial embed sent NON-EPHEMERALLY (so it can be deleted)
- Violation recorded → aggression level escalates
- Level 4 → punitive financial seizure (rank + rage scaled)
- Denial message auto-deleted after 45 seconds
- Never executes command logic after a denial
"""

import asyncio
import logging
from typing import Optional

import discord

from ..utils.embeds import EmbedFactory

logger = logging.getLogger("kingdom_treasury")

DELETE_DELAY = 45   # seconds before denial messages are auto-deleted


# ── Hard-locked default channel assignments ────────────────────────────────────

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
    "market":      "1492396305782407238",   # #🛍️┃exchange
    "relics":      "1492396305782407238",   # #🛍️┃exchange
    # Investments
    "invest":      "1491892584786825266",   # #🪙┃hell-bourse
    "portfolio":   "1491892584786825266",   # #🪙┃hell-bourse
    "collect":     "1491892584786825266",   # #🪙┃hell-bourse
    "withdraw":    "1491892584786825266",   # #🪙┃hell-bourse
    # Black market
    "blackmarket": "1491894676268257502",   # #🕴️┃blackmarket
}


# ── Auto-delete helper ─────────────────────────────────────────────────────────

async def _delete_after(message: discord.Message, delay: int):
    """Wait `delay` seconds then silently delete `message`."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except discord.NotFound:
        pass    # already gone
    except discord.Forbidden:
        logger.debug("[Routing] auto-delete: missing Manage Messages permission.")
    except Exception as exc:
        logger.warning(f"[Routing] auto-delete failed: {exc}")


async def _send_denial(
    interaction: discord.Interaction,
    embed: discord.Embed,
) -> Optional[discord.Message]:
    """
    Send the denial embed as a non-ephemeral, deletable message.

    If the interaction was already deferred, we:
      1. Silently delete the original "Bot is thinking…" response.
      2. Send a fresh non-ephemeral followup — visible to the channel.

    If not yet deferred we send a regular non-ephemeral response.

    Returns the Message object so the caller can schedule deletion.
    Returns None if sending failed entirely.
    """
    try:
        if interaction.response.is_done():
            # Remove the ephemeral/non-ephemeral "thinking" placeholder.
            try:
                await interaction.delete_original_response()
            except Exception:
                pass
            # Send a fresh, deletable message.
            msg = await interaction.followup.send(embed=embed, wait=True)
        else:
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
        return msg
    except Exception as exc:
        logger.error(f"[Routing] failed to send denial embed: {exc}")
        return None


# ── Public helper ──────────────────────────────────────────────────────────────

async def check_routing(
    interaction:   discord.Interaction,
    command_name:  str,
    config_service = None,
) -> bool:
    """
    Enforce channel routing for `command_name`.

    Returns True  → command is allowed, proceed normally.
    Returns False → command denied; Cerberus embed sent + 45-second auto-delete
                    scheduled. Caller must return immediately.
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

    # ── 2. Hardcoded default ───────────────────────────────────────────────
    if not allowed_channel:
        allowed_channel = DEFAULT_CHANNEL_ROUTING.get(command_name)

    # ── 3. No routing rule → unrestricted ──────────────────────────────────
    if not allowed_channel:
        return True

    # ── 4. Correct channel → allowed ───────────────────────────────────────
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

    # Grab Cerberus aggression service
    bot      = interaction.client
    cerberus = getattr(bot, "cerberus_aggression", None)

    level      = 1
    seizure    = 0
    rage_level = 0

    if cerberus is not None:
        level = cerberus.record_violation(guild_id, discord_id)

        # Level 4: punitive tax with rage scaling
        if level >= 4 and cerberus.should_tax(guild_id, discord_id):
            rage_level = cerberus.get_rage_level(guild_id, discord_id)
            db = getattr(bot, "db", None)
            if db is not None:
                rank = "Forsaken"
                try:
                    user = await db.get_user(guild_id, discord_id)
                    rank = user.get("rank", "Forsaken") if user else "Forsaken"
                except Exception:
                    pass
                result  = await cerberus.execute_seizure(db, guild_id, discord_id, rank)
                seizure = result["seizure"]
        elif level >= 4:
            rage_level = cerberus.get_rage_level(guild_id, discord_id)

    # ── Build embed ─────────────────────────────────────────────────────────
    embed = EmbedFactory.cerberus_routing_deny(level, seizure, rage_level)

    # ── Send non-ephemeral so we can delete it ──────────────────────────────
    msg = await _send_denial(interaction, embed)

    # ── Schedule auto-delete after 45 seconds ──────────────────────────────
    if msg is not None:
        asyncio.create_task(_delete_after(msg, DELETE_DELAY))

    return False
