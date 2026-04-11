"""
Kingdom Treasury — Infernal Inventory
The personal vault of a soul.

Flow:
  /inventory → hub → category → item browse → equip / unequip
  /inventory → hub → equipped → change slot → category

Every transition edits the same ephemeral message in-place.
Equip actions fire immediately — no separate confirmation screen.
"""

from __future__ import annotations

import json
import logging
import random
from typing import Dict, List, Optional, Set

import discord

from ..utils.skins import (
    SKINS, TITLES_CATALOG, RELICS_CATALOG, BADGES_CATALOG,
    DEFAULT_SKIN_ID, DEFAULT_TITLE,
)

log = logging.getLogger("kingdom_treasury")

# ─── Decorators ───────────────────────────────────────────────────────────────

_SEP       = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
_SEP_SHORT = "──────────────────────────"

# ─── Image registry (verified Wikimedia Commons CDN) ─────────────────────────

_CDN = "https://upload.wikimedia.org/wikipedia/commons/"

_IMG: Dict[str, Optional[str]] = {
    "hub":      _CDN + "6/65/John_Martin_-_Pandemonium_-_WGA14149.jpg",
    "equipped": _CDN + "6/65/John_Martin_-_Pandemonium_-_WGA14149.jpg",
    "relics":   _CDN + "5/50/John_Martin_-_The_Great_Day_of_His_Wrath_-_Google_Art_Project.jpg",
    "titles":   _CDN + "e/ec/John_Martin_-_Belshazzar%27s_Feast_-_Google_Art_Project.jpg",
    "skins":    _CDN + "e/e1/John_Martin_-_Sodom_and_Gomorrah.jpg",
    "badges":   _CDN + "6/6f/John_Martin_-_Ruins_of_an_Ancient_City_-_Cleveland_Art_Museum.jpg",
    "preview":  _CDN + "7/79/John_Martin_-_The_Plains_of_Heaven_-_Google_Art_Project.jpg",
    "exit":     _CDN + "7/79/John_Martin_-_The_Plains_of_Heaven_-_Google_Art_Project.jpg",
}

# ─── Rarity colours ───────────────────────────────────────────────────────────

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

# ─── Category metadata ────────────────────────────────────────────────────────

_CAT_ICON: Dict[str, str] = {
    "relics": "🔮",
    "titles": "👑",
    "skins":  "🎭",
    "badges": "🏅",
}

_CAT_INTRO: Dict[str, str] = {
    "relics": (
        "*Relics are not tools.*\n\n"
        "*They are fragments of something that should not exist.*\n\n"
        "*They do not serve you.*\n"
        "*They attach themselves to you.*\n\n"
        "*They whisper.*\n"
        "*They alter.*\n"
        "*They remain.*"
    ),
    "titles": (
        "*A title is not a name.*\n\n"
        "*It is a mark.*\n"
        "*A declaration.*\n\n"
        "*A memory others are forced to carry*\n"
        "*when they see you.*"
    ),
    "skins": (
        "*You were something once.*\n\n"
        "*That version is gone.*\n\n"
        "*A skin is not appearance.*\n\n"
        "*It is identity rewritten.*"
    ),
    "badges": (
        "*Badges are not rewards.*\n\n"
        "*They are proof.*\n\n"
        "*Proof that you endured.*\n"
        "*Proof that you remained.*"
    ),
}

# ─── Equip / Unequip atmosphere lines ────────────────────────────────────────

_EQUIP_LINES = [
    "*The mark settles.*\n*Something shifts.*\n*The Kingdom sees you differently now.*",
    "*It takes hold.*\n*The Abyss adjusts.*\n*You are no longer what you were.*",
    "*The power binds.*\n*Your form changes.*\n*The Kingdom has noted the change.*",
    "*Sealed.*\n*The ledger updates.*\n*What you are is now recorded.*",
]

