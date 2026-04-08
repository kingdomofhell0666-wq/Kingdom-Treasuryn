from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class CardSkin:
    id: str
    name: str
    color: int
    title_banner: str
    rank_prefix: str
    rank_suffix: str
    title_prefix: str
    wealth_prefix: str
    separator: str
    footer_flavor: str
    theme_tag: str
    stat_icon: str


SKINS: Dict[str, CardSkin] = {
    "default": CardSkin(
        id="default",
        name="Infernal Standard",
        color=0x6B0000,
        title_banner="👑  KINGDOM IDENTITY CARD",
        rank_prefix="",
        rank_suffix="",
        title_prefix="",
        wealth_prefix="💰",
        separator="━━━━━━━━━━━━━━━━━━━━━━━━━━",
        footer_flavor='"The Abyss remembers your name."',
        theme_tag="Infernal Standard",
        stat_icon="📜",
    ),
    "blood_crown": CardSkin(
        id="blood_crown",
        name="Blood Crown",
        color=0x9B0000,
        title_banner="♛  KINGDOM IDENTITY CARD",
        rank_prefix="♛ ",
        rank_suffix=" ♛",
        title_prefix="⚔ ",
        wealth_prefix="🩸",
        separator="─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─",
        footer_flavor='"The blood of kings flows through the ledger."',
        theme_tag="Blood Crown",
        stat_icon="⚔",
    ),
    "abyss_smoke": CardSkin(
        id="abyss_smoke",
        name="Abyss Smoke",
        color=0x1A0A2E,
        title_banner="🌑  KINGDOM IDENTITY CARD",
        rank_prefix="◈ ",
        rank_suffix=" ◈",
        title_prefix="✦ ",
        wealth_prefix="🌑",
        separator="· · · · · · · · · · · · · · ·",
        footer_flavor='"The void does not forget. It collects."',
        theme_tag="Abyss Smoke",
        stat_icon="✦",
    ),
    "infernal_gold": CardSkin(
        id="infernal_gold",
        name="Infernal Gold",
        color=0xB8860B,
        title_banner="✦  KINGDOM IDENTITY CARD",
        rank_prefix="✦ ",
        rank_suffix=" ✦",
        title_prefix="✧ ",
        wealth_prefix="✦",
        separator="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        footer_flavor='"Gold is not earned. It is seized."',
        theme_tag="Infernal Gold",
        stat_icon="✧",
    ),
    "royal_dark": CardSkin(
        id="royal_dark",
        name="Royal Dark",
        color=0x0D0D2B,
        title_banner="🔱  KINGDOM IDENTITY CARD",
        rank_prefix="🔱 ",
        rank_suffix="",
        title_prefix="◆ ",
        wealth_prefix="🔱",
        separator="════════════════════════════",
        footer_flavor='"By decree of the Infernal Court."',
        theme_tag="Royal Dark",
        stat_icon="◆",
    ),
    "black_throne": CardSkin(
        id="black_throne",
        name="Black Throne",
        color=0x111111,
        title_banner="🖤  KINGDOM IDENTITY CARD",
        rank_prefix="▸ ",
        rank_suffix="",
        title_prefix="▸ ",
        wealth_prefix="🖤",
        separator="▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀",
        footer_flavor='"The throne is not inherited. It is taken."',
        theme_tag="Black Throne",
        stat_icon="▸",
    ),
    "crimson_sigil": CardSkin(
        id="crimson_sigil",
        name="Crimson Sigil",
        color=0xB22222,
        title_banner="🔴  KINGDOM IDENTITY CARD",
        rank_prefix="⸸ ",
        rank_suffix=" ⸸",
        title_prefix="⸸ ",
        wealth_prefix="🔴",
        separator="✦ ─────────────────────── ✦",
        footer_flavor='"Marked by the Sigil. Bound to the Kingdom."',
        theme_tag="Crimson Sigil",
        stat_icon="⸸",
    ),
}

DEFAULT_SKIN_ID = "default"


def get_skin(skin_id: Optional[str]) -> CardSkin:
    if not skin_id or skin_id not in SKINS:
        return SKINS[DEFAULT_SKIN_ID]
    return SKINS[skin_id]


def get_all_skins() -> Dict[str, CardSkin]:
    return SKINS


# ─── All available titles ─────────────────────────────────────────────────────

TITLES = [
    "Unmarked",
    "Royal Gambler",
    "Abyss Walker",
    "Hand of the Kingdom",
    "Night Winner",
    "Bloodbound",
    "Infernal Patron",
    "Void Merchant",
    "Shadow Sovereign",
    "Coin of the Damned",
    "Eternal Debtor",
    "Cerberus Favored",
    "The Untaxed",
    "Infernal Investor",
    "The Unbranded",
]

DEFAULT_TITLE = "Unmarked"
