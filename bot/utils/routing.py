"""
Command Channel Routing — Hard-locked defaults with dashboard override.

Priority
─────────
1. Dashboard config (command_routing table in PostgreSQL), if a row exists
2. Bot-hardcoded default channel
3. If neither is configured → command is unrestricted (allowed everywhere)

Violation behavior
───────────────────
- Immediately return immersive ephemeral denial embed
- Log the violation with full context
- Never execute any command logic
- Never redirect automatically
- Never allow partial execution
"""

import logging
from typing import Optional

import discord

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


# ── Immersive denial messages ──────────────────────────────────────────────────
# Each command has its own flavoured response. title + body.

_DENIAL: dict[str, tuple[str, str]] = {
    "identity":    (
        "The Kingdom does not recognize you here.",
        "Present your identity where it is demanded.",
    ),
    "wealth":      (
        "The Kingdom does not recognize you here.",
        "Present your identity where it is demanded.",
    ),
    "grind":       (
        "The mines do not exist here.",
        "Descend where the labor is demanded.",
    ),
    "tribute":     (
        "Offerings are not made in the open.",
        "Kneel where the Kingdom accepts its due.",
    ),
    "transfer":    (
        "Transactions must be witnessed.",
        "Move your coin where exchanges are permitted.",
    ),
    "ascend":      (
        "Ascension is not granted in the open.",
        "Stand before the gate if you seek to rise.",
    ),
    "market":      (
        "Trade is forbidden outside the Exchange.",
        "All deals are made in the Underworld.",
    ),
    "equip-skin":  (
        "Trade is forbidden outside the Exchange.",
        "All deals are made in the Underworld.",
    ),
    "equip-title": (
        "Trade is forbidden outside the Exchange.",
        "All deals are made in the Underworld.",
    ),
    "invest":      (
        "Wealth flows only through the infernal markets.",
        "You are not standing where fortunes are made.",
    ),
    "portfolio":   (
        "Wealth flows only through the infernal markets.",
        "You are not standing where fortunes are made.",
    ),
    "collect":     (
        "Wealth flows only through the infernal markets.",
        "You are not standing where fortunes are made.",
    ),
    "withdraw":    (
        "Wealth flows only through the infernal markets.",
        "You are not standing where fortunes are made.",
    ),
    "blackmarket": (
        "The Black Market is hidden for a reason.",
        "Find it… or be denied.",
    ),
}

_DEFAULT_DENIAL = ("Wrong Channel", "This command is not permitted here.")


# ── Public helper ──────────────────────────────────────────────────────────────

async def check_routing(
    interaction:    discord.Interaction,
    command_name:   str,
    config_service  = None,         # ConfigService — for dashboard override lookup
) -> bool:
    """
    Enforce channel routing for `command_name`.

    Returns True  → command is allowed in this channel, proceed normally.
    Returns False → command is denied; an immersive ephemeral embed has already
                    been sent to the user.  Caller must return immediately.

    Sends via followup if the interaction is already deferred,
    otherwise via response.send_message.
    """
    guild_id   = str(interaction.guild_id)
    channel_id = str(interaction.channel_id)

    # ── 1. Dashboard override (config_service.get_command_routing) ─────────────
    allowed_channel: Optional[str] = None
    if config_service is not None:
        try:
            routing = await config_service.get_command_routing(guild_id)
            allowed_channel = routing.get(command_name)
        except Exception as exc:
            logger.warning(f"[Routing] failed to fetch dashboard routing: {exc}")

    # ── 2. Fall back to hardcoded default ──────────────────────────────────────
    if not allowed_channel:
        allowed_channel = DEFAULT_CHANNEL_ROUTING.get(command_name)

    # ── 3. If no routing rule exists → unrestricted ────────────────────────────
    if not allowed_channel:
        return True

    # ── 4. Channel match → allowed ─────────────────────────────────────────────
    if channel_id == str(allowed_channel):
        return True

    # ── 5. Denied ──────────────────────────────────────────────────────────────
    logger.warning(
        f"[ROUTING DENIED] user={interaction.user.id} ({interaction.user.display_name}) "
        f"command=/{command_name} "
        f"used_channel={channel_id} "
        f"expected_channel={allowed_channel}"
    )

    title, body = _DENIAL.get(command_name, _DEFAULT_DENIAL)
    embed = discord.Embed(
        title       = title,
        description = f"*{body}*",
        color       = 0x1A0000,
    )
    embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

    return False