_UNEQUIP_LINES = [
    "*The presence fades.*\n*But it does not disappear.*\n*It waits.*",
    "*The mark recedes.*\n*The Kingdom allows it.*\n*For now.*",
    "*Released.*\n*It remains in your vault.*\n*Dormant. Patient.*",
]

def _equip_line() -> str:
    return random.choice(_EQUIP_LINES)

def _unequip_line() -> str:
    return random.choice(_UNEQUIP_LINES)

# ─── Item key helper (Title has no .id; uses .name as DB key) ─────────────────

def _item_key(item) -> str:
    return getattr(item, "id", None) or getattr(item, "name", "")

# ─── Owned-items resolver ──────────────────────────────────────────────────────

def _resolve_owned(cat: str, owned_ids: Set[str]) -> list:
    """Return owned item objects for a category, sorted by price ascending."""
    if cat == "relics":
        pool = RELICS_CATALOG
    elif cat == "titles":
        pool = TITLES_CATALOG
    elif cat == "skins":
        pool = SKINS
    elif cat == "badges":
        pool = BADGES_CATALOG
    else:
        return []
    return sorted(
        [v for k, v in pool.items() if k in owned_ids],
        key=lambda x: x.price_dc,
    )

# ─── Main View ────────────────────────────────────────────────────────────────

