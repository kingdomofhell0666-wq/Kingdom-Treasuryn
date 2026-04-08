from typing import List, Dict, Optional, Tuple


RANKS = [
    ("Forsaken",     0,          0.12, False),
    ("Vermin",       1_500,      0.11, True),
    ("Corrupted",    6_000,      0.10, True),
    ("Mythology",    15_000,     0.09, True),
    ("Folklore",     35_000,     0.09, True),
    ("Eschatology",  80_000,     0.08, True),
    ("Demonology",   160_000,    0.08, True),
    ("Archangel",    400_000,    0.07, True),
    ("Archdemon",    1_000_000,  0.06, True),
    ("Knight",       2_500_000,  0.05, True),
    ("Baron",        5_000_000,  0.04, True),
    ("Viscount",     10_000_000, 0.03, True),
    ("Count",        20_000_000, 0.03, True),
    ("Marquis",      40_000_000, 0.02, True),
    ("Duke",         80_000_000, 0.01, True),
]

RANK_DICT: Dict[str, dict] = {
    name: {"cost": cost, "tax_rate": rate, "purchasable": purchasable}
    for name, cost, rate, purchasable in RANKS
}


class RankService:
    def get_tax_rate(self, rank_name: str) -> float:
        entry = RANK_DICT.get(rank_name)
        if entry:
            return entry["tax_rate"]
        return 0.12

    def get_rank_cost(self, rank_name: str) -> Optional[int]:
        entry = RANK_DICT.get(rank_name)
        if entry and entry["purchasable"]:
            return entry["cost"]
        return None

    def is_purchasable(self, rank_name: str) -> bool:
        entry = RANK_DICT.get(rank_name)
        return bool(entry and entry["purchasable"])

    def get_purchasable_ranks(self) -> List[Tuple[str, int, float]]:
        return [
            (name, cost, rate)
            for name, cost, rate, purchasable in RANKS
            if purchasable
        ]

    def get_all_ranks(self) -> List[Tuple[str, int, float, bool]]:
        return RANKS

    def rank_exists(self, rank_name: str) -> bool:
        return rank_name in RANK_DICT
