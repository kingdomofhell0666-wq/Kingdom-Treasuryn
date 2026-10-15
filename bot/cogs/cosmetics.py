"""
CosmeticsCog — /market, /inventory
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ..services.cosmetic_service import CosmeticService
from ..utils.skins import (
    detect_rank_from_roles, rank_idx,
)
from ..utils.routing import check_routing
from ..ui.infernal_market import InfernalMarketHub
from ..ui.infernal_inventory import InfernalInventoryView


VOID_BLACK = 0x0A0A0A
_SEP = "━━━━━━━━━━━━━━━━━━━━━━━"


class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def cosmetics(self) -> CosmeticService:
        return self.bot.cosmetic_service

    @property
    def db(self):
        return self.bot.db

    # ─── /market ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="market",
        description="Enter the Kingdom Exchange — the private cosmetics marketplace.",
    )
    async def market(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            # Interaction already expired (stale event after bot restart).
            # Nothing to do — Discord showed "interaction failed" on their end.
            return

        if not await check_routing(interaction, "market", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        await self.db.upsert_user(guild_id, discord_id, interaction.user.display_name)

        user_row = await self.db.get_user(guild_id, discord_id)

        # Sacrifice gate — market access revoked while under debt penalty
        if user_row and user_row.get("sacrifice_active"):
            embed = discord.Embed(
                description=(
                    f"{_SEP}\n\n"
                    "*The gates are sealed.*\n\n"
                    "*Your debt binds you. Settle it before you may enter.*\n\n"
                    f"{_SEP}"
                ),
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        user_balance  = user_row.get("balance", 0) if user_row else 0

        # Detect rank from actual Discord roles (real-time, highest wins).
        # Use the stored economy rank when no matching Discord role is present.
        db_rank   = user_row.get("rank", "Unranked") if user_row else "Unranked"
        role_rank = detect_rank_from_roles(getattr(interaction.user, "roles", []))
        user_rank = role_rank if role_rank and rank_idx(role_rank) > rank_idx(db_rank) else db_rank

        # Fetch full cosmetic state
        owned_skins  = await self.cosmetics.get_owned_skins(guild_id, discord_id)
        owned_titles = await self.cosmetics.get_owned_titles(guild_id, discord_id)
        owned_relics = await self.cosmetics.get_owned_relics(guild_id, discord_id)
        owned_badges = await self.cosmetics.get_owned_badges_list(guild_id, discord_id)
        eq_skin      = await self.cosmetics.get_equipped_skin_id(guild_id, discord_id)
        eq_title     = await self.cosmetics.get_equipped_title(guild_id, discord_id)
        eq_relic     = await self.cosmetics.get_equipped_relic(guild_id, discord_id)
        eq_badges    = await self.cosmetics.get_equipped_badges(guild_id, discord_id)

        hub = InfernalMarketHub(
            owner_id        = interaction.user.id,
            bot             = self.bot,
            guild_id        = guild_id,
            discord_id      = discord_id,
            user_rank       = user_rank,
            user_balance    = user_balance,
            owned_skins     = owned_skins,
            owned_titles    = owned_titles,
            owned_relics    = owned_relics,
            owned_badges    = owned_badges,
            equipped_skin   = eq_skin,
            equipped_title  = eq_title,
            equipped_relic  = eq_relic,
            equipped_badges = eq_badges,
        )
        msg = await interaction.followup.send(embed=hub.build_embed(), view=hub, ephemeral=True)
        hub._message = msg

    # ─── /inventory ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="inventory",
        description="Open your Infernal Inventory — manage and equip what you own.",
    )
    async def inventory(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            return

        if not await check_routing(interaction, "inventory", getattr(self.bot, "config_service", None)):
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

        view = InfernalInventoryView(
            owner_id        = interaction.user.id,
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
        msg = await interaction.followup.send(
            embed=view.build_embed(), view=view, ephemeral=True
        )
        view._message = msg


