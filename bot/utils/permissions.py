"""
Kingdom Treasury — Role-based permission helpers.

All role/permission checks are centralised here so every cog imports
from one canonical source.  Deny-embed builders are also kept here.

Role IDs are sourced from rank_service.EXCLUDED_ROLE_IDS so there is a
single definition for all non-purchasable authority roles.
"""
from __future__ import annotations

import discord
from ..services.rank_service import EXCLUDED_ROLE_IDS as _EX

_DC = "<:devilcoinStack:1492184333392412692>"

# ── Kingdom staff role IDs (sourced from rank_service — single source of truth) ──

ROLE_SOVEREIGN    = int(_EX["Sovereign"])
ROLE_CONSORTS     = int(_EX["Consorts"])
ROLE_PRINCES      = int(_EX["Princes"])
ROLE_PRINCESSES   = int(_EX["Princesses"])
ROLE_CHANCELLOR   = int(_EX["Chancellor"])
ROLE_LEGATES      = int(_EX["Legates"])
ROLE_CENTURION    = int(_EX["Centurion"])
ROLE_LEGIONNAIRES = int(_EX["Legionnaires"])

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


def is_strict_discord_admin(interaction: discord.Interaction) -> bool:
    """True only for a member with Discord's Administrator permission."""
    if not interaction.guild:
        return False
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms and perms.administrator)


def is_kingdom_or_admin(interaction: discord.Interaction) -> bool:
    """Kingdom staff OR Discord admin — used for /treasury."""
    return is_kingdom_staff(interaction) or is_admin_user(interaction)


def is_freeze_exempt(member: discord.Member) -> bool:
    """True if this member is immune to being frozen (all Kingdom staff + Centurion + Legionnaires)."""
    member_role_ids = frozenset(r.id for r in getattr(member, "roles", []))
    return bool(member_role_ids & EXTENDED_ROLES)


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
