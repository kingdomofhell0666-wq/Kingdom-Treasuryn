"""
Badge catalog for Kingdom Treasury.

Badges are EARNED through real actions — never purchased.
Each badge has an unlock_condition key matched by BadgeService.

unlock_type options:
  balance_gte       — user balance >= threshold
  taxes_gte         — taxes_paid >= threshold
  grind_count_gte   — total lifetime grind count >= threshold
  tribute_count_gte — total tribute claims >= threshold
  rank_index_gte    — rank hierarchy index >= threshold (0=Forsaken)
  account_age_days  — account age in days >= threshold
  manual            — awarded manually (founder, branded_soul, events)
  jackpot           — awarded on a grind jackpot hit
  cerberus_cleared  — awarded when passing a Cerberus audit cleanly
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class Badge:
    id: str
    name: str
    description: str
    icon: str
    rarity: str          # Common / Uncommon / Rare / Epic / Legendary / Special
    unlock_type: str
    unlock_threshold: Optional[int]   # None for manual
    unlock_label: str                 # Human-readable condition string


BADGES_CATALOG: Dict[str, Badge] = {

    # ── Economy badges ────────────────────────────────────────────────────────

    "first_fortune": Badge(
        id="first_fortune",
        name="First Fortune",
        description="Reached 10,000 DC for the first time.",
        icon="🪙",
        rarity="Common",
        unlock_type="balance_gte",
        unlock_threshold=10_000,
        unlock_label="Reach 10,000 DC",
    ),
    "wealth_ascendant": Badge(
        id="wealth_ascendant",
        name="Wealth Ascendant",
        description="Accumulated 1,000,000 DC in a single wallet.",
        icon="💎",
        rarity="Rare",
        unlock_type="balance_gte",
        unlock_threshold=1_000_000,
        unlock_label="Reach 1,000,000 DC",
    ),
    "treasury_patron": Badge(
        id="treasury_patron",
        name="Treasury Patron",
        description="Paid 50,000 DC in taxes to the Kingdom.",
        icon="🏛",
        rarity="Uncommon",
        unlock_type="taxes_gte",
        unlock_threshold=50_000,
        unlock_label="Pay 50,000 DC in taxes",
    ),
    "mine_veteran": Badge(
        id="mine_veteran",
        name="Mine Veteran",
        description="Completed 100 /grind sessions in the Infernal Mines.",
        icon="⛏",
        rarity="Uncommon",
        unlock_type="grind_count_gte",
        unlock_threshold=100,
        unlock_label="Complete 100 /grind",
    ),
    "infernal_laborer": Badge(
        id="infernal_laborer",
        name="Infernal Laborer",
        description="Descended 500 times. The mines know your name.",
        icon="🔥",
        rarity="Rare",
        unlock_type="grind_count_gte",
        unlock_threshold=500,
        unlock_label="Complete 500 /grind",
    ),
    "high_roller": Badge(
        id="high_roller",
        name="High Roller",
        description="Hit a jackpot in the Infernal Mines.",
        icon="🎰",
        rarity="Uncommon",
        unlock_type="jackpot",
        unlock_threshold=None,
        unlock_label="Hit a jackpot on /grind",
    ),

    # ── Tribute badges ────────────────────────────────────────────────────────

    "unbroken_oath": Badge(
        id="unbroken_oath",
        name="Unbroken Oath",
        description="Claimed /tribute 30 times. Loyalty without exception.",
        icon="📿",
        rarity="Uncommon",
        unlock_type="tribute_count_gte",
        unlock_threshold=30,
        unlock_label="Claim /tribute 30 times",
    ),

    # ── Ascension badges ──────────────────────────────────────────────────────

    "first_ascent": Badge(
        id="first_ascent",
        name="First Ascent",
        description="Purchased the first rank. The climb has begun.",
        icon="⬆",
        rarity="Common",
        unlock_type="rank_index_gte",
        unlock_threshold=1,       # Index 1 = Vermin
        unlock_label="Buy any rank (reach Vermin)",
    ),
    "infernal_scholar": Badge(
        id="infernal_scholar",
        name="Infernal Scholar",
        description="Reached the rank of Demonology. Knowledge is currency.",
        icon="📖",
        rarity="Rare",
        unlock_type="rank_index_gte",
        unlock_threshold=6,       # Index 6 = Demonology
        unlock_label="Reach Demonology rank",
    ),
    "abyss_crowned": Badge(
        id="abyss_crowned",
        name="Abyss Crowned",
        description="Ascended to Archdemon. The void bows.",
        icon="👁",
        rarity="Epic",
        unlock_type="rank_index_gte",
        unlock_threshold=8,       # Index 8 = Archdemon
        unlock_label="Reach Archdemon rank",
    ),
    "noble_blood": Badge(
        id="noble_blood",
        name="Noble Blood",
        description="Crossed into the noble ranks of the Kingdom.",
        icon="🏰",
        rarity="Epic",
        unlock_type="rank_index_gte",
        unlock_threshold=10,      # Index 10 = Baron
        unlock_label="Reach Baron rank",
    ),
    "thronebound": Badge(
        id="thronebound",
        name="Thronebound",
        description="Reached the upper echelons. The throne is within reach.",
        icon="♛",
        rarity="Legendary",
        unlock_type="rank_index_gte",
        unlock_threshold=14,      # Index 14 = Duke
        unlock_label="Reach Duke rank",
    ),

    # ── Loyalty / time badges ─────────────────────────────────────────────────

    "abyss_loyalist": Badge(
        id="abyss_loyalist",
        name="Abyss Loyalist",
        description="Member of the Kingdom for 30 days.",
        icon="🌑",
        rarity="Uncommon",
        unlock_type="account_age_days",
        unlock_threshold=30,
        unlock_label="30 days in the Kingdom",
    ),
    "marked_by_time": Badge(
        id="marked_by_time",
        name="Marked by Time",
        description="90 days in the Kingdom. The Abyss has shaped you.",
        icon="⌛",
        rarity="Rare",
        unlock_type="account_age_days",
        unlock_threshold=90,
        unlock_label="90 days in the Kingdom",
    ),

    # ── Special / manual badges ───────────────────────────────────────────────

    "duel_champion": Badge(
        id="duel_champion",
        name="Duel Champion",
        description="Won an official Kingdom duel. Victory is permanent.",
        icon="⚔",
        rarity="Epic",
        unlock_type="manual",
        unlock_threshold=None,
        unlock_label="Win an official Kingdom duel",
    ),
    "branded_soul": Badge(
        id="branded_soul",
        name="Branded Soul",
        description="A server booster. The Kingdom is stronger for it.",
        icon="💜",
        rarity="Special",
        unlock_type="manual",
        unlock_threshold=None,
        unlock_label="Boost the server",
    ),
    "cerberus_guard": Badge(
        id="cerberus_guard",
        name="Cerberus Guard",
        description="Passed a Cerberus audit without penalty.",
        icon="🐕",
        rarity="Rare",
        unlock_type="cerberus_cleared",
        unlock_threshold=None,
        unlock_label="Pass a Cerberus audit clean",
    ),
    "void_walker": Badge(
        id="void_walker",
        name="Void Walker",
        description="A soul that has touched the void. Origin: unknown.",
        icon="🌀",
        rarity="Legendary",
        unlock_type="manual",
        unlock_threshold=None,
        unlock_label="Awarded by the Kingdom hierarchy",
    ),
    "founder": Badge(
        id="founder",
        name="Founder",
        description="An original member. Present at the Kingdom's creation.",
        icon="🔰",
        rarity="Special",
        unlock_type="manual",
        unlock_threshold=None,
        unlock_label="Founding member of Kingdom of Hell",
    ),
    "record_verified": Badge(
        id="record_verified",
        name="Record Verified",
        description="Passed a major Cerberus audit with full clearance.",
        icon="✅",
        rarity="Epic",
        unlock_type="manual",
        unlock_threshold=None,
        unlock_label="Pass a major Cerberus audit",
    ),
}

RARITY_ORDER = {
    "Common": 0, "Uncommon": 1, "Rare": 2,
    "Epic": 3, "Legendary": 4, "Special": 5,
}
RARITY_COLORS = {
    "Common":    "⬜",
    "Uncommon":  "🟩",
    "Rare":      "🟦",
    "Epic":      "🟪",
    "Legendary": "🟨",
    "Special":   "🟥",
}

AUTO_UNLOCK_TYPES = {
    "balance_gte", "taxes_gte", "grind_count_gte",
    "tribute_count_gte", "rank_index_gte", "account_age_days",
    "jackpot", "cerberus_cleared",
}


def get_badge(badge_id: str) -> Optional[Badge]:
    return BADGES_CATALOG.get(badge_id)


def get_all_badges() -> Dict[str, Badge]:
    return BADGES_CATALOG
