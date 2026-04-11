"""
Kingdom Treasury — Infernal Market Hub
The most immersive market experience achievable inside Discord.

Flow: hub → category browse → preview → confirm → [sealing] → done
Every transition edits the same ephemeral message in-place.
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Set

import discord

from ..utils.skins import (
    SKINS, TITLES_CATALOG, RELICS_CATALOG, BADGES_CATALOG,
    rank_idx as _rank_idx,
)

log = logging.getLogger("kingdom_treasury")

# ─── Currency & separators ────────────────────────────────────────────────────

_DC  = "<:devilcoinStack:1492184333392412692>"
_SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
_SEP_SHORT = "──────────────────────────"

# ─── Atmosphere lines (rotate randomly, use sparingly) ───────────────────────

_ATMOSPHERE: List[str] = [
    "*The Kingdom is watching.*",
    "*This place remembers faces.*",
    "*Some offerings are never forgotten.*",
    "*Not every soul leaves unchanged.*",
    "*What you claim here claims something back.*",
    "*The fire burns low. Eyes watch from the dark.*",
    "*Power is not given. It is taken.*",
    "*The ledger records everything.*",
    "*The Kingdom does not forget debts.*",
    "*Only the marked may enter.*",
]

def _atmosphere() -> str:
    return random.choice(_ATMOSPHERE)

# ─── Rarity palette ──────────────────────────────────────────────────────────

_RARITY_COLOR: Dict[str, int] = {
    "Default":   0x1A0A0A,
    "Common":    0x2A1A1A,
    "Uncommon":  0x1A1A00,
    "Rare":      0x000D26,
    "Epic":      0x1A0033,
    "Legendary": 0x1A0A00,
    "Mythic":    0x2B0000,
}

_RARITY_SIGIL: Dict[str, str] = {
    "Default":   "⬛",
    "Common":    "◼",
    "Uncommon":  "🟫",
    "Rare":      "🔷",
    "Epic":      "🟣",
    "Legendary": "🟡",
    "Mythic":    "🔴",
}

_RARITY_LABEL: Dict[str, str] = {
    "Default":   "DEFAULT",
    "Common":    "COMMON",
    "Uncommon":  "UNCOMMON",
    "Rare":      "RARE",
    "Epic":      "EPIC",
    "Legendary": "LEGENDARY",
    "Mythic":    "MYTHIC",
}

# ─── Category metadata ────────────────────────────────────────────────────────

_CAT_ICON: Dict[str, str] = {
    "relics": "🔮",
    "titles": "👑",
    "skins":  "🎭",
    "badges": "🎖️",
}

_CAT_HEADER: Dict[str, str] = {
    "relics": "RELICS",
    "titles": "TITLES",
    "skins":  "SKINS",
    "badges": "BADGES",
}

_CAT_INTRO: Dict[str, str] = {
    "relics": (
        "*Fragments of power.*\n"
        "*They do not decorate.*\n"
        "*They alter what stands before others.*"
    ),
    "titles": (
        "*Names become chains.*\n"
        "*Or weapons.*\n"
        "*Choose which you need.*"
    ),
    "skins": (
        "*You do not remain unchanged here.*\n"
        "*The old frame is no longer enough.*\n"
        "*Become what survives.*"
    ),
    "badges": (
        "*Some marks are earned.*\n"
        "*Others are survived.*\n"
        "*All of them remember.*"
    ),
}

# ─── Image registry ──────────────────────────────────────────────────────────
# All images are verified direct Wikimedia Commons CDN URLs (resolved via API).
# Public domain paintings by John Martin (1789–1854). Permanently hosted.
# Discord embeds load these directly — no redirects, no rate limiting.
#
# Verified paintings:
#  Hub / Seal       →  "Pandemonium" (c.1841, WGA) — Satan's court in Hell
#  Acquire          →  "The Great Day of His Wrath" (1853) — divine fire/judgment
#  Exit             →  "The Plains of Heaven" (1853) — fading from the Exchange
#  Relics           →  "The Great Day of His Wrath" — cursed power, fire
#  Titles           →  "Belshazzar's Feast" (1826) — throne of fallen kings
#  Skins            →  "Sodom and Gomorrah" — dark transformation, destruction
#  Badges           →  "Ruins of an Ancient City" — ancient marks, carved stone

_CDN = "https://upload.wikimedia.org/wikipedia/commons/"

_IMG: Dict[str, Optional[str]] = {
    # Main screens
    "hub":     _CDN + "6/65/John_Martin_-_Pandemonium_-_WGA14149.jpg",
    "seal":    _CDN + "6/65/John_Martin_-_Pandemonium_-_WGA14149.jpg",
    "acquire": _CDN + "5/50/John_Martin_-_The_Great_Day_of_His_Wrath_-_Google_Art_Project.jpg",
    "exit":    _CDN + "7/79/John_Martin_-_The_Plains_of_Heaven_-_Google_Art_Project.jpg",
    # Category banners
    "relics":  _CDN + "5/50/John_Martin_-_The_Great_Day_of_His_Wrath_-_Google_Art_Project.jpg",
    "titles":  _CDN + "e/ec/John_Martin_-_Belshazzar%27s_Feast_-_Google_Art_Project.jpg",
    "skins":   _CDN + "e/e1/John_Martin_-_Sodom_and_Gomorrah.jpg",
    "badges":  _CDN + "6/6f/John_Martin_-_Ruins_of_an_Ancient_City_-_Cleveland_Art_Museum.jpg",
}

# Per-item image overrides (item.id → URL). Falls back to category image.
# Add custom URLs here for individual item art as the server grows.
_ITEM_IMG: Dict[str, Optional[str]] = {
    # Skins — inherits category "skins" fallback
    "blood_crown":   None,
    "abyss_smoke":   None,
    "infernal_gold": None,
    "royal_dark":    None,
    "black_throne":  None,
    "crimson_sigil": None,
    # Relics — inherits category "relics" fallback
    "soul_aura":       None,
    "infernal_crown":  None,
    "void_drift":      None,
    "crimson_chains":  None,
    "abyssal_veil":    None,
    "sanguine_halo":   None,
    # Badges — inherits category "badges" fallback
}

# Per-item lore quotes (psychological impact lines shown in item embeds)
_ITEM_LORE: Dict[str, str] = {
    # Skins
    "blood_crown":   "Worn by those who paid more than coin to earn it.",
    "abyss_smoke":   "Those who see it do not forget it. They are not meant to.",
    "infernal_gold": "Gold is not earned here. It is seized.",
    "royal_dark":    "By decree of the Infernal Court. Not a request.",
    "black_throne":  "The throne is not inherited. It is taken.",
    "crimson_sigil": "Marked by the sigil. Bound to the Kingdom. Forever.",
    # Relics
    "soul_aura":       "This presence does not follow everyone. Only those the Kingdom has noticed.",
    "infernal_crown":  "It does not touch you. It does not need to.",
    "void_drift":      "They do not fall. They orbit. Endlessly.",
    "crimson_chains":  "They are decorative. They are also real.",
    "abyssal_veil":    "The darkness does not conceal you. It announces you.",
    "sanguine_halo":   "It is not a reward. It is a warning.",
    # Titles
    "Royal Gambler":       "Fate is not random. It just looks that way to others.",
    "Night Winner":        "The ledger does not lie. They claimed it.",
    "Eternal Debtor":      "The debt is permanent. So is the presence.",
    "Abyss Walker":        "Unbothered by the dark. That alone is notable.",
    "Bloodbound":          "Loyalty was never a question. It was never allowed to be.",
    "Hand of the Kingdom": "Quiet authority. The most dangerous kind.",
    "Infernal Patron":     "The Treasury takes notice. It does not forget.",
    "Void Merchant":       "Some things should not have a price. They do now.",
    "Coin of the Damned":  "The curse spends just fine.",
    "Infernal Investor":   "Profit above all. Even the fires below.",
    "Throne Witness":      "Stood before the Black Throne. Did not falter.",
    "Shadow Sovereign":    "Known. But never seen.",
    "Cerberus Favored":    "The hound looked. And chose not to bite.",
    "Marked Noble":        "Branded by the Kingdom. The mark does not wash off.",
    "The Untaxed":         "How? The Kingdom does not discuss how.",
    "The Unbranded":       "No mark. Yet the Kingdom knows exactly who they are.",
    "Coin Reaper":         "Death and currency. Both inevitabilities. They deal in both.",
    # Badges
    "haunted":           "Something follows this soul. No one else can see it.",
    "void_sworn":        "An oath was made to the void. The void did not forget.",
    "bloodpact":         "The pact holds both ways. It always has.",
    "infernal_mark":     "The Kingdom burned its seal into their record. It does not fade.",
    "wraith_touched":    "Something reached through. Left a mark. Then retreated.",
    "cerberus_marked":   "The three-headed guardian looked directly. And nodded.",
    "throne_carved":     "Their name was cut into the Black Throne. As a record.",
    "kingdom_ascendant": "The Kingdom itself took note. The Abyss watches.",
}

def _item_lore(item) -> str:
    key = getattr(item, "id", None) or getattr(item, "name", "")
    return _ITEM_LORE.get(key, "")

def _item_image(item, cat: str) -> Optional[str]:
    key = getattr(item, "id", None) or ""
    url = _ITEM_IMG.get(key)
    if url:
        return url
    return _IMG.get(cat)

# ─── Status labels ────────────────────────────────────────────────────────────

def _status_equipped(cat: str) -> str:
    if cat == "skins":   return "✦  BOUND TO YOUR FORM"
    if cat == "titles":  return "✦  WORN BENEATH YOUR NAME"
    if cat == "relics":  return "✦  ACTIVE ON YOUR CARD"
    if cat == "badges":  return "✦  DISPLAYED ON YOUR IDENTITY"
    return "✦  EQUIPPED"

# ─── Item helpers ─────────────────────────────────────────────────────────────

def _cat_items(cat: str) -> list:
    if cat == "relics":
        return sorted(RELICS_CATALOG.values(), key=lambda x: x.price_dc)
    elif cat == "titles":
        return sorted(
            [t for t in TITLES_CATALOG.values() if t.price_dc > 0],
            key=lambda x: x.price_dc,
        )
    elif cat == "skins":
        return sorted(
            [s for s in SKINS.values() if s.price_dc > 0],
            key=lambda x: x.price_dc,
        )
    elif cat == "badges":
        return sorted(BADGES_CATALOG.values(), key=lambda x: x.price_dc)
    return []


# ─── Main Market View ─────────────────────────────────────────────────────────

class InfernalMarketHub(discord.ui.View):
    """
    One view manages the entire market session for a single user.
    All state transitions edit the same ephemeral message in place.
    Modes: hub → category → preview → confirm → done
    """

    MODE_HUB      = "hub"
    MODE_CATEGORY = "category"
    MODE_PREVIEW  = "preview"
    MODE_CONFIRM  = "confirm"
    MODE_DONE     = "done"

    def __init__(
        self,
        *,
        owner_id:        int,
        bot,
        guild_id:        str,
        discord_id:      str,
        user_rank:       str,
        user_balance:    int = 0,
        owned_skins:     List[str],
        owned_titles:    List[str],
        owned_relics:    List[str],
        owned_badges:    List[str],
        equipped_skin:   str,
        equipped_title:  str,
        equipped_relic:  str,
        equipped_badges: List[str],
    ):
        super().__init__(timeout=300)
        self.owner_id      = owner_id
        self.bot           = bot
        self.guild_id      = guild_id
        self.discord_id    = discord_id
        self.user_rank     = user_rank
        self.user_rank_idx = _rank_idx(user_rank)
        self._user_balance = user_balance

        # Ownership state (mutated on purchase)
        self._owned_skins:   Set[str] = set(owned_skins)
        self._owned_titles:  Set[str] = set(owned_titles)
        self._owned_relics:  Set[str] = set(owned_relics)
        self._owned_badges:  Set[str] = set(owned_badges)
        self._eq_skin   = equipped_skin  or "default"
        self._eq_title  = equipped_title or "Unmarked"
        self._eq_relic  = equipped_relic or ""
        self._eq_badges: List[str] = list(equipped_badges)

        # Navigation
        self._mode     = self.MODE_HUB
        self._cat:     Optional[str] = None
        self._item_idx = 0

        # Result state
        self._result_ok   = False
        self._result_item = None
        self._result_msg  = ""
        self._result_cost = 0
        self._result_bal  = 0

        # Message reference for timeout editing
        self._message: Optional[discord.Message] = None

        self._rebuild()

    # ── Guard ─────────────────────────────────────────────────────────────────

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This session belongs to another soul.*\n"
                "*Open your own Exchange with `/market`.*",
                ephemeral=True,
            )
            return False
        return True

    # ── Item helpers ──────────────────────────────────────────────────────────

    def _items(self) -> list:
        return _cat_items(self._cat or "")

    def _current(self):
        items = self._items()
        if not items:
            return None
        return items[min(self._item_idx, len(items) - 1)]

    def _is_owned(self, item) -> bool:
        if self._cat == "skins":   return item.id in self._owned_skins or item.price_dc == 0
        if self._cat == "titles":  return item.id in self._owned_titles
        if self._cat == "relics":  return item.id in self._owned_relics
        if self._cat == "badges":  return item.id in self._owned_badges
        return False

    def _is_equipped(self, item) -> bool:
        if self._cat == "skins":   return item.id == self._eq_skin
        if self._cat == "titles":  return item.id == self._eq_title
        if self._cat == "relics":  return item.id == self._eq_relic
        if self._cat == "badges":  return item.id in self._eq_badges
        return False

    def _is_locked(self, item) -> bool:
        min_rank = getattr(item, "min_rank", "")
        if not min_rank:
            return False
        return self.user_rank_idx < _rank_idx(min_rank)

    def _can_afford(self, item) -> bool:
        return self._user_balance >= getattr(item, "price_dc", 0)

    def _can_acquire(self, item) -> bool:
        return not self._is_owned(item) and not self._is_locked(item)

    def _status_line(self, item) -> str:
        if self._is_equipped(item):
            return _status_equipped(self._cat or "")
        if self._is_owned(item):
            return "✔  BOUND TO YOUR SOUL"
        if self._is_locked(item):
            req = getattr(item, "min_rank", "?")
            return f"🔒  LOCKED — Requires **{req}**"
        if not self._can_afford(item):
            return f"💀  INSUFFICIENT FUNDS"
        return "⚔  AVAILABLE"

    # ── View rebuild ──────────────────────────────────────────────────────────

    def _rebuild(self):
        self.clear_items()
        if self._mode == self.MODE_HUB:
            self._build_hub()
        elif self._mode == self.MODE_CATEGORY:
            self._build_category()
        elif self._mode == self.MODE_PREVIEW:
            self._build_preview()
        elif self._mode == self.MODE_CONFIRM:
            self._build_confirm()
        elif self._mode == self.MODE_DONE:
            self._build_done()

    def _build_hub(self):
        cats = [
            ("🔮  Relics",  "relics",  discord.ButtonStyle.secondary),
            ("👑  Titles",  "titles",  discord.ButtonStyle.secondary),
            ("🎭  Skins",   "skins",   discord.ButtonStyle.secondary),
            ("🎖️  Badges", "badges",  discord.ButtonStyle.secondary),
        ]
        for label, cat, style in cats:
            btn = discord.ui.Button(label=label, style=style, row=0)
            btn.callback = self._hub_cb(cat)
            self.add_item(btn)

        leave = discord.ui.Button(
            label="🚪  Leave the Exchange",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        leave.callback = self._leave_cb
        self.add_item(leave)

    def _build_category(self):
        items = self._items()
        item  = self._current()
        n     = len(items)
        idx   = self._item_idx

        can_acquire = item is not None and self._can_acquire(item)
        can_afford  = item is not None and self._can_afford(item)
        can_buy     = can_acquire and can_afford

        # Row 0: navigation
        prev = discord.ui.Button(
            label    = "◀  Previous",
            style    = discord.ButtonStyle.secondary,
            row      = 0,
            disabled = (idx <= 0),
        )
        nxt = discord.ui.Button(
            label    = "Next  ▶",
            style    = discord.ButtonStyle.secondary,
            row      = 0,
            disabled = (idx >= n - 1),
        )
        prev.callback = self._prev_cb
        nxt.callback  = self._next_cb
        self.add_item(prev)
        self.add_item(nxt)

        # Row 1: actions
        offer = discord.ui.Button(
            label    = "🩸  Offer Blood",
            style    = discord.ButtonStyle.danger if can_buy else discord.ButtonStyle.secondary,
            row      = 1,
            disabled = not can_buy,
        )
        preview = discord.ui.Button(
            label  = "👁️  Manifestation",
            style  = discord.ButtonStyle.secondary,
            row    = 1,
        )
        back = discord.ui.Button(
            label  = "↩  The Exchange",
            style  = discord.ButtonStyle.secondary,
            row    = 1,
        )
        leave = discord.ui.Button(
            label  = "🚪  Leave",
            style  = discord.ButtonStyle.secondary,
            row    = 1,
        )
        offer.callback   = self._acquire_cb
        preview.callback = self._preview_cb
        back.callback    = self._back_to_hub_cb
        leave.callback   = self._leave_cb
        self.add_item(offer)
        self.add_item(preview)
        self.add_item(back)
        self.add_item(leave)

    def _build_preview(self):
        item       = self._current()
        can_buy    = item is not None and self._can_acquire(item) and self._can_afford(item)

        offer = discord.ui.Button(
            label    = "🩸  Offer Blood",
            style    = discord.ButtonStyle.danger if can_buy else discord.ButtonStyle.secondary,
            row      = 0,
            disabled = not can_buy,
        )
        back = discord.ui.Button(
            label  = "↩  Return",
            style  = discord.ButtonStyle.secondary,
            row    = 0,
        )
        offer.callback = self._acquire_cb
        back.callback  = self._back_to_cat_cb
        self.add_item(offer)
        self.add_item(back)

    def _build_confirm(self):
        item       = self._current()
        can_afford = item is not None and self._can_afford(item)

        seal = discord.ui.Button(
            label    = "🩸  Seal the Exchange",
            style    = discord.ButtonStyle.danger if can_afford else discord.ButtonStyle.secondary,
            row      = 0,
            disabled = not can_afford,
        )
        cancel = discord.ui.Button(
            label  = "✖  Withdraw",
            style  = discord.ButtonStyle.secondary,
            row    = 0,
        )
        seal.callback   = self._seal_cb
        cancel.callback = self._back_to_cat_cb
        self.add_item(seal)
        self.add_item(cancel)

    def _build_done(self):
        cont = discord.ui.Button(
            label  = "↩  Continue Browsing",
            style  = discord.ButtonStyle.secondary,
            row    = 0,
        )
        leave = discord.ui.Button(
            label  = "🚪  Leave the Exchange",
            style  = discord.ButtonStyle.secondary,
            row    = 0,
        )
        cont.callback  = self._continue_cb
        leave.callback = self._leave_cb
        self.add_item(cont)
        self.add_item(leave)

    # ── Embed builders ────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        if self._mode == self.MODE_HUB:
            return self._hub_embed()
        if self._mode == self.MODE_CATEGORY:
            return self._cat_embed()
        if self._mode == self.MODE_PREVIEW:
            return self._preview_embed()
        if self._mode == self.MODE_CONFIRM:
            return self._confirm_embed()
        if self._mode == self.MODE_DONE:
            return self._done_embed()
        return self._hub_embed()

    # ── Hub embed ─────────────────────────────────────────────────────────────

    def _hub_embed(self) -> discord.Embed:
        n_relics  = len(RELICS_CATALOG)
        n_titles  = sum(1 for t in TITLES_CATALOG.values() if t.price_dc > 0)
        n_skins   = sum(1 for s in SKINS.values() if s.price_dc > 0)
        n_badges  = len(BADGES_CATALOG)

        embed = discord.Embed(
            title = "🩸  Kingdom Exchange",
            description = (
                f"{_SEP}\n\n"
                "The doors creak open.\n\n"
                "You step into the Infernal Exchange.\n"
                "The air is thick.\n"
                "The fire burns low.\n\n"
                "Eyes turn toward you.\n"
                "Not welcoming. Not hostile.\n"
                "**Judging.**\n\n"
                "Power is not given.\n"
                "It is taken… and paid in full.\n\n"
                "*Choose carefully.*\n\n"
                f"{_SEP}"
            ),
            color = 0x1A0004,
        )
        embed.add_field(
            name  = "🔮  Relics",
            value = (
                "*Fragments of power.*\n"
                "*They alter what stands before others.*\n"
                f"`{n_relics} available`"
            ),
            inline = True,
        )
        embed.add_field(
            name  = "👑  Titles",
            value = (
                "*Names that cling to you.*\n"
                "*Some command fear.*\n"
                f"`{n_titles} available`"
            ),
            inline = True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name  = "🎭  Skins",
            value = (
                "*You are not what you were.*\n"
                "*Become what survives.*\n"
                f"`{n_skins} available`"
            ),
            inline = True,
        )
        embed.add_field(
            name  = "🎖️  Badges",
            value = (
                "*Marks of memory.*\n"
                "*Proof of endurance.*\n"
                f"`{n_badges} available`"
            ),
            inline = True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name  = _SEP,
            value = (
                f"**Your Treasury:** {self._user_balance:,} {_DC}\n"
                f"**Your Rank:** {self.user_rank}"
            ),
            inline = False,
        )
        if img := _IMG.get("hub"):
            embed.set_image(url=img)
        embed.set_footer(text=f"The Kingdom is watching.  ·  Kingdom of Hell")
        return embed

    # ── Category / item browse embed ──────────────────────────────────────────

    def _cat_embed(self) -> discord.Embed:
        item  = self._current()
        items = self._items()
        n     = len(items)
        idx   = self._item_idx

        if not item:
            return discord.Embed(
                description="*No items exist in this section.*",
                color=0x1A0004,
            )

        cat      = self._cat or ""
        icon     = _CAT_ICON.get(cat, "🛒")
        header   = _CAT_HEADER.get(cat, cat.upper())
        intro    = _CAT_INTRO.get(cat, "")
        rarity   = getattr(item, "rarity", "Unknown")
        sigil    = _RARITY_SIGIL.get(rarity, "◼")
        rar_lbl  = _RARITY_LABEL.get(rarity, rarity.upper())
        color    = _RARITY_COLOR.get(rarity, 0x1A0004)
        price_dc = getattr(item, "price_dc", 0)
        min_rank = getattr(item, "min_rank", "")
        status   = self._status_line(item)
        lore     = _item_lore(item)
        icon_str = getattr(item, "icon", "") if cat == "badges" else ""

        # Balance affordability display
        if self._user_balance >= price_dc:
            bal_display = f"**{self._user_balance:,}** {_DC}  ·  Cost: **{price_dc:,}** {_DC}"
        else:
            short = price_dc - self._user_balance
            bal_display = f"**{self._user_balance:,}** {_DC}  ·  *Need {short:,} more {_DC}*"

        item_name = f"{icon_str}  {item.name}" if icon_str else item.name

        embed = discord.Embed(
            title       = f"{icon}  {header}",
            description = f"{intro}\n\n{_SEP_SHORT}",
            color       = color,
        )

        embed.add_field(
            name  = f"{sigil}  {rar_lbl}",
            value = f"## {item_name}",
            inline = False,
        )
        embed.add_field(
            name  = "\u200b",
            value = f"*{item.description}*",
            inline = False,
        )
        if lore:
            embed.add_field(
                name  = "\u200b",
                value = f"*\"{lore}\"*",
                inline = False,
            )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(
            name  = "PRICE",
            value = f"**{price_dc:,}** {_DC}",
            inline = True,
        )
        embed.add_field(
            name  = "TYPE",
            value = f"**{header.rstrip('S').title() if header.endswith('S') else header.title()}**",
            inline = True,
        )
        embed.add_field(
            name  = "RARITY",
            value = f"**{rarity}**",
            inline = True,
        )
        embed.add_field(
            name  = "REQUIRED RANK",
            value = f"**{min_rank}**+" if min_rank else "**All Ranks**",
            inline = True,
        )
        embed.add_field(
            name  = "STATUS",
            value = status,
            inline = True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(
            name  = "YOUR TREASURY",
            value = bal_display,
            inline = False,
        )

        if img := _item_image(item, cat):
            embed.set_image(url=img)

        embed.set_footer(
            text=f"Item {idx + 1} of {n}  ·  {self.user_rank}  ·  Kingdom Treasury"
        )
        return embed

    # ── Preview / Manifestation embed ─────────────────────────────────────────

    def _preview_embed(self) -> discord.Embed:
        item = self._current()

        # Simulate equipped loadout with this item active
        preview_skin   = self._eq_skin
        preview_title  = self._eq_title
        preview_relic  = self._eq_relic
        preview_badges = list(self._eq_badges)

        if item:
            if self._cat == "skins":
                preview_skin  = item.id
            elif self._cat == "titles":
                preview_title = item.id
            elif self._cat == "relics":
                preview_relic = item.id
            elif self._cat == "badges" and item.id not in preview_badges:
                preview_badges.append(item.id)

        skin_obj   = SKINS.get(preview_skin, SKINS.get("default"))
        skin_name  = skin_obj.name if skin_obj else "Infernal Standard"
        title_name = preview_title or "Unmarked"
        relic_name = RELICS_CATALOG[preview_relic].name if preview_relic in RELICS_CATALOG else "None"

        badge_display = ""
        for bid in preview_badges[:3]:
            if bid in BADGES_CATALOG:
                badge_display += BADGES_CATALOG[bid].icon + "  "
        badge_display = badge_display.strip() or "None"

        effect_desc = ""
        if item:
            effect_desc = getattr(item, "effect_desc", item.description)

        lore = _item_lore(item) if item else ""
        item_name = item.name if item else "Unknown"

        embed = discord.Embed(
            title = "👁️  Manifestation",
            description = (
                f"{_SEP}\n\n"
                "*A dark presence gathers around your form.*\n\n"
                f"*This is not yet yours.*\n\n"
                "*But the Kingdom allows you to see*\n"
                f"*what you could become.*\n\n"
                f"{_SEP}"
            ),
            color = 0x1A0A2E,
        )
        embed.add_field(
            name  = f"If you claimed  **{item_name}**",
            value = f"*{effect_desc}*",
            inline = False,
        )
        if lore:
            embed.add_field(
                name  = "\u200b",
                value = f"*\"{lore}\"*",
                inline = False,
            )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(name="Skin",   value=f"**{skin_name}**",  inline=True)
        embed.add_field(name="Title",  value=f"**{title_name}**", inline=True)
        embed.add_field(name="Relic",  value=f"**{relic_name}**", inline=True)
        embed.add_field(name="Badges", value=badge_display,        inline=True)
        embed.add_field(
            name  = "\u200b",
            value = (
                f"\n*This is a simulation only.*\n"
                "*Use `/relics` to equip after purchase.*"
            ),
            inline = False,
        )
        if item and (img := _item_image(item, self._cat or "")):
            embed.set_image(url=img)
        embed.set_footer(text="Manifestation Preview  ·  Kingdom of Hell")
        return embed

    # ── Confirmation embed ─────────────────────────────────────────────────────

    def _confirm_embed(self) -> discord.Embed:
        item = self._current()
        if not item:
            return discord.Embed(description="*No item selected.*", color=0x1A0004)

        rarity    = getattr(item, "rarity", "Unknown")
        sigil     = _RARITY_SIGIL.get(rarity, "◼")
        color     = _RARITY_COLOR.get(rarity, 0x1A0004)
        price_dc  = getattr(item, "price_dc", 0)
        bal_after = self._user_balance - price_dc
        icon_str  = getattr(item, "icon", "") if self._cat == "badges" else ""
        item_name = f"{icon_str}  {item.name}" if icon_str else item.name
        lore      = _item_lore(item)

        embed = discord.Embed(
            title = "⚔  The Exchange Awaits Your Blood",
            description = (
                f"{_SEP}\n\n"
                "*The Kingdom awaits your offering.*\n\n"
                "*This transaction cannot be undone.*\n"
                "*The ledger is permanent.*\n\n"
                f"{_SEP}"
            ),
            color = color,
        )
        embed.add_field(
            name  = "ITEM",
            value = f"{sigil}  **{item_name}**  —  *{rarity}*",
            inline = False,
        )
        if lore:
            embed.add_field(
                name  = "\u200b",
                value = f"*\"{lore}\"*",
                inline = False,
            )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(
            name  = "COST",
            value = f"**{price_dc:,}** {_DC}",
            inline = True,
        )
        embed.add_field(
            name  = "YOUR TREASURY",
            value = f"**{self._user_balance:,}** {_DC}",
            inline = True,
        )
        embed.add_field(
            name  = "BALANCE AFTER",
            value = (
                f"**{bal_after:,}** {_DC}"
                if bal_after >= 0
                else "*Insufficient funds — this will be denied*"
            ),
            inline = True,
        )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(
            name  = "\u200b",
            value = "*Seal the Exchange to complete your offering.\nWithdraw to reconsider.*",
            inline = False,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ── Done / result embed ───────────────────────────────────────────────────

    def _done_embed(self) -> discord.Embed:
        if self._result_ok and self._result_item:
            item   = self._result_item
            rarity = getattr(item, "rarity", "Unknown")
            color  = _RARITY_COLOR.get(rarity, 0x1A0004)
            sigil  = _RARITY_SIGIL.get(rarity, "◼")
            icon_s = getattr(item, "icon", "") if self._cat == "badges" else ""
            lore   = _item_lore(item)
            effect = getattr(item, "effect_desc", item.description)

            embed = discord.Embed(
                title = "🩸  Transaction Accepted",
                description = (
                    f"{_SEP}\n\n"
                    "*The Kingdom has taken your offering.*\n\n"
                    "*It does not thank you.*\n"
                    "*It remembers.*\n\n"
                    f"{_SEP}"
                ),
                color = color,
            )
            embed.add_field(
                name  = "You have claimed:",
                value = (
                    f"{sigil}  **{icon_s + '  ' if icon_s else ''}{item.name}**\n"
                    f"*{effect}*"
                ),
                inline = False,
            )
            if lore:
                embed.add_field(
                    name  = "\u200b",
                    value = f"*\"{lore}\"*",
                    inline = False,
                )
            embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
            embed.add_field(
                name  = "COST",
                value = f"**{self._result_cost:,}** {_DC}",
                inline = True,
            )
            embed.add_field(
                name  = "REMAINING TREASURY",
                value = f"**{self._result_bal:,}** {_DC}",
                inline = True,
            )
            embed.add_field(
                name  = "RARITY",
                value = f"**{rarity}**",
                inline = True,
            )
            embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
            embed.add_field(
                name  = "\u200b",
                value = "*You are marked.*\n*Use `/relics` to equip your acquisition.*",
                inline = False,
            )
            if img := _IMG.get("acquire"):
                embed.set_image(url=img)
        else:
            embed = discord.Embed(
                title = "🩸  The Exchange Refused",
                description = (
                    f"{_SEP}\n\n"
                    f"*{self._result_msg or 'The Kingdom refuses this transaction.'}*\n\n"
                    "*Return when your offering is sufficient.*\n\n"
                    f"{_SEP}"
                ),
                color = 0x0A0A0A,
            )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _hub_cb(self, cat: str):
        async def cb(interaction: discord.Interaction):
            if not await self._guard(interaction):
                return
            self._cat      = cat
            self._item_idx = 0
            self._mode     = self.MODE_CATEGORY
            self._rebuild()
            await interaction.response.edit_message(
                embed=self.build_embed(), view=self
            )
        return cb

    async def _prev_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._item_idx = max(0, self._item_idx - 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        items = self._items()
        self._item_idx = min(len(items) - 1, self._item_idx + 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back_to_hub_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode = self.MODE_HUB
        self._cat  = None
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back_to_cat_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode = self.MODE_CATEGORY
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _preview_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode = self.MODE_PREVIEW
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _acquire_cb(self, interaction: discord.Interaction):
        """Route to confirmation screen."""
        if not await self._guard(interaction):
            return
        item = self._current()
        if not item or not self._can_acquire(item):
            await interaction.response.send_message(
                "*This item cannot be acquired.*", ephemeral=True
            )
            return
        self._mode = self.MODE_CONFIRM
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _continue_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode        = self.MODE_CATEGORY
        self._result_ok   = False
        self._result_item = None
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _leave_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        farewell = discord.Embed(
            description = (
                f"{_SEP}\n\n"
                "*The gates close behind you.*\n\n"
                "*No transaction is forgotten.*\n"
                "*No mark is erased.*\n\n"
                "*Return…*\n"
                "*when you have more to offer.*\n\n"
                f"{_SEP}"
            ),
            color = 0x0A0A0A,
        )
        if img := _IMG.get("exit"):
            farewell.set_image(url=img)
        farewell.set_footer(text="The Kingdom remembers.  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=farewell, view=None)
        self.stop()

    # ── Seal — execute purchase ────────────────────────────────────────────────

    async def _seal_cb(self, interaction: discord.Interaction):
        """Confirm and execute the purchase. Defers + edits after async work."""
        if not await self._guard(interaction):
            return

        item = self._current()
        if not item or not self._can_acquire(item):
            await interaction.response.send_message(
                "*This item is not available for acquisition.*", ephemeral=True
            )
            return

        # Immediately acknowledge — show sealing ritual
        sealing = discord.Embed(
            title = "🩸  Sealing the Exchange…",
            description = (
                f"{_SEP}\n\n"
                "*The Exchange accepts your offering.*\n\n"
                "*The mark is being carved.*\n"
                "*The ledger prepares to remember.*\n\n"
                "*This cannot be interrupted.*\n\n"
                f"{_SEP}"
            ),
            color = 0x1A0004,
        )
        if img := _IMG.get("seal"):
            sealing.set_image(url=img)
        sealing.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

        msg_id = interaction.message.id
        await interaction.response.edit_message(embed=sealing, view=None)

        # Atmospheric pause — the ritual has weight
        await asyncio.sleep(1.5)

        # Execute purchase
        try:
            user_data = await self.bot.db.get_user(self.guild_id, self.discord_id)
            if user_data and user_data.get("sacrifice_active"):
                raise ValueError(
                    "Access denied. Your debt bars you from the market. Settle it first."
                )

            svc = self.bot.cosmetic_service

            if self._cat == "skins":
                result = await svc.buy_skin(self.guild_id, self.discord_id, item.id)
                self._owned_skins.add(item.id)
            elif self._cat == "titles":
                result = await svc.buy_title(self.guild_id, self.discord_id, item.id)
                self._owned_titles.add(item.id)
            elif self._cat == "relics":
                result = await svc.buy_relic(self.guild_id, self.discord_id, item.id)
                self._owned_relics.add(item.id)
            elif self._cat == "badges":
                result = await svc.buy_badge(self.guild_id, self.discord_id, item.id)
                self._owned_badges.add(item.id)
            else:
                raise ValueError("Unknown item category.")

            cost    = result.get("cost", 0)
            new_bal = result.get("new_balance", 0)
            self._user_balance = new_bal

            # Ledger — if money moved, the Treasury must see it
            ledger = getattr(self.bot, "ledger_service", None)
            if ledger and cost > 0:
                try:
                    await ledger.log(
                        action          = "market_purchase",
                        amount          = cost,
                        from_label      = f"<@{self.discord_id}>",
                        to_label        = f"Kingdom Market — {item.name}",
                        guild_id        = self.guild_id,
                        from_discord_id = self.discord_id,
                        wallet_before   = new_bal + cost,
                        wallet_after    = new_bal,
                        action_type     = "market",
                    )
                except Exception:
                    pass

            self._result_ok   = True
            self._result_item = item
            self._result_cost = cost
            self._result_bal  = new_bal

        except ValueError as e:
            self._result_ok  = False
            self._result_msg = str(e)
        except Exception:
            log.exception("Market purchase error")
            self._result_ok  = False
            self._result_msg = "An internal error occurred. Please try again."

        # Rebuild to done state
        self._mode = self.MODE_DONE
        self._rebuild()

        try:
            await interaction.followup.edit_message(
                msg_id,
                embed = self.build_embed(),
                view  = self,
            )
        except Exception:
            try:
                await interaction.message.edit(embed=self.build_embed(), view=self)
            except Exception:
                log.exception("Failed to edit market message after purchase")

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self):
        """Disable all buttons and show expired state."""
        for child in self.children:
            child.disabled = True

        expired = discord.Embed(
            description = (
                f"{_SEP}\n\n"
                "*The Exchange has gone still.*\n\n"
                "*The fire has died.*\n"
                "*The doors are no longer open.*\n\n"
                "*Open `/market` again to return.*\n\n"
                f"{_SEP}"
            ),
            color = 0x0A0A0A,
        )
        expired.set_footer(text="Session expired  ·  Kingdom of Hell")

        try:
            if self._message:
                await self._message.edit(embed=expired, view=self)
        except Exception:
            pass
