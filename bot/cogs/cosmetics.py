"""
CosmeticsCog — /market, /equip-skin, /equip-title
Removed: /skins, /buy-skin, /titles, /buy-title (replaced by /market)
Removed: /badges (badges no longer displayed)
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

                icon  = "🎨" if item.item_type == "skin" else "🎭"
                hint  = "/equip-skin" if item.item_type == "skin" else "/equip-title"
                embed = discord.Embed(
                    title=f"{icon}  Acquired — {item.name}",
                    description=f"*{item.description}*",
                    color=GOLD,
                )
                embed.add_field(name="COST",    value=f"**{cost:,} DC**",        inline=True)
                embed.add_field(name="BALANCE", value=f"**{new_balance:,} DC**", inline=True)
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
                    name  = f"{item.name} [{type_tag} · {item.rarity} · {item.price:,} DC]",
                    value = f"{item.item_type}:{item.id}",
                ))
            if len(choices) >= 25:
                break
        return choices

    # ─── /equip-skin ──────────────────────────────────────────────────────────

    @app_commands.command(name="equip-skin", description="Equip an owned card skin.")
    @app_commands.describe(skin_id="The skin to equip.")
    @app_commands.choices(skin_id=[
        app_commands.Choice(name=s.name, value=sid) for sid, s in SKINS.items()
    ])
    async def equip_skin(self, interaction: discord.Interaction, skin_id: str):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "equip-skin", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            result = await self.cosmetics.equip_skin(guild_id, discord_id, skin_id)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        skin  = result["skin"]
        embed = discord.Embed(
            title=f"{skin.title_banner.split('  ')[0]}  Skin Equipped",
            description=(
                f"*You have equipped the **{skin.name}** card skin.*\n"
                f"*Use `/identity` to see your updated card.*"
            ),
            color=skin.color,
        )
        embed.add_field(name="Theme",  value=skin.theme_tag,     inline=True)
        embed.add_field(name="Flavor", value=skin.footer_flavor, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ─── /equip-title ─────────────────────────────────────────────────────────

    @app_commands.command(name="equip-title", description="Equip a title you own.")
    @app_commands.describe(title="The title to equip.")
    @app_commands.choices(title=[
        app_commands.Choice(name=t.name, value=t.name) for t in TITLES_CATALOG.values()
    ])
    async def equip_title(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "equip-title", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)
        try:
            await self.cosmetics.equip_title(guild_id, discord_id, title)
        except ValueError as e:
            embed = discord.Embed(description=f"*{e}*", color=VOID_BLACK)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        t_obj = TITLES_CATALOG.get(title)
        embed = discord.Embed(
            title="🎭  Title Equipped",
            description=(
                f"*You now bear the title **{title}**.*\n"
                f"*It is displayed on your `/identity` card.*"
            ),
            color=RARITY_EMBED_COLORS.get(t_obj.rarity if t_obj else "Common", BLOOD_RED),
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)


# ── item resolution helper ────────────────────────────────────────────────────

def _resolve_item(raw: str) -> Optional[MarketItem]:
    """
    Parse the autocomplete value (type:id) or fall back to name search.
    """
    if ":" in raw:
        item_type, item_id = raw.split(":", 1)
        for item in _MARKET_ITEMS:
            if item.item_type == item_type and item.id == item_id:
                return item
    # Fallback: name match (case-insensitive)
    q = raw.lower()
    for item in _MARKET_ITEMS:
        if item.name.lower() == q:
            return item
    return None
