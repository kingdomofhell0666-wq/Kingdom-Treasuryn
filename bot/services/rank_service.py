from typing import List, Dict, Optional, Tuple


# (name, cost, tax_rate, purchasable)
RANKS = [
    ("Forsaken",     0,           0.12, False),
    ("Vermin",       1_500,       0.11, True),
    ("Corrupted",    6_000,       0.10, True),
    ("Mythology",    15_000,      0.09, True),
    ("Folklore",     35_000,      0.09, True),
    ("Eschatology",  80_000,      0.08, True),
    ("Demonology",   160_000,     0.08, True),
    ("Archangel",    400_000,     0.07, True),
    ("Archdemon",    1_000_000,   0.06, True),
    ("Knight",       2_500_000,   0.05, True),
    ("Baron",        5_000_000,   0.04, True),
    ("Viscount",     10_000_000,  0.03, True),
    ("Count",        20_000_000,  0.03, True),
    ("Marquis",      40_000_000,  0.02, True),
    ("Duke",         80_000_000,  0.01, True),
    ("Chancellor",   200_000_000, 0.00, True),
]

RANK_NAMES: List[str] = [r[0] for r in RANKS]

RANK_DICT: Dict[str, dict] = {
    name: {"cost": cost, "tax_rate": rate, "purchasable": purchasable, "index": idx}
    for idx, (name, cost, rate, purchasable) in enumerate(RANKS)
}


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
        entry = RANK_DICT.get(rank_name)
        return bool(entry and entry["purchasable"])

    def rank_exists(self, rank_name: str) -> bool:
        return rank_name in RANK_DICT

    def get_next_rank(self, current_rank: str) -> Optional[str]:
        """Return the next rank in progression, or None if at the top."""
        entry = RANK_DICT.get(current_rank)
        if entry is None:
            return None
        next_idx = entry["index"] + 1
        if next_idx >= len(RANK_NAMES):
            return None
        return RANK_NAMES[next_idx]

    def can_ascend_to(self, current_rank: str, target_rank: str) -> bool:
        """Users must ascend one step at a time — no skipping."""
        return self.get_next_rank(current_rank) == target_rank

    def get_purchasable_ranks(self) -> List[Tuple[str, int, float]]:
        return [
            (name, cost, rate)
            for name, cost, rate, purchasable in RANKS
            if purchasable
        ]

    def get_rank_index(self, rank_name: str) -> int:
        entry = RANK_DICT.get(rank_name)
        return entry["index"] if entry else 0
