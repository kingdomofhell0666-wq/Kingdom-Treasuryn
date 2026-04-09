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

# ─── Canonical Discord role IDs — Kingdom of Hell server ─────────────────────
# These are the exact role IDs for the Kingdom of Hell Discord server.
# Used as a bot-first fallback when no dashboard config exists.
# Dashboard config (rank_role_mapping table) overrides these when present.
# ALL public ascension ranks + Forsaken (needed for remove_previous logic).
CANONICAL_ROLE_IDS: Dict[str, str] = {
    "Forsaken":    "1489101267048468490",
    "Vermin":      "1484302112241352744",
    "Corrupted":   "1290484661419638866",
    "Folklore":    "1290484661419638868",
    "Mythology":   "1290484661419638867",
    "Demonology":  "1290529262377500815",
    "Eschatology": "1290484661419638869",
    "Archangel":   "1290530281580662796",
    "Archdemon":   "1290530372748185612",
    "Knight":      "1489126295798415380",
    "Baron":       "1489127375206613082",
    "Viscount":    "1489127901461876807",
    "Count":       "1489128625474113697",
    "Marquis":     "1489129490209706045",
    "Duke":        "1489130140532211874",
}

# Staff/moderator roles — NEVER assigned or removed by the economy system.
EXCLUDED_ROLE_IDS: Dict[str, str] = {
    "Sovereign":     "1290484661419638873",
    "Consorts":      "1418279591528890508",
    "Princes":       "1290484661419638870",
    "Princesses":    "1489067882557079603",
    "Chancellor":    "1414110540128718898",
    "Legates":       "1489108767353344130",
    "Centurion":     "1489108909682589696",
    "Legionnaires":  "1290484661419638871",
}


# ─── Default ascension cooldowns (bot-first, dashboard-override) ─────────────
# Keyed by CURRENT rank — how long you must wait at that rank before ascending.
# Dashboard config (rank_cooldown_settings table) overrides these per guild.
# All values in seconds.
DEFAULT_ASCENSION_COOLDOWNS: Dict[str, int] = {
    "Forsaken":    0,               # no wait — buy Vermin immediately
    "Vermin":      15 * 60,         # 15 minutes
    "Corrupted":   30 * 60,         # 30 minutes
    "Folklore":    1 * 3600,        # 1 hour
    "Mythology":   2 * 3600,        # 2 hours
    "Demonology":  4 * 3600,        # 4 hours
    "Eschatology": 8 * 3600,        # 8 hours
    "Archangel":   12 * 3600,       # 12 hours
    "Archdemon":   24 * 3600,       # 24 hours
    "Knight":      48 * 3600,       # 48 hours
    "Baron":       72 * 3600,       # 72 hours
    "Viscount":    120 * 3600,      # 120 hours
    "Count":       168 * 3600,      # 168 hours (7 days)
    "Marquis":     240 * 3600,      # 240 hours (10 days)
    "Duke":        336 * 3600,      # 336 hours (14 days) — no next rank, effectively unused
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
