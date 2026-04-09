import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from ..services.investment_service import InvestmentService, INVESTMENT_TYPES
from ..utils.embeds import EmbedFactory
from ..utils.result_cards import (
    generate_invest_card, generate_portfolio_card,
    generate_collect_card, generate_withdraw_card,
)
from ..utils.card_generator import fetch_avatar


class InvestmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def investments(self) -> InvestmentService:
        return self.bot.investment_service

    # ─── /invest ──────────────────────────────────────────────────────────────

    @app_commands.command(name="invest", description="Commit DevilCoins to the infernal markets.")
    @app_commands.describe(inv_type="Investment type: safe, medium, or risky.", amount="Amount of DevilCoins to invest.")
    @app_commands.choices(inv_type=[
        app_commands.Choice(name="Safe (1h, 5-10% guaranteed)",      value="safe"),
        app_commands.Choice(name="Medium (6h, 20-35% / 75% success)", value="medium"),
        app_commands.Choice(name="Risky (24h, 50-80% / 50% success)", value="risky"),
    ])
    async def invest(self, interaction: discord.Interaction, inv_type: str, amount: int):
        await interaction.response.defer(ephemeral=False)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        try:
            result = await self.investments.invest(guild_id, discord_id, username, inv_type, amount)
        except ValueError as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        try:
            avatar_url = interaction.user.display_avatar.with_size(128).url
        except Exception:
            avatar_url = None
        avatar_bytes = await fetch_avatar(avatar_url)

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_invest_card(
            username       = username,
            rank           = result.get("rank", "Forsaken"),
            inv_type       = inv_type,
            type_label     = result["label"],
            amount         = result["amount"],
            maturity_hours = result["maturity_hours"],
            new_balance    = result["new_balance"],
            avatar_bytes   = avatar_bytes,
            skin_id        = result.get("equipped_skin"),
        ))
        card_embed = discord.Embed(color=0xB22222)
        card_embed.set_image(url="attachment://invest_result.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="invest_result.png")
        )

    # ─── /portfolio ────────────────────────────────────────────────────────────

    @app_commands.command(name="portfolio", description="View your active and matured investments.")
    async def portfolio(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        try:
            inv_list = await self.investments.get_portfolio(guild_id, discord_id)
        except Exception as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        # Fetch skin from user record
        user_data = await self.bot.db.upsert_user(guild_id, discord_id, username)
        skin_id   = user_data.get("equipped_skin") or "default"

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_portfolio_card(
            username    = username,
            investments = inv_list,
            skin_id     = skin_id,
        ))
        card_embed = discord.Embed(color=0xFFD700)
        card_embed.set_image(url="attachment://portfolio_result.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="portfolio_result.png")
        )

    # ─── /collect ──────────────────────────────────────────────────────────────

    @app_commands.command(name="collect", description="Collect all matured investments.")
    async def collect(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        try:
            result = await self.investments.collect(guild_id, discord_id)
        except ValueError as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        try:
            avatar_url = interaction.user.display_avatar.with_size(128).url
        except Exception:
            avatar_url = None
        avatar_bytes = await fetch_avatar(avatar_url)

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_collect_card(
            username     = username,
            rank         = result.get("rank", "Forsaken"),
            results      = result["results"],
            total_payout = result["total_payout"],
            new_balance  = result["new_balance"],
            avatar_bytes = avatar_bytes,
            skin_id      = result.get("equipped_skin"),
        ))
        card_embed = discord.Embed(color=0xFFD700)
        card_embed.set_image(url="attachment://collect_result.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="collect_result.png")
        )

    # ─── /withdraw ─────────────────────────────────────────────────────────────

    @app_commands.command(name="withdraw", description="Withdraw all active investments early. A 20% penalty applies.")
    async def withdraw(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        try:
            result = await self.investments.withdraw_early(guild_id, discord_id)
        except ValueError as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        try:
            avatar_url = interaction.user.display_avatar.with_size(128).url
        except Exception:
            avatar_url = None
        avatar_bytes = await fetch_avatar(avatar_url)

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_withdraw_card(
            username     = username,
            rank         = result.get("rank", "Forsaken"),
            results      = result["results"],
            total_payout = result["total_payout"],
            new_balance  = result["new_balance"],
            avatar_bytes = avatar_bytes,
            skin_id      = result.get("equipped_skin"),
        ))
        card_embed = discord.Embed(color=0x6B0000)
        card_embed.set_image(url="attachment://withdraw_result.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="withdraw_result.png")
        )
