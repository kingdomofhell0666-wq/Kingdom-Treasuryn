"""
Identity Card Variant Resolver
Determines the single primary visible role for the Identity Card.

Priority (card presentation only — no effect on economy or rank ladder):
  1. Sovereign
  2. Consorts
  3. Princes
  4. Princesses
  5. Chancellor
  6. Legates
  7. Centurion
  8. Legionnaires
  9. Public Kingdom Rank (fallback)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

SPECIAL_ROLE_PRIORITY: List[tuple] = [
    ("Sovereign",    "1290484661419638873"),
    ("Consorts",     "1418279591528890508"),
    ("Princes",      "1290484661419638870"),
    ("Princesses",   "1489067882557079603"),
    ("Chancellor",   "1414110540128718898"),
    ("Legates",      "1489108767353344130"),
    ("Centurion",    "1489108909682589696"),
    ("Legionnaires", "1290484661419638871"),
]

_PRIORITY_INDEX = {role_id: i for i, (_, role_id) in enumerate(SPECIAL_ROLE_PRIORITY)}


@dataclass(frozen=True)
class EffectiveCardVariant:
    variant_type: str
    primary_display_role: str
    source_role_id: Optional[str]
    public_rank: str


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
        EffectiveCardVariant — either a special role variant or the public rank fallback.

    Tests (from spec):
        T1: Sovereign + Duke        → variant=Sovereign  (special beats public)
        T2: Chancellor + Archdemon  → variant=Chancellor
        T3: Legates + Knight        → variant=Legates
        T4: Legionnaires + Count    → variant=Legionnaires
        T5: no special, Marquis     → variant=Marquis    (public fallback)
        T6: Princes + Princesses    → variant=Princes    (higher in priority list)
    """
    role_set = set(member_role_ids)

    best_index: Optional[int] = None
    best_name: Optional[str] = None
    best_id: Optional[str] = None

    for role_name, role_id in SPECIAL_ROLE_PRIORITY:
        if role_id in role_set:
            idx = _PRIORITY_INDEX[role_id]
            if best_index is None or idx < best_index:
                best_index = idx
                best_name  = role_name
                best_id    = role_id

    if best_name is not None:
        return EffectiveCardVariant(
            variant_type="special",
            primary_display_role=best_name,
            source_role_id=best_id,
            public_rank=public_rank,
        )

    return EffectiveCardVariant(
        variant_type="public",
        primary_display_role=public_rank,
        source_role_id=None,
        public_rank=public_rank,
    )
