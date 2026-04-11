"""
Identity Card Variant Resolver
Determines the highest authority role, hierarchy group, and classification
for the Identity Card — driven by real Discord role IDs.

Hierarchy groups (spec):
  1. Owners             — Sovereign
  2. Admin/Royal Family — Consorts, Princes, Princesses
  3. Moderation/Council — Chancellor, Legates
  4. Staff/Legion       — Centurion, Legionnaires
  5. Nobility           — Duke … Knight
  6. Members            — Archdemon … Forsaken

Kingdom Rank eligibility: ONLY Nobility + Members (groups 5 & 6).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


# ─── Full hierarchy priority list ─────────────────────────────────────────────
# (display_name, role_id, hierarchy_group, kingdom_rank_eligible, classification)
_HIERARCHY: List[tuple] = [
    # Owners
    ("Sovereign",    "1290484661419638873", "Owners",       False, "SOVEREIGN ENTITY"),
    # Admin / Royal Family
    ("Consorts",     "1418279591528890508", "Royal Family", False, "ROYAL AUTHORITY"),
    ("Princes",      "1290484661419638870", "Royal Family", False, "ROYAL AUTHORITY"),
    ("Princesses",   "1489067882557079603", "Royal Family", False, "ROYAL AUTHORITY"),
    # Moderation / High Council
    ("Chancellor",   "1414110540128718898", "Council",      False, "COUNCIL AUTHORITY"),
    ("Legates",      "1489108767353344130", "Council",      False, "COUNCIL AUTHORITY"),
    # Staff / Legion
    ("Centurion",    "1489108909682589696", "Legion",       False, "LEGION AUTHORITY"),
    ("Legionnaires", "1290484661419638871", "Legion",       False, "LEGION AUTHORITY"),
    # Nobility — eligible for Kingdom Rank
    ("Duke",         "1489130140532211874", "Nobility",     True,  "NOBLE ENTITY"),
    ("Marquis",      "1489129490209706045", "Nobility",     True,  "NOBLE ENTITY"),
    ("Count",        "1489128625474113697", "Nobility",     True,  "NOBLE ENTITY"),
    ("Viscount",     "1489127901461876807", "Nobility",     True,  "NOBLE ENTITY"),
    ("Baron",        "1489127375206613082", "Nobility",     True,  "NOBLE ENTITY"),
    ("Knight",       "1489126295798415380", "Nobility",     True,  "NOBLE ENTITY"),
    # Members — eligible for Kingdom Rank
    ("Archdemon",    "1290530372748185612", "Members",      True,  "HIGH ENTITY"),
    ("Archangel",    "1290530281580662796", "Members",      True,  "INFERNAL ENTITY"),
    ("Demonology",   "1290529262377500815", "Members",      True,  "LESSER ENTITY"),
    ("Eschatology",  "1290484661419638869", "Members",      True,  "LESSER ENTITY"),
    ("Folklore",     "1290484661419638868", "Members",      True,  "LOWER ENTITY"),
    ("Mythology",    "1290484661419638867", "Members",      True,  "LOWER ENTITY"),
    ("Corrupted",    "1290484661419638866", "Members",      True,  "LOWER ENTITY"),
    ("Vermin",       "1484302112241352744", "Members",      True,  "CONDEMNED"),
    ("Forsaken",     "1489101267048468490", "Members",      True,  "CONDEMNED — LOWEST CLASS"),
]

# Build lookup by role_id — priority = list index (lower = higher authority)
_PRIORITY_BY_ID = {row[1]: i for i, row in enumerate(_HIERARCHY)}
_DATA_BY_ID     = {row[1]: row for row in _HIERARCHY}


@dataclass(frozen=True)
class EffectiveCardVariant:
    variant_type:         str            # "special" | "public"
    primary_display_role: str            # Displayed as RANK on the card
    source_role_id:       Optional[str]  # Matched Discord role ID
    public_rank:          str            # Economy rank (for rank_level calc)
    hierarchy_group:      str            # "Owners" | "Royal Family" | etc.
    kingdom_rank_eligible: bool          # Whether to show real leaderboard pos
    classification:       str            # Classification label for the card


def resolve_identity_card_variant(
    member_role_ids: List[str],
    public_rank: str,
) -> EffectiveCardVariant:
    """
    Return the single highest-priority card variant for the given member.

    Args:
        member_role_ids: All Discord role IDs the member currently holds (as strings).
        public_rank:     The user's stored economy rank (e.g. "Archdemon").

    Returns:
        EffectiveCardVariant with full hierarchy metadata.
    """
    role_set = set(member_role_ids)

    best_index: Optional[int]  = None
    best_row:   Optional[tuple] = None

    for role_id, idx in _PRIORITY_BY_ID.items():
        if role_id in role_set:
            if best_index is None or idx < best_index:
                best_index = idx
                best_row   = _DATA_BY_ID[role_id]

    if best_row is not None:
        name, role_id, group, eligible, cls = best_row
        return EffectiveCardVariant(
            variant_type          = "special" if group not in ("Nobility", "Members") else "public",
            primary_display_role  = name,
            source_role_id        = role_id,
            public_rank           = public_rank,
            hierarchy_group       = group,
            kingdom_rank_eligible = eligible,
            classification        = cls,
        )

    # Fallback — unrecognised member (treat as Forsaken-level)
    return EffectiveCardVariant(
        variant_type          = "public",
        primary_display_role  = public_rank,
        source_role_id        = None,
        public_rank           = public_rank,
        hierarchy_group       = "Members",
        kingdom_rank_eligible = True,
        classification        = "REGISTERED ENTITY",
    )
