from typing import List, Dict, Optional, Tuple


# ─── Canonical public Kingdom rank progression ────────────────────────────────
#
# This is the SINGLE SOURCE OF TRUTH for all public economy rank logic.
#
# Rules:
#  - Forsaken is the default starting rank (non-purchasable).
#  - PUBLIC_KINGDOM_RANKS are the only ranks a player can ascend through.
#  - Chancellor is a STAFF/MODERATOR role — excluded from all public rank logic.
#
# Cost ordering is ascending: each rank must cost more than the previous.
# Tax ordering is descending: higher ranks pay lower tax rates.

# (name, cost, tax_rate, purchasable)
RANKS = [
    ("Forsaken",     0,           0.12, False),   # default start, not purchasable
    ("Vermin",       1_500,       0.11, True),
    ("Corrupted",    6_000,       0.10, True),
    ("Folklore",     15_000,      0.09, True),    # rank 3 — cheaper than Mythology
    ("Mythology",    35_000,      0.09, True),    # rank 4
    ("Demonology",   80_000,      0.08, True),    # rank 5 — cheaper than Eschatology
    ("Eschatology",  160_000,     0.08, True),    # rank 6
    ("Archangel",    400_000,     0.07, True),
    ("Archdemon",    1_000_000,   0.06, True),
    ("Knight",       2_500_000,   0.05, True),
    ("Baron",        5_000_000,   0.04, True),
    ("Viscount",     10_000_000,  0.03, True),
    ("Count",        20_000_000,  0.03, True),
    ("Marquis",      40_000_000,  0.02, True),
    ("Duke",         80_000_000,  0.01, True),    # highest public rank
    # ─── Staff/moderator role — NOT part of public ascension ─────────────────
    ("Chancellor",   0,           0.00, False),   # staff only, never purchasable
]

RANK_NAMES: List[str] = [r[0] for r in RANKS]

RANK_DICT: Dict[str, dict] = {
    name: {"cost": cost, "tax_rate": rate, "purchasable": purchasable, "index": idx}
    for idx, (name, cost, rate, purchasable) in enumerate(RANKS)
}

# ─── Canonical public rank list (the only ranks players can earn/ascend) ─────
# Excludes Forsaken (start state) and Chancellor (staff role).
PUBLIC_KINGDOM_RANKS: List[str] = [
    "Vermin",
    "Corrupted",
    "Folklore",
    "Mythology",
    "Demonology",
    "Eschatology",
    "Archangel",
    "Archdemon",
    "Knight",
    "Baron",
    "Viscount",
    "Count",
    "Marquis",
    "Duke",
]

# Fast set for O(1) validation
_PUBLIC_RANK_SET = set(PUBLIC_KINGDOM_RANKS)


class RankService:
    def get_tax_rate(self, rank_name: str) -> float:
        entry = RANK_DICT.get(rank_name)
        return entry["tax_rate"] if entry else 0.12

    def get_rank_cost(self, rank_name: str) -> Optional[int]:
        entry = RANK_DICT.get(rank_name)
        if entry and entry["purchasable"]:
            return entry["cost"]
        return None

    def is_purchasable(self, rank_name: str) -> bool:
        """True only for ranks in PUBLIC_KINGDOM_RANKS (excludes Forsaken and Chancellor)."""
        return rank_name in _PUBLIC_RANK_SET

    def rank_exists(self, rank_name: str) -> bool:
        return rank_name in RANK_DICT

    def is_public_rank(self, rank_name: str) -> bool:
        """Return True if rank_name is a valid public economy rank."""
        return rank_name in _PUBLIC_RANK_SET

    def get_next_rank(self, current_rank: str) -> Optional[str]:
        """
        Return the next rank in PUBLIC_KINGDOM_RANKS progression.
        Returns None if current_rank is Duke (highest public rank) or unknown.
        Chancellor and any staff role are never returned.
        """
        if current_rank == "Forsaken":
            return PUBLIC_KINGDOM_RANKS[0]   # first purchasable rank
        try:
            idx = PUBLIC_KINGDOM_RANKS.index(current_rank)
        except ValueError:
            return None
        next_idx = idx + 1
        if next_idx >= len(PUBLIC_KINGDOM_RANKS):
            return None      # Duke is the ceiling
        return PUBLIC_KINGDOM_RANKS[next_idx]

    def can_ascend_to(self, current_rank: str, target_rank: str) -> bool:
        """Users must ascend one step at a time — no skipping."""
        return self.get_next_rank(current_rank) == target_rank

    def get_purchasable_ranks(self) -> List[Tuple[str, int, float]]:
        """Return only PUBLIC_KINGDOM_RANKS with their cost and tax_rate."""
        result = []
        for name in PUBLIC_KINGDOM_RANKS:
            entry = RANK_DICT[name]
            result.append((name, entry["cost"], entry["tax_rate"]))
        return result

    def get_rank_index(self, rank_name: str) -> int:
        entry = RANK_DICT.get(rank_name)
        return entry["index"] if entry else 0
