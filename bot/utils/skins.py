from dataclasses import dataclass
from typing import Dict, List, Optional


# ─── Card Skin ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CardSkin:
    id: str
    name: str
    description: str
    price_dc: int
    rarity: str
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
        description="The mark of every soul in the Kingdom. Grim, enduring, bound in flame.",
        price_dc=0,
        rarity="Default",
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
        description="Forged in the blood of fallen kings. A crown that demands tribute.",
        price_dc=25_000,
        rarity="Uncommon",
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
        description="Woven from void itself. Those who see it do not forget it.",
        price_dc=50_000,
        rarity="Rare",
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
        description="Wealth made manifest. Only those who have truly earned belong beneath this gold.",
        price_dc=75_000,
        rarity="Rare",
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
        description="The sigil of the infernal court. Reserved for those with ambition beyond rank.",
        price_dc=100_000,
        rarity="Epic",
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
        description="Power without mercy. The card of those who rule from shadow.",
        price_dc=150_000,
        rarity="Epic",
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
        description="Marked by the ancient sigil. A card that announces itself before it is shown.",
        price_dc=250_000,
        rarity="Legendary",
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

RARITY_ORDER = {"Default": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4}
RARITY_COLORS = {
    "Default":   "⬜",
    "Uncommon":  "🟩",
    "Rare":      "🟦",
    "Epic":      "🟪",
    "Legendary": "🟨",
}

DEFAULT_SKIN_ID = "default"


def get_skin(skin_id: Optional[str]) -> CardSkin:
    if not skin_id or skin_id not in SKINS:
        return SKINS[DEFAULT_SKIN_ID]
    return SKINS[skin_id]


def get_all_skins() -> Dict[str, CardSkin]:
    return SKINS


# ─── Title ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Title:
    name: str
    description: str
    price_dc: int
    rarity: str


TITLES_CATALOG: Dict[str, Title] = {
    "Unmarked": Title(
        name="Unmarked",
        description="The default title. Every soul begins here.",
        price_dc=0,
        rarity="Default",
    ),
    "Royal Gambler": Title(
        name="Royal Gambler",
        description="For those who risk it all at the table of fate.",
        price_dc=10_000,
        rarity="Common",
    ),
    "Night Winner": Title(
        name="Night Winner",
        description="Claimed the night. The ledger agrees.",
        price_dc=12_000,
        rarity="Common",
    ),
    "Eternal Debtor": Title(
        name="Eternal Debtor",
        description="Owes the Kingdom everything. And keeps spending anyway.",
        price_dc=15_000,
        rarity="Common",
    ),
    "Abyss Walker": Title(
        name="Abyss Walker",
        description="Travels the void between ranks, unbothered by the dark.",
        price_dc=20_000,
        rarity="Uncommon",
    ),
    "Bloodbound": Title(
        name="Bloodbound",
        description="Sealed in blood. Their loyalty is not a choice.",
        price_dc=25_000,
        rarity="Uncommon",
    ),
    "Hand of the Kingdom": Title(
        name="Hand of the Kingdom",
        description="Trusted by the hierarchy. A title of quiet authority.",
        price_dc=30_000,
        rarity="Uncommon",
    ),
    "Infernal Patron": Title(
        name="Infernal Patron",
        description="A pillar of the Kingdom's wealth. The Treasury takes notice.",
        price_dc=35_000,
        rarity="Rare",
    ),
    "Void Merchant": Title(
        name="Void Merchant",
        description="Trades in things that should not have a price.",
        price_dc=40_000,
        rarity="Rare",
    ),
    "Coin of the Damned": Title(
        name="Coin of the Damned",
        description="Their wealth carries a curse. But it still spends.",
        price_dc=45_000,
        rarity="Rare",
    ),
    "Infernal Investor": Title(
        name="Infernal Investor",
        description="Profit above all. Even in the fires below.",
        price_dc=50_000,
        rarity="Rare",
    ),
    "Throne Witness": Title(
        name="Throne Witness",
        description="Stood before the Black Throne and did not falter.",
        price_dc=55_000,
        rarity="Epic",
    ),
    "Shadow Sovereign": Title(
        name="Shadow Sovereign",
        description="Governs from the dark. Known, but never seen.",
        price_dc=60_000,
        rarity="Epic",
    ),
    "Cerberus Favored": Title(
        name="Cerberus Favored",
        description="The hound looked — and chose not to bite.",
        price_dc=65_000,
        rarity="Epic",
    ),
    "Marked Noble": Title(
        name="Marked Noble",
        description="Branded by the Kingdom. Noblesse with an infernal edge.",
        price_dc=70_000,
        rarity="Epic",
    ),
    "The Untaxed": Title(
        name="The Untaxed",
        description="How? The Kingdom does not discuss how.",
        price_dc=80_000,
        rarity="Legendary",
    ),
    "The Unbranded": Title(
        name="The Unbranded",
        description="Claimed no mark. Yet the Kingdom knows exactly who they are.",
        price_dc=85_000,
        rarity="Legendary",
    ),
    "Coin Reaper": Title(
        name="Coin Reaper",
        description="Death and currency — both inevitabilities. They deal in both.",
        price_dc=100_000,
        rarity="Legendary",
    ),
}

DEFAULT_TITLE = "Unmarked"

# Flat list for backward-compat choice lists
TITLES: List[str] = list(TITLES_CATALOG.keys())


# ─── Rank Order ───────────────────────────────────────────────────────────────

