"""
Kingdom Treasury — Infernal Market Hub
Single-message AAA shop: hub → category browse → acquire → preview.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

import discord

from ..utils.skins import (
    SKINS, TITLES_CATALOG, RELICS_CATALOG, BADGES_CATALOG,
    rank_idx as _rank_idx,
)

log = logging.getLogger("kingdom_treasury")

_DC  = "<:devilcoinStack:1492184333392412692>"
_SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── Rarity cosmetics ─────────────────────────────────────────────────────────

_RARITY_COLOR: Dict[str, int] = {
    "Default":   0x1A1A1A,
    "Common":    0x444444,
    "Uncommon":  0x1A5C1A,
    "Rare":      0x0D3D80,
    "Epic":      0x4B0082,
    "Legendary": 0x8B6914,
    "Mythic":    0xB22222,
}

_RARITY_DOT: Dict[str, str] = {
    "Default":   "⬜",
    "Common":    "🔘",
    "Uncommon":  "🟢",
    "Rare":      "🔵",
    "Epic":      "🟣",
    "Legendary": "🟡",
    "Mythic":    "🔴",
}

_CAT_ICON: Dict[str, str] = {
    "relics": "🔮",
    "titles": "👑",
    "skins":  "🎭",
    "badges": "🎖️",
}


# ─── Item helpers ─────────────────────────────────────────────────────────────

def _cat_items(cat: str) -> list:
    """Return price-sorted item list for a category (excluding free defaults)."""
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


# ─── Main Hub View ────────────────────────────────────────────────────────────

class InfernalMarketHub(discord.ui.View):
    """
    One view object manages the entire market session for a single user.
    Modes: hub → category → preview → done.
    All transitions edit the same message in place.
    """

    MODE_HUB      = "hub"
    MODE_CATEGORY = "category"
    MODE_PREVIEW  = "preview"
    MODE_DONE     = "done"

    def __init__(
        self,
        *,
        owner_id:       int,
        bot,
        guild_id:       str,
        discord_id:     str,
        user_rank:      str,
        owned_skins:    List[str],
        owned_titles:   List[str],
        owned_relics:   List[str],
        owned_badges:   List[str],
        equipped_skin:  str,
        equipped_title: str,
        equipped_relic: str,
        equipped_badges: List[str],
    ):
        super().__init__(timeout=300)
        self.owner_id        = owner_id
        self.bot             = bot
        self.guild_id        = guild_id
        self.discord_id      = discord_id
        self.user_rank       = user_rank
        self.user_rank_idx   = _rank_idx(user_rank)

        # Mutable ownership state (updated on purchase)
        self._owned_skins:   Set[str] = set(owned_skins)
        self._owned_titles:  Set[str] = set(owned_titles)
        self._owned_relics:  Set[str] = set(owned_relics)
        self._owned_badges:  Set[str] = set(owned_badges)
        self._eq_skin   = equipped_skin  or "default"
        self._eq_title  = equipped_title or "Unmarked"
        self._eq_relic  = equipped_relic or ""
        self._eq_badges: List[str] = list(equipped_badges)

        # Navigation state
        self._mode     = self.MODE_HUB
        self._cat:     Optional[str] = None
        self._item_idx = 0

        # Result state (after purchase)
        self._result_ok   = False
        self._result_item = None
        self._result_msg  = ""
        self._result_cost = 0
        self._result_bal  = 0

        self._rebuild()

    # ── Access guard ──────────────────────────────────────────────────────────

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This session belongs to another soul. Open your own market.*",
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

    def _status_label(self, item) -> str:
        if self._is_equipped(item):
            return "✦  **EQUIPPED**"
        if self._is_owned(item):
            return "✓  **OWNED**"
        if self._is_locked(item):
            req = getattr(item, "min_rank", "?")
            return f"🔒  **LOCKED** — Requires **{req}**"
        return "⚔  **AVAILABLE**"

    def _can_acquire(self, item) -> bool:
        return not self._is_owned(item) and not self._is_locked(item)

    # ── View rebuild ──────────────────────────────────────────────────────────

    def _rebuild(self):
        self.clear_items()
        if self._mode == self.MODE_HUB:
            self._build_hub()
        elif self._mode == self.MODE_CATEGORY:
            self._build_category()
        elif self._mode == self.MODE_PREVIEW:
            self._build_preview()
        elif self._mode == self.MODE_DONE:
            self._build_done()

    def _build_hub(self):
        cats = [
            ("🔮  Relics",  "relics"),
            ("👑  Titles",  "titles"),
            ("🎭  Skins",   "skins"),
            ("🎖️  Badges", "badges"),
        ]
        for label, cat in cats:
            btn = discord.ui.Button(
                label=label, style=discord.ButtonStyle.secondary, row=0
            )
            btn.callback = self._hub_cb(cat)
            self.add_item(btn)

        leave = discord.ui.Button(
            label="🚪  Leave", style=discord.ButtonStyle.secondary, row=1
        )
        leave.callback = self._leave_cb
        self.add_item(leave)

    def _build_category(self):
        items = self._items()
        item  = self._current()
        n     = len(items)
        idx   = self._item_idx

        can_acquire = item is not None and self._can_acquire(item)

        prev = discord.ui.Button(
            label="⬅️  Previous",
            style=discord.ButtonStyle.secondary,
            row=0,
            disabled=(idx <= 0),
        )
        nxt = discord.ui.Button(
            label="➡️  Next",
            style=discord.ButtonStyle.secondary,
            row=0,
            disabled=(idx >= n - 1),
        )
        prev.callback = self._prev_cb
        nxt.callback  = self._next_cb
        self.add_item(prev)
        self.add_item(nxt)

        acquire = discord.ui.Button(
            label="🩸  Acquire",
            style=discord.ButtonStyle.danger if can_acquire else discord.ButtonStyle.secondary,
            row=1,
            disabled=not can_acquire,
        )
        preview = discord.ui.Button(
            label="👁️  Preview",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        back = discord.ui.Button(
            label="🔙  Back",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        acquire.callback = self._acquire_cb
        preview.callback = self._preview_cb
        back.callback    = self._back_to_hub_cb
        self.add_item(acquire)
        self.add_item(preview)
        self.add_item(back)

    def _build_preview(self):
        back = discord.ui.Button(
            label="🔙  Back",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        back.callback = self._back_to_cat_cb
        self.add_item(back)

    def _build_done(self):
        cont = discord.ui.Button(
            label="🔙  Continue Browsing",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        leave = discord.ui.Button(
            label="🚪  Leave",
            style=discord.ButtonStyle.secondary,
            row=0,
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
        if self._mode == self.MODE_DONE:
            return self._done_embed()
        return self._hub_embed()

    def _hub_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🩸  Kingdom Exchange",
            description=(
                f"{_SEP}\n\n"
                "*The gates open.*\n\n"
                "*Power is not given.*\n"
                "*It is taken… at a price.*\n\n"
                "*Choose what you seek, soul.*\n\n"
                f"{_SEP}"
            ),
            color=0x0D0D0D,
        )
        embed.add_field(
            name="🔮  Relics",
            value=f"*Visual effects applied to your Identity Card*\n`{len(RELICS_CATALOG)} items`",
            inline=True,
        )
        embed.add_field(
            name="👑  Titles",
            value=f"*Marks displayed beneath your name*\n`{sum(1 for t in TITLES_CATALOG.values() if t.price_dc > 0)} items`",
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="🎭  Skins",
            value=f"*Full Identity Card redesign*\n`{sum(1 for s in SKINS.values() if s.price_dc > 0)} items`",
            inline=True,
        )
        embed.add_field(
            name="🎖️  Badges",
            value=f"*Insignia displayed on your Identity*\n`{len(BADGES_CATALOG)} items`",
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.set_footer(text=f"Kingdom Treasury  ·  {self.user_rank}  ·  Kingdom of Hell")
        return embed

    def _cat_embed(self) -> discord.Embed:
        item  = self._current()
        items = self._items()
        n     = len(items)
        idx   = self._item_idx

        if not item:
            return discord.Embed(
                description="*No items found in this category.*",
                color=0x0D0D0D,
            )

        icon      = _CAT_ICON.get(self._cat or "", "🛒")
        rarity    = getattr(item, "rarity", "Unknown")
        dot       = _RARITY_DOT.get(rarity, "⬜")
        color     = _RARITY_COLOR.get(rarity, 0x0D0D0D)
        price_dc  = getattr(item, "price_dc", 0)
        min_rank  = getattr(item, "min_rank", "")
        status    = self._status_label(item)

        cat_label = (self._cat or "").rstrip("s").title()
        if self._cat == "badges":
            cat_label = "Badge"

        icon_str = getattr(item, "icon", "") if self._cat == "badges" else ""

        embed = discord.Embed(
            title=f"{icon}  {(self._cat or '').upper()}",
            color=color,
        )
        embed.add_field(name="\u200b", value=_SEP, inline=False)
        embed.add_field(
            name=f"{dot}  **{icon_str}{' ' if icon_str else ''}{item.name}**",
            value=f"*{item.description}*",
            inline=False,
        )
        embed.add_field(name="\u200b", value=_SEP, inline=False)
        embed.add_field(
            name="PRICE",
            value=f"**{price_dc:,}** {_DC}",
            inline=True,
        )
        embed.add_field(
            name="TYPE",
            value=f"**{cat_label}**",
            inline=True,
        )
        embed.add_field(
            name="RARITY",
            value=f"**{rarity}**",
            inline=True,
        )
        embed.add_field(
            name="REQUIRED RANK",
            value=f"**{min_rank}**+" if min_rank else "**All Ranks**",
            inline=True,
        )
        embed.add_field(
            name="STATUS",
            value=status,
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value=_SEP, inline=False)
        embed.set_footer(
            text=f"Item {idx + 1} of {n}  ·  {self.user_rank}  ·  Kingdom Treasury"
        )
        return embed

    def _preview_embed(self) -> discord.Embed:
        item = self._current()

        # Simulate equipped state if this item were equipped
        preview_skin    = self._eq_skin
        preview_title   = self._eq_title
        preview_relic   = self._eq_relic
        preview_badges  = list(self._eq_badges)

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
                badge_display += BADGES_CATALOG[bid].icon + " "
        if not badge_display:
            badge_display = "None"

        effect_desc = ""
        if item:
            effect_desc = getattr(item, "effect_desc", item.description)

        embed = discord.Embed(
            title="👁️  Manifestation",
            description=(
                f"{_SEP}\n\n"
                f"*{effect_desc}*\n\n"
                f"{_SEP}"
            ),
            color=0x1A0A2E,
        )
        embed.add_field(name="Active Skin",   value=f"**{skin_name}**",   inline=True)
        embed.add_field(name="Active Title",  value=f"**{title_name}**",  inline=True)
        embed.add_field(name="Active Relic",  value=f"**{relic_name}**",  inline=True)
        embed.add_field(name="Active Badges", value=badge_display,         inline=True)
        embed.add_field(
            name="\u200b",
            value=(
                "*This is a simulation of your identity after equipping this item.*\n"
                "*Use `/relics` to manage equipped items after purchase.*"
            ),
            inline=False,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    def _done_embed(self) -> discord.Embed:
        if self._result_ok and self._result_item:
            item   = self._result_item
            rarity = getattr(item, "rarity", "Unknown")
            color  = _RARITY_COLOR.get(rarity, 0xFFD700)
            embed  = discord.Embed(
                title="🩸  Acquisition Complete",
                description=(
                    f"{_SEP}\n\n"
                    "*You have claimed:*\n\n"
                    f"## {getattr(item, 'icon', '') + ' ' if getattr(item, 'icon', '') else ''}{item.name}\n\n"
                    "*The Kingdom acknowledges your offering.*\n\n"
                    f"{_SEP}"
                ),
                color=color,
            )
            embed.add_field(
                name="COST",
                value=f"**{self._result_cost:,}** {_DC}",
                inline=True,
            )
            embed.add_field(
                name="BALANCE",
                value=f"**{self._result_bal:,}** {_DC}",
                inline=True,
            )
            embed.add_field(
                name="RARITY",
                value=f"**{rarity}**",
                inline=True,
            )
            embed.add_field(
                name="\u200b",
                value="*Use `/relics` to equip your acquisition.*",
                inline=False,
            )
        else:
            embed = discord.Embed(
                title="🩸  Exchange Denied",
                description=(
                    f"{_SEP}\n\n"
                    f"*{self._result_msg or 'The Kingdom refuses this transaction.'}*\n\n"
                    f"{_SEP}"
                ),
                color=0x0A0A0A,
            )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ── Navigation callbacks ──────────────────────────────────────────────────

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
            description=(
                f"{_SEP}\n\n"
                "*The gates close behind you.*\n\n"
                "*The Kingdom remembers all transactions.*\n\n"
                f"{_SEP}"
            ),
            color=0x0D0D0D,
        )
        farewell.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=farewell, view=None)
        self.stop()

    # ── Acquire callback ──────────────────────────────────────────────────────

    async def _acquire_cb(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return

        item = self._current()
        if not item or not self._can_acquire(item):
            await interaction.response.send_message(
                "*This item is not available for acquisition.*", ephemeral=True
            )
            return

        # Immediate response — "Sealing the exchange..."
        seal_embed = discord.Embed(
            description=(
                f"{_SEP}\n\n"
                "🩸  *Sealing the exchange...*\n\n"
                "*The Kingdom weighs your offering.*\n\n"
                f"{_SEP}"
            ),
            color=0x0D0D0D,
        )
        seal_embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        msg_id = interaction.message.id
        await interaction.response.edit_message(embed=seal_embed, view=None)

        # Atmospheric delay
        await asyncio.sleep(1.0)

        # Perform purchase
        try:
            # Re-check sacrifice gate
            user_data = await self.bot.db.get_user(self.guild_id, self.discord_id)
            if user_data and user_data.get("sacrifice_active"):
                raise ValueError(
                    "Access denied. Your debt must be cleared before entering the market."
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

            # Ledger log
            cost    = result.get("cost", 0)
            new_bal = result.get("new_balance", 0)
            ledger  = getattr(self.bot, "ledger_service", None)
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
        except Exception as e:
            log.exception("Market purchase error")
            self._result_ok  = False
            self._result_msg = "An internal error occurred. Please try again."

        # Update display
        self._mode = self.MODE_DONE
        self._rebuild()

        try:
            await interaction.followup.edit_message(
                msg_id,
                embed=self.build_embed(),
                view=self,
            )
        except Exception:
            try:
                await interaction.message.edit(embed=self.build_embed(), view=self)
            except Exception:
                log.exception("Failed to edit market message after purchase")

    # ── Timeout ───────────────────────────────────────────────────────────────

    async def on_timeout(self):
        try:
            # View will simply stop responding; message stays visible
            pass
        except Exception:
            pass
