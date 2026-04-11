"""
CosmeticsCog — /market, /relics
"""
from __future__ import annotations

from typing import Optional, List

import discord
from discord import app_commands
from discord.ext import commands

from ..services.cosmetic_service import CosmeticService
from ..utils.skins import (
    get_skin, get_all_skins, SKINS, TITLES_CATALOG,
    RARITY_COLORS as SKIN_RARITY_COLORS, DEFAULT_SKIN_ID,
)
from ..utils.formatting import format_dc
from ..utils.routing import check_routing
from ..ui import MarketView, MarketItem


VOID_BLACK = 0x0A0A0A
BLOOD_RED  = 0x6B0000
GOLD       = 0xFFD700
DARK_RED   = 0x8B0000
SEP        = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

RARITY_EMBED_COLORS = {
    "Default":   VOID_BLACK, "Common":    0x444444,
    "Uncommon":  0x1A5C1A,   "Rare":      0x0D3D80,
    "Epic":      0x4B0082,   "Legendary": 0x8B6914,
    "Special":   0x8B0000,
}


def _build_market_items() -> List[MarketItem]:
    """
    Returns the full catalog of purchasable cosmetics:
    - Skins with price_dc > 0 (sorted by price)
    - Titles with price_dc > 0 (sorted by price)
    """
    items: List[MarketItem] = []

    for sid, skin in SKINS.items():
        if skin.price_dc > 0:
            items.append(MarketItem(
                id=sid, name=skin.name, item_type="skin",
                price=skin.price_dc, description=skin.description,
                rarity=skin.rarity,
            ))

    for tname, title in TITLES_CATALOG.items():
        if title.price_dc > 0:
            items.append(MarketItem(
                id=tname, name=title.name, item_type="title",
                price=title.price_dc, description=title.description,
                rarity=title.rarity,
            ))

    items.sort(key=lambda x: x.price)
    return items


_MARKET_ITEMS: List[MarketItem] = _build_market_items()


# ── Cog ────────────────────────────────────────────────────────────────────────

