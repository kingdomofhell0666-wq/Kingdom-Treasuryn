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
        description="The blood of kings never dries. It seeps into everything beneath it.",
        price_dc=25_000,
        rarity="Uncommon",
        color=0xA80000,
        title_banner="♛  KINGDOM IDENTITY CARD",
        rank_prefix="♛ ",
        rank_suffix=" ♛",
        title_prefix="⚔ ",
        wealth_prefix="🩸",
        separator="⸺ ⸺ ⸺ ⸺ ⸺ ⸺ ⸺ ⸺",
        footer_flavor='"Blood remembers every name it was spilled for."',
        theme_tag="Blood Crown",
        stat_icon="⚔",
    ),
    "abyss_smoke": CardSkin(
        id="abyss_smoke",
        name="Abyss Smoke",
        description="Where the void breathes. Where smoke becomes something that watches.",
        price_dc=50_000,
        rarity="Rare",
        color=0x2A0A50,
        title_banner="🌑  KINGDOM IDENTITY CARD",
        rank_prefix="◈ ",
        rank_suffix=" ◈",
        title_prefix="✦ ",
        wealth_prefix="🌑",
        separator="· ∙ · ∙ · ∙ · ∙ · ∙ · ∙ · ∙",
        footer_flavor='"The void does not collect. It keeps."',
        theme_tag="Abyss Smoke",
        stat_icon="✦",
    ),
    "infernal_gold": CardSkin(
        id="infernal_gold",
        name="Infernal Gold",
        description="The card of those who have made gold afraid of them.",
        price_dc=75_000,
        rarity="Rare",
        color=0xAA7800,
        title_banner="✦  KINGDOM IDENTITY CARD",
        rank_prefix="✦ ",
        rank_suffix=" ✦",
        title_prefix="✧ ",
        wealth_prefix="✦",
        separator="═══════════════════════════",
        footer_flavor='"Gold does not flow to the worthy. It flows to the ruthless."',
        theme_tag="Infernal Gold",
        stat_icon="✧",
    ),
    "royal_dark": CardSkin(
        id="royal_dark",
        name="Royal Dark",
        description="The court does not announce itself. It simply arrives.",
        price_dc=100_000,
        rarity="Epic",
        color=0x0A1040,
        title_banner="🔱  KINGDOM IDENTITY CARD",
        rank_prefix="🔱 ",
        rank_suffix=" 🔱",
        title_prefix="◆ ",
        wealth_prefix="🔱",
        separator="─══════════════════════════─",
        footer_flavor='"By decree of those who need no decree."',
        theme_tag="Royal Dark",
        stat_icon="◆",
    ),
    "black_throne": CardSkin(
        id="black_throne",
        name="Black Throne",
        description="Power does not need a name. It needs a chair and a room that empties when you enter.",
        price_dc=150_000,
        rarity="Epic",
        color=0x0E0A0A,
        title_banner="🖤  KINGDOM IDENTITY CARD",
        rank_prefix="◼ ",
        rank_suffix=" ◼",
        title_prefix="◼ ",
        wealth_prefix="🖤",
        separator="▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪",
        footer_flavor='"The throne is not inherited. It is outlasted."',
        theme_tag="Black Throne",
        stat_icon="◼",
    ),
    "crimson_sigil": CardSkin(
        id="crimson_sigil",
        name="Crimson Sigil",
        description="The sigil does not mark the chosen. It marks what the Kingdom has claimed.",
        price_dc=250_000,
        rarity="Legendary",
        color=0xA01830,
        title_banner="⸸  KINGDOM IDENTITY CARD",
        rank_prefix="⸸ ",
        rank_suffix=" ⸸",
        title_prefix="⸸ ",
        wealth_prefix="⸸",
        separator="⸸ ─────────────────────── ⸸",
        footer_flavor='"Marked. Bound. Permanent."',
        theme_tag="Crimson Sigil",
        stat_icon="⸸",
    ),
    # ── New skins ──────────────────────────────────────────────────────────────
    "ember_ash": CardSkin(
        id="ember_ash",
        name="Ember Ash",
        description="What remains after the fire. Not extinction — transformation.",
        price_dc=35_000,
        rarity="Uncommon",
        color=0x7A3A10,
        title_banner="🔥  KINGDOM IDENTITY CARD",
        rank_prefix="🔥 ",
        rank_suffix="",
        title_prefix="◈ ",
        wealth_prefix="🔥",
        separator="· ─ · ─ · ─ · ─ · ─ · ─ ·",
        footer_flavor='"Ash does not mourn the flame."',
        theme_tag="Ember Ash",
        stat_icon="◈",
    ),
    "bone_pale": CardSkin(
        id="bone_pale",
        name="Bone Pale",
        description="The colour of old power. Stripped bare, bleached, and still standing.",
        price_dc=60_000,
        rarity="Rare",
        color=0x6E5C3E,
        title_banner="☠  KINGDOM IDENTITY CARD",
        rank_prefix="☠ ",
        rank_suffix="",
        title_prefix="✧ ",
        wealth_prefix="☠",
        separator="─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─",
        footer_flavor='"Even bones remember the name."',
        theme_tag="Bone Pale",
        stat_icon="✧",
    ),
    "phantom_teal": CardSkin(
        id="phantom_teal",
        name="Phantom Teal",
        description="The colour of deep water. The colour of things that are almost seen.",
        price_dc=70_000,
        rarity="Rare",
        color=0x006472,
        title_banner="🌊  KINGDOM IDENTITY CARD",
        rank_prefix="◆ ",
        rank_suffix=" ◆",
        title_prefix="◇ ",
        wealth_prefix="🌊",
        separator="≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈",
        footer_flavor='"The depths do not yield. They consume."',
        theme_tag="Phantom Teal",
        stat_icon="◆",
    ),
    "midnight_azure": CardSkin(
        id="midnight_azure",
        name="Midnight Azure",
        description="The hour after midnight, when the sky becomes a weapon.",
        price_dc=80_000,
        rarity="Rare",
        color=0x0F2D6B,
        title_banner="🌌  KINGDOM IDENTITY CARD",
        rank_prefix="★ ",
        rank_suffix=" ★",
        title_prefix="✦ ",
        wealth_prefix="🌌",
        separator="· · · · · · · · · · · · · · ·",
        footer_flavor='"Midnight does not wait. It arrives."',
        theme_tag="Midnight Azure",
        stat_icon="★",
    ),
    "magma_core": CardSkin(
        id="magma_core",
        name="Magma Core",
        description="The interior of something ancient and furious. It has not cooled.",
        price_dc=120_000,
        rarity="Epic",
        color=0x8C2800,
        title_banner="🌋  KINGDOM IDENTITY CARD",
        rank_prefix="▲ ",
        rank_suffix=" ▲",
        title_prefix="⚡ ",
        wealth_prefix="🌋",
        separator="▬ ▬ ▬ ▬ ▬ ▬ ▬ ▬ ▬ ▬ ▬ ▬",
        footer_flavor='"The core does not cool. It waits."',
        theme_tag="Magma Core",
        stat_icon="▲",
    ),
    "cursed_silver": CardSkin(
        id="cursed_silver",
        name="Cursed Silver",
        description="Silver without shine. The metal of things that have been touched too many times.",
        price_dc=140_000,
        rarity="Epic",
        color=0x3A3A52,
        title_banner="⚔  KINGDOM IDENTITY CARD",
        rank_prefix="⚔ ",
        rank_suffix=" ⚔",
        title_prefix="◇ ",
        wealth_prefix="⚔",
        separator="════════════════════════════",
        footer_flavor='"Silver remembers every hand that held it."',
        theme_tag="Cursed Silver",
        stat_icon="◇",
    ),
    "verdant_venom": CardSkin(
        id="verdant_venom",
        name="Verdant Venom",
        description="Poison made into identity. Beautiful. Lethal. Inevitable.",
        price_dc=200_000,
        rarity="Legendary",
        color=0x1A5C1E,
        title_banner="☣  KINGDOM IDENTITY CARD",
        rank_prefix="☣ ",
        rank_suffix=" ☣",
        title_prefix="⚗ ",
        wealth_prefix="☣",
        separator="✦ ─────────────────────── ✦",
        footer_flavor='"Everything it touches belongs to it."',
        theme_tag="Verdant Venom",
        stat_icon="⚗",
    ),
    "abyssal_jade": CardSkin(
        id="abyssal_jade",
        name="Abyssal Jade",
        description="From the bottom of something that has no name. Ancient. Immovable. Watching.",
        price_dc=350_000,
        rarity="Legendary",
        color=0x0B4A34,
        title_banner="🐉  KINGDOM IDENTITY CARD",
        rank_prefix="龍 ",
        rank_suffix=" 龍",
        title_prefix="✦ ",
        wealth_prefix="🐉",
        separator="─══════════════════════════─",
        footer_flavor='"The abyss does not speak. It has already decided."',
        theme_tag="Abyssal Jade",
        stat_icon="✦",
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
# Levels are additive — higher number = higher rank.
# Staff/Nobility override Member ranks.
# Admin/Owner override everything.

RANK_ORDER: Dict[str, int] = {
    # Member progression
    "Forsaken":     0,
    "Vermin":       1,
    "Corrupted":    2,
    "Folklore":     3,
    "Mythology":    4,
    "Demonology":   5,
    "Eschatology":  6,
    "Archangel":    7,
    "Archdemon":    8,
    # Nobility
    "Knight":       9,
    "Baron":        10,
    "Viscount":     11,
    "Count":        12,
    "Marquis":      13,
    "Duke":         14,
    # Staff / Legion
    "Legionnaires": 15,
    "Centurion":    16,
    # High Council / Moderation
    "Legates":      17,
    "Chancellor":   18,
    # Royal / Admin
    "Princesses":   19,
    "Princes":      19,
    "Consorts":     20,
    # Owner
    "Sovereign":    21,
}


def rank_idx(rank: str) -> int:
    return RANK_ORDER.get(rank, 0)


# ─── Discord Role ID → Rank Name Mapping ─────────────────────────────────────
# Maps each Discord role ID to its Kingdom rank name.
# Used to detect rank in real-time from member roles at market open.

DISCORD_ROLE_RANKS: Dict[int, str] = {
    # Owner
    1290484661419638873: "Sovereign",
    # Admin / Royal Family
    1418279591528890508: "Consorts",
    1290484661419638870: "Princes",
    1489067882557079603: "Princesses",
    # Moderation / High Council
    1414110540128718898: "Chancellor",
    1489108767353344130: "Legates",
    # Nobility
    1489130140532211874: "Duke",
    1489129490209706045: "Marquis",
    1489128625474113697: "Count",
    1489127901461876807: "Viscount",
    1489127375206613082: "Baron",
    1489126295798415380: "Knight",
    # Staff / Legion
    1489108909682589696: "Centurion",
    1290484661419638871: "Legionnaires",
    # Member Ranks
    1290530372748185612: "Archdemon",
    1290530281580662796: "Archangel",
    1290529262377500815: "Demonology",
    1290484661419638869: "Eschatology",
    1290484661419638868: "Folklore",
    1290484661419638867: "Mythology",
    1290484661419638866: "Corrupted",
    1484302112241352744: "Vermin",
    1489101267048468490: "Forsaken",
}


def detect_rank_from_roles(member_roles) -> str:
    """
    Return the highest Kingdom rank for a member based on their Discord roles.

    member_roles: iterable of objects with an `.id` attribute (discord.Role list).
    Falls back to "Forsaken" if no known role is found.
    """
    best_rank  = "Forsaken"
    best_level = RANK_ORDER.get("Forsaken", 0)
    for role in member_roles:
        rank_name = DISCORD_ROLE_RANKS.get(role.id)
        if rank_name:
            level = RANK_ORDER.get(rank_name, -1)
            if level > best_level:
                best_level = level
                best_rank  = rank_name
    return best_rank


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