class InfernalInventoryView(discord.ui.View):
    """
    Ephemeral inventory panel.
    Modes: hub → cat → (browse owned items → equip/unequip)
                   ↳ equipped (current loadout overview)
    All state lives here; every button edits the same message in-place.
    """

    MODE_HUB      = "hub"
    MODE_CAT      = "cat"
    MODE_EQUIPPED = "equipped"
    MODE_PREVIEW  = "preview"

    def __init__(
        self,
        *,
        owner_id:        int,
        bot,
        guild_id:        str,
        discord_id:      str,
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
        self.owner_id   = owner_id
        self.bot        = bot
        self.guild_id   = guild_id
        self.discord_id = discord_id

        # Ownership state (mutated on equip; items are never added here — /market handles purchase)
        self._owned_skins:   Set[str] = set(owned_skins)
        self._owned_titles:  Set[str] = set(owned_titles)
        self._owned_relics:  Set[str] = set(owned_relics)
        self._owned_badges:  Set[str] = set(owned_badges)

        # Equipped state
        self._eq_skin   = equipped_skin  or DEFAULT_SKIN_ID
        self._eq_title  = equipped_title or DEFAULT_TITLE
        self._eq_relic  = equipped_relic or ""
        self._eq_badges: List[str] = list(equipped_badges)

        # Navigation
        self._mode     = self.MODE_HUB
        self._cat:     Optional[str] = None
        self._item_idx = 0

        # Flash message shown briefly after equip/unequip (displayed once, then cleared)
        self._flash:   Optional[str] = None

        # Message ref for timeout editing
        self._message: Optional[discord.Message] = None

        self._rebuild()

    # ── Guard ─────────────────────────────────────────────────────────────────

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This vault belongs to another soul.*", ephemeral=True
            )
            return False
        return True

    # ── Owned item helpers ────────────────────────────────────────────────────

    def _owned_for(self, cat: str) -> list:
        if cat == "relics":  return _resolve_owned("relics", self._owned_relics)
        if cat == "titles":  return _resolve_owned("titles", self._owned_titles)
        if cat == "skins":   return _resolve_owned("skins",  self._owned_skins)
        if cat == "badges":  return _resolve_owned("badges", self._owned_badges)
        return []

    def _current_item(self):
        items = self._owned_for(self._cat or "")
        if not items:
            return None
        return items[min(self._item_idx, len(items) - 1)]

    def _is_equipped(self, item) -> bool:
        if item is None:
            return False
        key = _item_key(item)
        if self._cat == "skins":   return key == self._eq_skin
        if self._cat == "titles":  return key == self._eq_title
        if self._cat == "relics":  return key == self._eq_relic
        if self._cat == "badges":  return key in self._eq_badges
        return False

    def _status_text(self, item) -> str:
        if self._is_equipped(item):
            if self._cat == "relics":  return "✔  Active on your identity"
            if self._cat == "titles":  return "✔  Active on your identity"
            if self._cat == "skins":   return "✔  Active on your identity"
            if self._cat == "badges":  return "✔  Active on your identity"
        return "🩸  Bound to your soul  —  Dormant"

    # ── View rebuild ──────────────────────────────────────────────────────────

    def _rebuild(self):
        self.clear_items()
        if self._mode == self.MODE_HUB:
            self._build_hub()
        elif self._mode == self.MODE_CAT:
            self._build_cat()
        elif self._mode == self.MODE_EQUIPPED:
            self._build_equipped()
        elif self._mode == self.MODE_PREVIEW:
            self._build_preview()

    def _build_hub(self):
        # Row 0: category buttons
        for label, cat in [
            ("🔮  Relics",  "relics"),
            ("👑  Titles",  "titles"),
            ("🎭  Skins",   "skins"),
            ("🏅  Badges",  "badges"),
        ]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, row=0)
            btn.callback = self._cat_cb(cat)
            self.add_item(btn)

        # Row 1: equipped overview + leave
        eq_btn = discord.ui.Button(
            label="👁  Equipped",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        eq_btn.callback = self._equipped_cb
        self.add_item(eq_btn)

        leave_btn = discord.ui.Button(
            label="🚪  Leave",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        leave_btn.callback = self._leave_cb
        self.add_item(leave_btn)

    def _build_cat(self):
        items = self._owned_for(self._cat or "")
        item  = self._current_item()
        n     = len(items)
        idx   = self._item_idx

        # Row 0: navigation (only shown if > 1 item)
        prev_btn = discord.ui.Button(
            label    = "◀  Previous",
            style    = discord.ButtonStyle.secondary,
            row      = 0,
            disabled = (idx <= 0 or n <= 1),
        )
        next_btn = discord.ui.Button(
            label    = "Next  ▶",
            style    = discord.ButtonStyle.secondary,
            row      = 0,
            disabled = (idx >= n - 1 or n <= 1),
        )
        prev_btn.callback = self._prev_cb
        next_btn.callback = self._next_cb
        self.add_item(prev_btn)
        self.add_item(next_btn)

        # Row 1: equip/unequip + preview
        equipped = self._is_equipped(item)

        equip_btn = discord.ui.Button(
            label    = "✦  Equip" if not equipped else "✦  Equipped",
            style    = discord.ButtonStyle.danger if not equipped else discord.ButtonStyle.secondary,
            row      = 1,
            disabled = item is None or equipped,
        )
        equip_btn.callback = self._equip_cb

        unequip_btn = discord.ui.Button(
            label    = "✖  Remove Mark",
            style    = discord.ButtonStyle.secondary,
            row      = 1,
            disabled = item is None or not equipped,
        )
        unequip_btn.callback = self._unequip_cb

        preview_btn = discord.ui.Button(
            label    = "👁  Preview",
            style    = discord.ButtonStyle.secondary,
            row      = 1,
            disabled = item is None,
        )
        preview_btn.callback = self._preview_cb

        self.add_item(equip_btn)
        self.add_item(unequip_btn)
        self.add_item(preview_btn)

        # Row 2: navigation
        back_btn = discord.ui.Button(
            label  = "↩  The Vault",
            style  = discord.ButtonStyle.secondary,
            row    = 2,
        )
        leave_btn = discord.ui.Button(
            label  = "🚪  Leave",
            style  = discord.ButtonStyle.secondary,
            row    = 2,
        )
        back_btn.callback  = self._back_to_hub_cb
        leave_btn.callback = self._leave_cb
        self.add_item(back_btn)
        self.add_item(leave_btn)

    def _build_equipped(self):
        # Row 0: change relic / change title
        change_relic = discord.ui.Button(label="🔮  Change Relic", style=discord.ButtonStyle.secondary, row=0)
        change_title = discord.ui.Button(label="👑  Change Title", style=discord.ButtonStyle.secondary, row=0)
        change_relic.callback = self._cat_cb("relics")
        change_title.callback = self._cat_cb("titles")
        self.add_item(change_relic)
        self.add_item(change_title)

        # Row 1: change skin / change badges
        change_skin   = discord.ui.Button(label="🎭  Change Skin",   style=discord.ButtonStyle.secondary, row=1)
        change_badges = discord.ui.Button(label="🏅  Change Badges", style=discord.ButtonStyle.secondary, row=1)
        change_skin.callback   = self._cat_cb("skins")
        change_badges.callback = self._cat_cb("badges")
        self.add_item(change_skin)
        self.add_item(change_badges)

        # Row 2: back
        back_btn = discord.ui.Button(label="↩  The Vault", style=discord.ButtonStyle.secondary, row=2)
        back_btn.callback = self._back_to_hub_cb
        self.add_item(back_btn)

    def _build_preview(self):
        back_btn = discord.ui.Button(label="↩  Return", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self._back_to_cat_cb
        self.add_item(back_btn)

    # ── Embed builders ────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        if self._mode == self.MODE_HUB:
            return self._hub_embed()
        if self._mode == self.MODE_CAT:
            return self._cat_embed()
        if self._mode == self.MODE_EQUIPPED:
            return self._equipped_embed()
        if self._mode == self.MODE_PREVIEW:
            return self._preview_embed()
        return self._hub_embed()

    # Hub embed ----------------------------------------------------------------

    def _hub_embed(self) -> discord.Embed:
        n_relics = len(self._owned_relics)
        n_titles = len(self._owned_titles)
        n_skins  = len(self._owned_skins)
        n_badges = len(self._owned_badges)

        embed = discord.Embed(
            title = "🩸  INFERNAL INVENTORY",
            description = (
                f"{_SEP}\n\n"
                "The gates do not open for everyone.\n\n"
                "But they opened for **you**.\n\n"
                "*Everything you claimed…*\n"
                "*Everything you took…*\n\n"
                "*It is here.*\n\n"
                "*Waiting.*\n"
                "*Watching.*\n"
                "*Bound to your existence.*\n\n"
                "Relics.  Titles.  Forms.  Marks.\n\n"
                "*This is not what you own.*\n\n"
                "**This is what you have become.**\n\n"
                f"{_SEP}"
            ),
            color = 0x1A0004,
        )
        embed.add_field(
            name  = "🔮  Relics",
            value = f"`{n_relics} bound`" if n_relics else "*None claimed*",
            inline = True,
        )
        embed.add_field(
            name  = "👑  Titles",
            value = f"`{n_titles} held`" if n_titles else "*None claimed*",
            inline = True,
        )
        embed.add_field(
            name  = "🎭  Skins",
            value = f"`{n_skins} worn`" if n_skins else "*None claimed*",
            inline = True,
        )
        embed.add_field(
            name  = "🏅  Badges",
            value = f"`{n_badges} marked`" if n_badges else "*None claimed*",
            inline = True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        if img := _IMG.get("hub"):
            embed.set_image(url=img)
        embed.set_footer(text="The Kingdom sees everything.  ·  Kingdom of Hell")
        return embed

    # Category browse embed ----------------------------------------------------

    def _cat_embed(self) -> discord.Embed:
        cat   = self._cat or ""
        icon  = _CAT_ICON.get(cat, "📦")
        intro = _CAT_INTRO.get(cat, "")
        items = self._owned_for(cat)
        item  = self._current_item()
        n     = len(items)
        idx   = self._item_idx

        # Flash message (shown once after equip/unequip)
        flash      = self._flash
        self._flash = None

        if not items:
            embed = discord.Embed(
                title       = f"{icon}  {cat.upper()}",
                description = (
                    f"{intro}\n\n{_SEP_SHORT}\n\n"
                    "*You own nothing in this chamber.*\n\n"
                    "*Visit the Exchange to claim power.*"
                ),
                color = 0x1A0004,
            )
            if img := _IMG.get(cat):
                embed.set_image(url=img)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        rarity  = getattr(item, "rarity", "Unknown")
        sigil   = _RARITY_SIGIL.get(rarity, "◼")
        color   = _RARITY_COLOR.get(rarity, 0x1A0004)
        icon_s  = getattr(item, "icon", "") if cat == "badges" else ""
        name_s  = f"{icon_s}  {item.name}" if icon_s else item.name
        status  = self._status_text(item)

        # Badge: show how many of 3 slots are active
        if cat == "badges":
            badge_key  = _item_key(item)
            badge_slot = (
                f"Badge **{self._eq_badges.index(badge_key) + 1}** of 3 active"
                if badge_key in self._eq_badges
                else f"{len(self._eq_badges)}/3 badge slots used"
            )
            status = f"✔  ACTIVE — {badge_slot}" if badge_key in self._eq_badges else f"🩸  DORMANT — {badge_slot}"

        embed = discord.Embed(
            title       = f"{icon}  {cat.upper()}",
            description = f"{intro}\n\n{_SEP_SHORT}",
            color       = color,
        )

        embed.add_field(
            name  = f"{sigil}  {rarity.upper()}",
            value = f"## {name_s}",
            inline = False,
        )
        embed.add_field(
            name  = "\u200b",
            value = f"*{item.description}*",
            inline = False,
        )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(name="STATUS", value=status, inline=True)
        embed.add_field(
            name  = "ITEM",
            value = f"{idx + 1} / {n}",
            inline = True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Flash message (equip/unequip confirmation)
        if flash:
            embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
            embed.add_field(name="\u200b", value=flash, inline=False)

        if img := _IMG.get(cat):
            embed.set_image(url=img)
        embed.set_footer(text=f"Item {idx + 1} of {n}  ·  Kingdom of Hell")
        return embed

    # Equipped overview embed --------------------------------------------------

    def _equipped_embed(self) -> discord.Embed:
        # Relic
        relic_obj  = RELICS_CATALOG.get(self._eq_relic)
        relic_name = relic_obj.name if relic_obj else "None"

        # Title
        title_name = self._eq_title or DEFAULT_TITLE

        # Skin
        skin_obj   = SKINS.get(self._eq_skin, SKINS.get(DEFAULT_SKIN_ID))
        skin_name  = skin_obj.name if skin_obj else "Infernal Standard"

        # Badges
        badge_icons = ""
        for bid in self._eq_badges[:3]:
            bd = BADGES_CATALOG.get(bid)
            if bd:
                badge_icons += f"{bd.icon}  {bd.name}\n"
        badge_display = badge_icons.strip() or "*None*"

        color = skin_obj.color if skin_obj else 0x1A0004

        embed = discord.Embed(
            title = "👁  CURRENT FORM",
            description = (
                f"{_SEP}\n\n"
                "*This is what the Kingdom sees when it looks at you.*\n\n"
                "*Not what you were.*\n"
                "*Not what you claim to be.*\n\n"
                "**What you are.**\n\n"
                "**Now.**\n\n"
                f"{_SEP}"
            ),
            color = color,
        )
        embed.add_field(name="🔮  Active Relic",  value=f"**{relic_name}**",  inline=True)
        embed.add_field(name="👑  Active Title",  value=f"**{title_name}**",  inline=True)
        embed.add_field(name="🎭  Active Skin",   value=f"**{skin_name}**",   inline=True)
        embed.add_field(name="🏅  Active Badges", value=badge_display,         inline=False)
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(
            name  = "\u200b",
            value = "*Use the buttons below to change your equipped form.*",
            inline = False,
        )
        if img := _IMG.get("equipped"):
            embed.set_image(url=img)
        embed.set_footer(text="Current Loadout  ·  Kingdom of Hell")
        return embed

    # Preview embed ------------------------------------------------------------

    def _preview_embed(self) -> discord.Embed:
        item = self._current_item()
        cat  = self._cat or ""

        # Simulate the equipped loadout with this item active
        p_skin   = self._eq_skin
        p_title  = self._eq_title
        p_relic  = self._eq_relic
        p_badges = list(self._eq_badges)

        if item:
            key = _item_key(item)
            if cat == "skins":   p_skin  = key
            elif cat == "titles": p_title = key
            elif cat == "relics": p_relic = key
            elif cat == "badges" and key not in p_badges:
                p_badges.append(key)

        skin_obj   = SKINS.get(p_skin, SKINS.get(DEFAULT_SKIN_ID))
        skin_name  = skin_obj.name if skin_obj else "Infernal Standard"
        relic_obj  = RELICS_CATALOG.get(p_relic)
        relic_name = relic_obj.name if relic_obj else "None"
        badge_icons = ""
        for bid in p_badges[:3]:
            bd = BADGES_CATALOG.get(bid)
            if bd:
                badge_icons += bd.icon + "  "
        badge_display = badge_icons.strip() or "None"

        item_name = item.name if item else "Unknown"
        effect    = getattr(item, "effect_desc", None) or (item.description if item else "")

        embed = discord.Embed(
            title = "👁  MANIFESTATION",
            description = (
                f"{_SEP}\n\n"
                "*You are not meant to see this.*\n\n"
                "*And yet…*\n\n"
                "*The Kingdom allows it.*\n*For a moment.*\n\n"
                "**Observe what you could become.**\n\n"
                f"{_SEP}"
            ),
            color = 0x1A0A2E,
        )
        embed.add_field(
            name  = f"If you equipped  **{item_name}**",
            value = f"*{effect}*",
            inline = False,
        )
        embed.add_field(name="\u200b", value=_SEP_SHORT, inline=False)
        embed.add_field(name="Skin",   value=f"**{skin_name}**",  inline=True)
        embed.add_field(name="Title",  value=f"**{p_title}**",    inline=True)
        embed.add_field(name="Relic",  value=f"**{relic_name}**", inline=True)
        embed.add_field(name="Badges", value=badge_display,         inline=True)
        if img := _IMG.get("preview"):
            embed.set_image(url=img)
        embed.set_footer(text="Manifestation Preview  ·  Kingdom of Hell")
        return embed

    # ── Safe-edit helper ──────────────────────────────────────────────────────

    async def _safe_edit(self, interaction: discord.Interaction):
        """Rebuild view + embed and edit message. Always acknowledges interaction."""
        try:
            self._rebuild()
            await interaction.response.edit_message(
                embed=self.build_embed(), view=self
            )
        except Exception:
            log.exception("Inventory view error [mode=%s cat=%s]", self._mode, self._cat)
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    "*An internal error occurred. Please try `/inventory` again.*",
                    ephemeral=True,
                )
            except Exception:
                pass

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cat_cb(self, cat: str):
        async def cb(interaction: discord.Interaction):
            if not await self._guard(interaction):
                return
            self._cat      = cat
            self._item_idx = 0
            self._mode     = self.MODE_CAT
            self._flash    = None
            await self._safe_edit(interaction)
        return cb

    async def _prev_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._item_idx = max(0, self._item_idx - 1)
        self._flash    = None
        await self._safe_edit(interaction)

    async def _next_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        items = self._owned_for(self._cat or "")
        self._item_idx = min(len(items) - 1, self._item_idx + 1)
        self._flash    = None
        await self._safe_edit(interaction)

    async def _back_to_hub_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode  = self.MODE_HUB
        self._cat   = None
        self._flash = None
        await self._safe_edit(interaction)

    async def _back_to_cat_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode  = self.MODE_CAT
        self._flash = None
        await self._safe_edit(interaction)

    async def _equipped_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode  = self.MODE_EQUIPPED
        self._flash = None
        await self._safe_edit(interaction)

    async def _preview_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self._mode  = self.MODE_PREVIEW
        self._flash = None
        await self._safe_edit(interaction)

    async def _leave_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        farewell = discord.Embed(
            description = (
                f"{_SEP}\n\n"
                "*The vault seals behind you.*\n\n"
                "*What you carry is yours.*\n"
                "*What you have become…*\n"
                "*remains.*\n\n"
                f"{_SEP}"
            ),
            color = 0x0A0A0A,
        )
        if img := _IMG.get("exit"):
            farewell.set_image(url=img)
        farewell.set_footer(text="The Kingdom remembers.  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=farewell, view=None)
        self.stop()

    # ── Equip ─────────────────────────────────────────────────────────────────

    async def _equip_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        item = self._current_item()
        if not item:
            await interaction.response.defer()
            return

        cat    = self._cat or ""
        key    = _item_key(item)
        svc    = self.bot.cosmetic_service

        try:
            if cat == "skins":
                await svc.equip_skin(self.guild_id, self.discord_id, key)
                self._eq_skin  = key

            elif cat == "titles":
                await svc.equip_title(self.guild_id, self.discord_id, key)
                self._eq_title = key

            elif cat == "relics":
                await svc.equip_relic(self.guild_id, self.discord_id, key)
                self._eq_relic = key

            elif cat == "badges":
                if key in self._eq_badges:
                    # Already active
                    self._flash = "*This mark is already active.*"
                elif len(self._eq_badges) >= 3:
                    # Too many
                    self._flash = (
                        "*You carry too many marks.*\n"
                        "*Choose which one fades.*\n"
                        "*(Unequip a badge first.)*"
                    )
                    await self._safe_edit(interaction)
                    return
                else:
                    self._eq_badges.append(key)
                    await self.bot.db.set_equipped_badges(
                        self.guild_id, self.discord_id, json.dumps(self._eq_badges)
                    )

            if self._flash is None:
                self._flash = _equip_line()

        except ValueError as e:
            self._flash = f"*{e}*"
        except Exception:
            log.exception("Inventory equip error [cat=%s key=%s]", cat, key)
            self._flash = "*An error occurred. Please try again.*"

        await self._safe_edit(interaction)

    # ── Unequip ───────────────────────────────────────────────────────────────

    async def _unequip_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        item = self._current_item()
        if not item:
            await interaction.response.defer()
            return

        cat = self._cat or ""
        key = _item_key(item)
        svc = self.bot.cosmetic_service

        try:
            if cat == "skins":
                await svc.equip_skin(self.guild_id, self.discord_id, DEFAULT_SKIN_ID)
                self._eq_skin = DEFAULT_SKIN_ID

            elif cat == "titles":
                await svc.equip_title(self.guild_id, self.discord_id, DEFAULT_TITLE)
                self._eq_title = DEFAULT_TITLE

            elif cat == "relics":
                await svc.unequip_relic(self.guild_id, self.discord_id)
                self._eq_relic = ""

            elif cat == "badges":
                if key in self._eq_badges:
                    self._eq_badges.remove(key)
                    await self.bot.db.set_equipped_badges(
                        self.guild_id, self.discord_id, json.dumps(self._eq_badges)
                    )

            self._flash = _unequip_line()

        except ValueError as e:
            self._flash = f"*{e}*"
        except Exception:
            log.exception("Inventory unequip error [cat=%s key=%s]", cat, key)
            self._flash = "*An error occurred. Please try again.*"

        await self._safe_edit(interaction)

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        expired = discord.Embed(
            description = (
                f"{_SEP}\n\n"
                "*The vault has gone still.*\n\n"
                "*Open `/inventory` again to return.*\n\n"
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
