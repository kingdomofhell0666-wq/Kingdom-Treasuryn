"""
Kingdom Treasury — Role-based permission helpers.

All role/permission checks are centralised here so every cog imports
from one canonical source.  Deny-embed builders are also kept here.
"""
from __future__ import annotations

import discord

_DC = "<:devilcoinStack:1492184333392412692>"

# ── Kingdom staff role IDs ─────────────────────────────────────────────────────

ROLE_SOVEREIGN    = 1290484661419638873
ROLE_CONSORTS     = 1418279591528890508
ROLE_PRINCES      = 1290484661419638870
ROLE_PRINCESSES   = 1489067882557079603
ROLE_CHANCELLOR   = 1414110540128718898
ROLE_LEGATES      = 1489108767353344130
ROLE_CENTURION    = 1489108909682589696
ROLE_LEGIONNAIRES = 1290484661419638871

# All Kingdom staff roles (Legates included)
KINGDOM_ROLES: frozenset[int] = frozenset({
    ROLE_SOVEREIGN, ROLE_CONSORTS, ROLE_PRINCES,
    ROLE_PRINCESSES, ROLE_CHANCELLOR, ROLE_LEGATES,
})

# Roles authorised for /freeze (Legates deliberately excluded)
FREEZE_ROLES: frozenset[int] = frozenset({
    ROLE_SOVEREIGN, ROLE_CONSORTS, ROLE_PRINCES,
    ROLE_PRINCESSES, ROLE_CHANCELLOR,
})

# Kingdom staff + Centurion + Legionnaires (for /remove-dc)
EXTENDED_ROLES: frozenset[int] = KINGDOM_ROLES | frozenset({
    ROLE_CENTURION, ROLE_LEGIONNAIRES,
})


# ── Role ID extractor ─────────────────────────────────────────────────────────

def _member_role_ids(interaction: discord.Interaction) -> frozenset[int]:
    return frozenset(r.id for r in getattr(interaction.user, "roles", []))


# ── Permission predicates ─────────────────────────────────────────────────────

def is_kingdom_staff(interaction: discord.Interaction) -> bool:
    """True if user holds any Kingdom role (Legates included)."""
    return bool(_member_role_ids(interaction) & KINGDOM_ROLES)


def is_freeze_authorized(interaction: discord.Interaction) -> bool:
    """True if user may /freeze (Sovereign → Chancellor, NOT Legates)."""
    return bool(_member_role_ids(interaction) & FREEZE_ROLES)


def is_extended_staff(interaction: discord.Interaction) -> bool:
    """True if user may /remove-dc (Kingdom + Centurion + Legionnaires)."""
    return bool(_member_role_ids(interaction) & EXTENDED_ROLES)


def is_admin_user(interaction: discord.Interaction) -> bool:
    """True if user is a Discord Administrator or has Manage Guild."""
    if not interaction.guild:
        return False
    perms = interaction.user.guild_permissions
    return perms.administrator or perms.manage_guild


def is_kingdom_or_admin(interaction: discord.Interaction) -> bool:
    """Kingdom staff OR Discord admin — used for /treasury."""
    return is_kingdom_staff(interaction) or is_admin_user(interaction)


# ── Deny-embed builders ───────────────────────────────────────────────────────

def denied_generic() -> discord.Embed:
    return discord.Embed(
        description="*You are not authorized to command the Kingdom.*",
        color=0x0A0A0A,
    )


def denied_freeze() -> discord.Embed:
    return discord.Embed(
        description="*You do not hold the authority to seal this ledger.*",
        color=0x0A0A0A,
    )


def denied_unfreeze() -> discord.Embed:
    return discord.Embed(
        description="*You do not hold the authority to lift this seal.*",
        color=0x0A0A0A,
    )