class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def cosmetics(self) -> CosmeticService: return self.bot.cosmetic_service
    @property
    def db(self):                           return self.bot.db

    # ─── /market ──────────────────────────────────────────────────────────────

    @app_commands.command(name="market", description="Browse infernal cosmetics — skins and titles.")
    @app_commands.describe(buy="Name of a skin or title to purchase directly (optional).")
    async def market(self, interaction: discord.Interaction, buy: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "market", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        await self.db.upsert_user(guild_id, discord_id, username)

        # ── Sacrifice gate: market access revoked while under penalty ─────────
        user_row = await self.db.get_user(guild_id, discord_id)
        if user_row and user_row.get("sacrifice_active"):
            embed = discord.Embed(
                description="*You are under restriction. Settle your debt.*",
                color=0x0A0A0A,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # ── Direct purchase path ───────────────────────────────────────────────
        if buy:
            item = _resolve_item(buy)
            if item is None:
                embed = discord.Embed(
                    description="*Item not found. Use autocomplete or `/market` to browse.*",
                    color=VOID_BLACK,
                )
                embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            try:
                if item.item_type == "skin":
                    result = await self.cosmetics.buy_skin(guild_id, discord_id, item.id)
                    cost, new_balance = result["cost"], result["new_balance"]
                else:
                    result = await self.cosmetics.buy_title(guild_id, discord_id, item.id)
                    cost, new_balance = result["cost"], result["new_balance"]

                ledger = getattr(self.bot, "ledger_service", None)
                if ledger and cost > 0:
                    await ledger.log(
                        action          = "market_purchase",
                        amount          = cost,
                        from_label      = f"<@{discord_id}>",
                        to_label        = f"Kingdom Market — {item.name}",
                        guild_id        = guild_id,
                        from_discord_id = discord_id,
                        wallet_before   = new_balance + cost,
                        wallet_after    = new_balance,
                        action_type     = "market",
                    )

                icon  = "🎨" if item.item_type == "skin" else "🎭"
                hint  = "/equip-skin" if item.item_type == "skin" else "/equip-title"
                embed = discord.Embed(
                    title=f"{icon}  Acquired — {item.name}",
                    description=f"*{item.description}*",
                    color=GOLD,
                )
                embed.add_field(name="COST",    value=f"**{cost:,}** <:devilcoinStack:1492184333392412692>",        inline=True)
                embed.add_field(name="BALANCE", value=f"**{new_balance:,}** <:devilcoinStack:1492184333392412692>", inline=True)
                embed.add_field(name="RARITY",  value=item.rarity,               inline=True)
                embed.add_field(
                    name="\u200b",
                    value=f"*Use `{hint}` to activate it on your Identity Card.*",
                    inline=False,
                )
                embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

            except ValueError as e:
                embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
                embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # ── UI browse path ─────────────────────────────────────────────────────
        owned_skins   = await self.cosmetics.get_owned_skins(guild_id, discord_id)
        owned_titles  = await self.cosmetics.get_owned_titles(guild_id, discord_id)
        equipped_skin = await self.cosmetics.get_equipped_skin_id(guild_id, discord_id)
        equipped_title= await self.cosmetics.get_equipped_title(guild_id, discord_id)

        view = MarketView(
            items          = _MARKET_ITEMS,
            owner_id       = interaction.user.id,
            bot            = self.bot,
            guild_id       = guild_id,
            discord_id     = discord_id,
            owned_skins    = owned_skins,
            owned_titles   = owned_titles,
            equipped_skin  = equipped_skin,
            equipped_title = equipped_title,
        )
        await interaction.followup.send(embed=view.build_embed(), view=view, ephemeral=True)

    @market.autocomplete("buy")
    async def market_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        q = current.lower()
        choices = []
        for item in _MARKET_ITEMS:
            if q in item.name.lower() or q in item.item_type.lower():
                type_tag = "Skin" if item.item_type == "skin" else "Title"
                choices.append(app_commands.Choice(
                    name  = f"{item.name} [{type_tag} · {item.rarity} · {item.price:,} DC]",  # DC kept — autocomplete has char limit
                    value = f"{item.item_type}:{item.id}",
                ))
            if len(choices) >= 25:
                break
        return choices

    # ─── /relics ──────────────────────────────────────────────────────────────

    @app_commands.command(name="relics", description="View and equip your owned relics and marks.")
    async def relics(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "relics", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)

        owned_skins    = await self.cosmetics.get_owned_skins(guild_id, discord_id)
        owned_titles   = await self.cosmetics.get_owned_titles(guild_id, discord_id)
        equipped_skin  = await self.cosmetics.get_equipped_skin_id(guild_id, discord_id)
        equipped_title = await self.cosmetics.get_equipped_title(guild_id, discord_id)

        view = RelicsView(
            bot            = self.bot,
            guild_id       = guild_id,
            discord_id     = discord_id,
            owned_skins    = owned_skins,
            owned_titles   = owned_titles,
            equipped_skin  = equipped_skin,
            equipped_title = equipped_title,
        )
        await interaction.followup.send(embed=view.build_embed(), view=view, ephemeral=True)


# ── item resolution helper ────────────────────────────────────────────────────

def _resolve_item(raw: str) -> Optional[MarketItem]:
    """Parse the autocomplete value (type:id) or fall back to name search."""
    if ":" in raw:
        item_type, item_id = raw.split(":", 1)
        for item in _MARKET_ITEMS:
            if item.item_type == item_type and item.id == item_id:
                return item
    q = raw.lower()
    for item in _MARKET_ITEMS:
        if item.name.lower() == q:
            return item
    return None


# ── Relics View ────────────────────────────────────────────────────────────────

class RelicsView(discord.ui.View):
    """
    A private, ephemeral panel showing a user's owned relics (skins) and marks
    (titles), with dropdown menus to equip either instantly.
    """

    def __init__(
        self,
        *,
        bot,
        guild_id:       str,
        discord_id:     str,
        owned_skins:    List[str],
        owned_titles:   List[str],
        equipped_skin:  str,
        equipped_title: str,
    ):
        super().__init__(timeout=120)
        self.bot            = bot
        self.guild_id       = guild_id
        self.discord_id     = discord_id
        self.owned_skins    = owned_skins
        self.owned_titles   = owned_titles
        self.equipped_skin  = equipped_skin
        self.equipped_title = equipped_title
        self._rebuild()

    # ── internal helpers ───────────────────────────────────────────────────────

    def _rebuild(self):
        self.clear_items()

        # ── Relic (skin) select ────────────────────────────────────────────────
        skin_options: List[discord.SelectOption] = []
        for skin_id in self.owned_skins:
            skin = SKINS.get(skin_id)
            if not skin:
                continue
            equipped = skin_id == self.equipped_skin
            label    = (f"✦ {skin.name}" if equipped else skin.name)[:100]
            skin_options.append(discord.SelectOption(
                label       = label,
                value       = skin_id,
                description = f"{skin.rarity}  ·  {skin.theme_tag}"[:100],
                default     = equipped,
            ))

        if skin_options:
            sel = discord.ui.Select(
                placeholder = "Bind a relic to your card…",
                options     = skin_options[:25],
                min_values  = 1,
                max_values  = 1,
            )
            sel.callback = self._skin_cb
            self.add_item(sel)

        # ── Mark (title) select ────────────────────────────────────────────────
        title_options: List[discord.SelectOption] = []
        for title_name, title in TITLES_CATALOG.items():
            if title.price_dc > 0 and title_name not in self.owned_titles:
                continue
            equipped = title_name == self.equipped_title
            label    = (f"✦ {title.name}" if equipped else title.name)[:100]
            title_options.append(discord.SelectOption(
                label       = label,
                value       = title_name,
                description = title.rarity[:100],
                default     = equipped,
            ))

        if title_options:
            sel = discord.ui.Select(
                placeholder = "Bear a mark upon your card…",
                options     = title_options[:25],
                min_values  = 1,
                max_values  = 1,
            )
            sel.callback = self._title_cb
            self.add_item(sel)

    # ── callbacks ──────────────────────────────────────────────────────────────

    async def _skin_cb(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.discord_id:
            await interaction.response.send_message(
                "*This collection belongs to another soul.*", ephemeral=True
            )
            return
        skin_id = interaction.data["values"][0]
        try:
            await self.bot.cosmetic_service.equip_skin(self.guild_id, self.discord_id, skin_id)
            self.equipped_skin = skin_id
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except ValueError as e:
            await interaction.response.send_message(f"*{e}*", ephemeral=True)

    async def _title_cb(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.discord_id:
            await interaction.response.send_message(
                "*This collection belongs to another soul.*", ephemeral=True
            )
            return
        title_name = interaction.data["values"][0]
        try:
            await self.bot.cosmetic_service.equip_title(self.guild_id, self.discord_id, title_name)
            self.equipped_title = title_name
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except ValueError as e:
            await interaction.response.send_message(f"*{e}*", ephemeral=True)

    # ── embed ──────────────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        eq_skin  = SKINS.get(self.equipped_skin) or SKINS[DEFAULT_SKIN_ID]
        eq_title = self.equipped_title or "Unmarked"

        embed = discord.Embed(
            title       = "🗝️  Relics & Marks",
            description = (
                "*Relics reshape your card. Marks define your name.*\n"
                "*Select from the menus below to equip.*"
            ),
            color = eq_skin.color,
        )
        embed.add_field(
            name  = "Bound Relic",
            value = f"**{eq_skin.name}**\n*{eq_skin.rarity}  ·  {eq_skin.theme_tag}*",
            inline = True,
        )
        embed.add_field(
            name  = "Worn Mark",
            value = f"**{eq_title}**",
            inline = True,
        )
        embed.add_field(
            name  = "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value = (
                f"Relics in collection: **{len(self.owned_skins)}**\n"
                f"Marks in collection: **{len(self.owned_titles)}** owned"
                f" + {sum(1 for t in TITLES_CATALOG.values() if t.price_dc == 0)} free"
            ),
            inline = False,
        )
        embed.set_footer(text="Use /market to acquire relics and marks  ·  Kingdom Treasury")
        return embed
