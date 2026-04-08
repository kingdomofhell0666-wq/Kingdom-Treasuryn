import discord
from discord import app_commands
from discord.ext import commands

from ..services.investment_service import InvestmentService, INVESTMENT_TYPES
from ..utils.embeds import EmbedFactory


class InvestmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def investments(self) -> InvestmentService:
        return self.bot.investment_service

    # ─── /invest ──────────────────────────────────────────────

    @app_commands.command(
        name="invest",
        description="Commit DevilCoins to the infernal markets. Choose your risk.",
    )
    @app_commands.describe(
        inv_type="Investment type: safe, medium, or risky.",
        amount="Amount of DevilCoins to invest.",
    )
    @app_commands.choices(inv_type=[
        app_commands.Choice(name="Safe (1h, 5-10% guaranteed)", value="safe"),
        app_commands.Choice(name="Medium (6h, 20-35% / 75% success)", value="medium"),
        app_commands.Choice(name="Risky (24h, 50-80% / 50% success)", value="risky"),
    ])
    async def invest(
        self,
        interaction: discord.Interaction,
        inv_type: str,
        amount: int,
    ):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        try:
            result = await self.investments.invest(discord_id, username, inv_type, amount)
        except ValueError as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.investment_opened(result)
        await interaction.followup.send(embed=embed)

    # ─── /portfolio ───────────────────────────────────────────

    @app_commands.command(
        name="portfolio",
        description="View your active and matured investments.",
    )
    async def portfolio(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)

        try:
            investments = await self.investments.get_portfolio(discord_id)
        except Exception as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.portfolio(investments)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ─── /collect ─────────────────────────────────────────────

    @app_commands.command(
        name="collect",
        description="Collect all matured investments. The Kingdom renders its verdict.",
    )
    async def collect(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)

        try:
            result = await self.investments.collect(discord_id)
        except ValueError as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.investment_collected(result)
        await interaction.followup.send(embed=embed)

    # ─── /withdraw ────────────────────────────────────────────

    @app_commands.command(
        name="withdraw",
        description="Withdraw all active investments early. A 20% penalty applies.",
    )
    async def withdraw(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)

        try:
            result = await self.investments.withdraw_early(discord_id)
        except ValueError as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.investment_withdrawn(result)
        await interaction.followup.send(embed=embed)