RANK_ORDER: Dict[str, int] = {
    "Forsaken": 0, "Vermin": 1, "Corrupted": 2, "Folklore": 3, "Mythology": 4,
    "Demonology": 5, "Eschatology": 6, "Archangel": 7, "Archdemon": 8,
    "Knight": 9, "Baron": 10, "Viscount": 11, "Count": 12, "Marquis": 13, "Duke": 14,
    "Chancellor": 15,
}


def rank_idx(rank: str) -> int:
    return RANK_ORDER.get(rank, 0)


# ─── Relic ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Relic:
    id:          str
    name:        str
    description: str
    effect_desc: str
    price_dc:    int
    rarity:      str
    min_rank:    str   # "" = all ranks


RELICS_CATALOG: Dict[str, Relic] = {
    "soul_aura": Relic(
        id="soul_aura",
        name="Soul Aura",
        description="A pale luminescence extends beyond the card's edge. It watches.",
        effect_desc="A pale luminescence surrounds your presence. The air grows cold where you stand.",
        price_dc=35_000,
        rarity="Uncommon",
        min_rank="",
    ),
    "infernal_crown": Relic(
        id="infernal_crown",
        name="Infernal Crown",
        description="A crown of pure sin floats above. It is not worn. It hovers.",
        effect_desc="A crown of burning obsidian hovers above your form. It does not touch you. It does not need to.",
        price_dc=80_000,
        rarity="Rare",
        min_rank="Demonology",
    ),
    "void_drift": Relic(
        id="void_drift",
        name="Void Drift",
        description="The void leaks through the card. Particles of nothing orbit your presence.",
        effect_desc="Fragments of the void drift around you like dark snow. They do not fall. They orbit.",
        price_dc=120_000,
        rarity="Rare",
        min_rank="Eschatology",
    ),
    "crimson_chains": Relic(
        id="crimson_chains",
        name="Crimson Chains",
        description="Chains of blood-red energy bind the border. They are not locked. They choose to hold.",
        effect_desc="Blood-forged chains orbit the edges of your identity. They are decorative. They are also real.",
        price_dc=200_000,
        rarity="Epic",
        min_rank="Archangel",
    ),
    "abyssal_veil": Relic(
        id="abyssal_veil",
        name="Abyssal Veil",
        description="A translucent shroud of darkness descends. Even the card seems afraid.",
        effect_desc="A shroud of the deep abyss falls across your form. The darkness does not conceal you. It announces you.",
        price_dc=300_000,
        rarity="Epic",
        min_rank="Archdemon",
    ),
    "sanguine_halo": Relic(
        id="sanguine_halo",
        name="Sanguine Halo",
        description="Above all others. The halo does not bless. It marks a debt.",
        effect_desc="A halo of deep crimson and gold crowns your silhouette. It is not a reward. It is a warning.",
        price_dc=500_000,
        rarity="Legendary",
        min_rank="Knight",
    ),
}


def get_relic(relic_id: Optional[str]) -> Optional[Relic]:
    if not relic_id:
        return None
    return RELICS_CATALOG.get(relic_id)


# ─── Badge ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Badge:
    id:          str
    name:        str
    description: str
    price_dc:    int
    rarity:      str
    icon:        str   # emoji displayed on identity
    min_rank:    str   # "" = all ranks


BADGES_CATALOG: Dict[str, Badge] = {
    "haunted": Badge(
        id="haunted", name="Haunted",
        description="Something follows this soul everywhere it goes. No one else can see it.",
        price_dc=5_000, rarity="Common", icon="🕯️", min_rank="",
    ),
    "void_sworn": Badge(
        id="void_sworn", name="Void Sworn",
        description="An oath was made to the void. The void did not forget.",
        price_dc=10_000, rarity="Common", icon="🌑", min_rank="",
    ),
    "bloodpact": Badge(
        id="bloodpact", name="Bloodpact",
        description="Sealed in something older than ink. The pact holds both ways.",
        price_dc=15_000, rarity="Uncommon", icon="🩸", min_rank="Corrupted",
    ),
    "infernal_mark": Badge(
        id="infernal_mark", name="Infernal Mark",
        description="The Kingdom burned its seal into their record. It does not fade.",
        price_dc=25_000, rarity="Uncommon", icon="🔥", min_rank="Folklore",
    ),
    "wraith_touched": Badge(
        id="wraith_touched", name="Wraith-Touched",
        description="Something from the other side reached through. Left a mark. Then retreated.",
        price_dc=40_000, rarity="Rare", icon="👁️", min_rank="Mythology",
    ),
    "cerberus_marked": Badge(
        id="cerberus_marked", name="Cerberus Marked",
        description="The three-headed guardian looked directly at this soul. And nodded.",
        price_dc=60_000, rarity="Rare", icon="🐺", min_rank="Demonology",
    ),
    "throne_carved": Badge(
        id="throne_carved", name="Throne Carved",
        description="Their name was cut directly into the Black Throne. Not as an honor. As a record.",
        price_dc=100_000, rarity="Epic", icon="⛓️", min_rank="Archangel",
    ),
    "kingdom_ascendant": Badge(
        id="kingdom_ascendant", name="Kingdom Ascendant",
        description="They have risen so far, the Kingdom itself took note. The Abyss watches.",
        price_dc=200_000, rarity="Legendary", icon="👑", min_rank="Knight",
    ),
}


def get_badge(badge_id: Optional[str]) -> Optional[Badge]:
    if not badge_id:
        return None
    return BADGES_CATALOG.get(badge_id)
