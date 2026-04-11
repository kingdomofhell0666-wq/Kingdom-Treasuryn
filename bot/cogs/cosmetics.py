"""
CosmeticsCog — /market, /relics
"""
from __future__ import annotations

import os
import json
from typing import Optional, List

import discord
from discord import app_commands
from discord.ext import commands

from ..services.cosmetic_service import CosmeticService
from ..utils.skins import (
    SKINS, TITLES_CATALOG, RELICS_CATALOG, BADGES_CATALOG,
    DEFAULT_SKIN_ID,
)
from ..utils.routing import check_routing
from ..ui.infernal_market import InfernalMarketHub


VOID_BLACK = 0x0A0A0A
GOLD       = 0xFFD700

_SEP = "━━━━━━━━━━━━━━━━━━━━━━━"


def _get_exchange_url() -> str:
    domains = os.environ.get("REPLIT_DOMAINS") or os.environ.get("REPLIT_DEV_DOMAIN") or "localhost:80"
    primary = domains.split(",")[0].strip()
    if "localhost" in primary:
        return f"http://{primary}/exchange/"
    return f"https://{primary}/exchange/"


# ── Market entry view ─────────────────────────────────────────────────────────

class MarketEntryView(discord.ui.View):
    """Shown when a user types /market — links to the web Exchange."""

    def __init__(self, exchange_url: str):
        super().__init__(timeout=300)
        self.add_item(discord.ui.Button(
            label  = "Enter the Exchange",
            style  = discord.ButtonStyle.link,
            url    = exchange_url,
            emoji  = "🩸",
        ))

    @discord.ui.button(label="Step back", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def step_back(self, interaction: discord.Interaction, _button: discord.ui.Button):
        embed = discord.Embed(
            description=(
                f"{_SEP}\n\n"
                "*You stepped back.*\n\n"
                "*The threshold remains.*\n\n"
                "*Return when you are ready.*\n\n"
                f"{_SEP}"
            ),
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=embed, view=None)


# ── Cog ────────────────────────────────────────────────────────────────────────

class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def cosmetics(self) -> CosmeticService: return self.bot.cosmetic_service
    @property
    def db(self):                           return self.bot.db

    # ─── /market ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="market",
        description="Enter the Kingdom Exchange — the private cosmetics marketplace.",
    )
    async def market(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "market", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)

        # Sacrifice gate — market access revoked while under penalty
        user_row = await self.db.get_user(guild_id, discord_id)
        if user_row and user_row.get("sacrifice_active"):
            embed = discord.Embed(
                description=(
                    f"{_SEP}\n\n"
                    "*The gates are sealed.*\n\n"
                    "*Settle your debt before you may enter.*\n\n"
                    f"{_SEP}"
                ),
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        exchange_url = _get_exchange_url()

        embed = discord.Embed(
            title="💀  Kingdom Exchange",
            description=(
                f"{_SEP}\n\n"
                "*You stand before a threshold not meant for the weak.*\n\n"
                "*Beyond this point… nothing is given.*\n\n"
                "*Everything is taken.*\n\n"
                "*The Kingdom does not guarantee your return unchanged.*\n\n"
                f"{_SEP}"
            ),
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

        view = MarketEntryView(exchange_url=exchange_url)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ─── /relics ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="relics",
        description="Manage equipped skins, titles, relics, and badges on your Identity.",
    )
    async def relics(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "relics", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)

        owned_skins     = await self.cosmetics.get_owned_skins(guild_id, discord_id)
        owned_titles    = await self.cosmetics.get_owned_titles(guild_id, discord_id)
        owned_relics    = await self.cosmetics.get_owned_relics(guild_id, discord_id)
        owned_badges    = await self.cosmetics.get_owned_badges_list(guild_id, discord_id)
        equipped_skin   = await self.cosmetics.get_equipped_skin_id(guild_id, discord_id)
        equipped_title  = await self.cosmetics.get_equipped_title(guild_id, discord_id)
        equipped_relic  = await self.cosmetics.get_equipped_relic(guild_id, discord_id)
        equipped_badges = await self.cosmetics.get_equipped_badges(guild_id, discord_id)

        view = RelicsView(
            bot             = self.bot,
            guild_id        = guild_id,
            discord_id      = discord_id,
            owned_skins     = owned_skins,
            owned_titles    = owned_titles,
            owned_relics    = owned_relics,
            owned_badges    = owned_badges,
            equipped_skin   = equipped_skin,
            equipped_title  = equipped_title,
            equipped_relic  = equipped_relic,
            equipped_badges = equipped_badges,
        )
        await interaction.followup.send(
            embed=view.build_embed(), view=view, ephemeral=True
        )


# ── Relics View ────────────────────────────────────────────────────────────────

class RelicsView(discord.ui.View):
    """
    Ephemeral panel showing a user's owned cosmetics with dropdown menus to equip.
    Rows: skin select, title select, relic select, badge multi-select (up to 3).
    """

    def __init__(
        self,
        *,
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
        super().__init__(timeout=180)
        self.bot             = bot
        self.guild_id        = guild_id
        self.discord_id      = discord_id
        self.owned_skins     = owned_skins
        self.owned_titles    = owned_titles
        self.owned_relics    = owned_relics
        self.owned_badges    = owned_badges
        self.equipped_skin   = equipped_skin
        self.equipped_title  = equipped_title
        self.equipped_relic  = equipped_relic
        self.equipped_badges: List[str] = list(equipped_badges)
        self._rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.discord_id

    def _rebuild(self):
        self.clear_items()

        # Row 0 — Skin select
        skin_options: List[discord.SelectOption] = []
        for skin_id in self.owned_skins:
            skin = SKINS.get(skin_id)
            if not skin:
                continue
            equipped = skin_id == self.equipped_skin
            skin_options.append(discord.SelectOption(
                label       = (f"✦ {skin.name}" if equipped else skin.name)[:100],
                value       = skin_id,
                description = f"{skin.rarity}  ·  {skin.theme_tag}"[:100],
                default     = equipped,
            ))
        if skin_options:
            sel = discord.ui.Select(
                placeholder = "🎭  Bind a skin to your card…",
                options     = skin_options[:25],
                min_values  = 1,
                max_values  = 1,
                row         = 0,
            )
            sel.callback = self._skin_cb
            self.add_item(sel)

        # Row 1 — Title select
        title_options: List[discord.SelectOption] = []
        for title_name, title in TITLES_CATALOG.items():
            if title.price_dc > 0 and title_name not in self.owned_titles:
                continue
            equipped = title_name == self.equipped_title
            title_options.append(discord.SelectOption(
                label       = (f"✦ {title.name}" if equipped else title.name)[:100],
                value       = title_name,
                description = title.rarity[:100],
                default     = equipped,
            ))
        if title_options:
            sel = discord.ui.Select(
                placeholder = "👑  Bear a mark upon your card…",
                options     = title_options[:25],
                min_values  = 1,
                max_values  = 1,
                row         = 1,
            )
            sel.callback = self._title_cb
            self.add_item(sel)

        # Row 2 — Relic select (owned relics + "No Relic" option)
        relic_options: List[discord.SelectOption] = [
            discord.SelectOption(
                label       = "— No Relic —",
                value       = "",
                description = "Remove active relic",
                default     = not self.equipped_relic,
            )
        ]
        for relic_id in self.owned_relics:
            relic = RELICS_CATALOG.get(relic_id)
            if not relic:
                continue
            equipped = relic_id == self.equipped_relic
            relic_options.append(discord.SelectOption(
                label       = (f"✦ {relic.name}" if equipped else relic.name)[:100],
                value       = relic_id,
                description = relic.rarity[:100],
                default     = equipped,
            ))
        if len(relic_options) > 1:  # only show if user owns at least one relic
            sel = discord.ui.Select(
                placeholder = "🔮  Activate a relic…",
                options     = relic_options[:25],
                min_values  = 1,
                max_values  = 1,
                row         = 2,
            )
            sel.callback = self._relic_cb
            self.add_item(sel)

        # Row 3 — Badge multi-select (select which to equip, 0-3)
        badge_options: List[discord.SelectOption] = []
        for badge_id in self.owned_badges:
            badge = BADGES_CATALOG.get(badge_id)
            if not badge:
                continue
            badge_options.append(discord.SelectOption(
                label       = badge.name[:100],
                value       = badge_id,
                description = f"{badge.icon}  {badge.rarity}"[:100],
                default     = badge_id in self.equipped_badges,
            ))
        if badge_options:
            sel = discord.ui.Select(
                placeholder = "🎖️  Toggle active badges (choose up to 3)…",
                options     = badge_options[:25],
                min_values  = 0,
                max_values  = min(3, len(badge_options)),
                row         = 3,
            )
            sel.callback = self._badge_cb
            self.add_item(sel)

    # ── Callbacks ──────────────────────────────────────────────────────────────

    async def _skin_cb(self, interaction: discord.Interaction):
        if not self._guard(interaction):
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
        if not self._guard(interaction):
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

    async def _relic_cb(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message(
                "*This collection belongs to another soul.*", ephemeral=True
            )
            return
        relic_id = interaction.data["values"][0]
        try:
            if relic_id:
                await self.bot.cosmetic_service.equip_relic(self.guild_id, self.discord_id, relic_id)
                self.equipped_relic = relic_id
            else:
                await self.bot.cosmetic_service.unequip_relic(self.guild_id, self.discord_id)
                self.equipped_relic = ""
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except ValueError as e:
            await interaction.response.send_message(f"*{e}*", ephemeral=True)

    async def _badge_cb(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message(
                "*This collection belongs to another soul.*", ephemeral=True
            )
            return
        selected = interaction.data.get("values", [])
        try:
            await self.bot.db.set_equipped_badges(
                self.guild_id, self.discord_id, json.dumps(selected)
            )
            self.equipped_badges = selected
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except Exception as e:
            await interaction.response.send_message(f"*An error occurred: {e}*", ephemeral=True)

    # ── Embed ──────────────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        eq_skin_obj  = SKINS.get(self.equipped_skin) or SKINS.get(DEFAULT_SKIN_ID)
        eq_skin_name = eq_skin_obj.name if eq_skin_obj else "Infernal Standard"
        eq_title     = self.equipped_title or "Unmarked"
        eq_relic_obj = RELICS_CATALOG.get(self.equipped_relic)
        eq_relic_str = eq_relic_obj.name if eq_relic_obj else "None"

        badge_icons = ""
        for bid in self.equipped_badges[:3]:
            bd = BADGES_CATALOG.get(bid)
            if bd:
                badge_icons += bd.icon + " "
        badge_display = badge_icons.strip() or "None"

        color = eq_skin_obj.color if eq_skin_obj else 0x0D0D0D

        embed = discord.Embed(
            title       = "🗝️  Identity Loadout",
            description = (
                "*Relics reshape your card. Marks define your name.*\n"
                "*Select from the menus below to equip.*"
            ),
            color = color,
        )
        embed.add_field(name="Active Skin",   value=f"**{eq_skin_name}**",  inline=True)
        embed.add_field(name="Active Title",  value=f"**{eq_title}**",      inline=True)
        embed.add_field(name="Active Relic",  value=f"**{eq_relic_str}**",  inline=True)
        embed.add_field(name="Active Badges", value=badge_display,           inline=True)
        embed.add_field(name="\u200b",        value="\u200b",                inline=True)
        embed.add_field(name="\u200b",        value="\u200b",                inline=True)
        embed.add_field(
            name  = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value = (
                f"Skins: **{len(self.owned_skins)}** owned  ·  "
                f"Titles: **{len(self.owned_titles)}** owned  ·  "
                f"Relics: **{len(self.owned_relics)}** owned  ·  "
                f"Badges: **{len(self.owned_badges)}** owned"
            ),
            inline = False,
        )
        embed.set_footer(text="Use /market to acquire cosmetics  ·  Kingdom Treasury")
        return embed
