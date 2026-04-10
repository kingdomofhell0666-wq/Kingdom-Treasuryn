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
from ..utils.routing import check_routing


class InvestmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def investments(self) -> InvestmentService:
        return self.bot.investment_service

    @property
    def ledger(self):
        return getattr(self.bot, "ledger_service", None)

    async def _check_frozen(self, interaction: discord.Interaction) -> bool:
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        user = await self.bot.db.get_user(guild_id, discord_id)
        if user and user.get("is_frozen"):
            embed = discord.Embed(
                description="*Cerberus has sealed your ledger.*",
                color=0x0A0A0A,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return True
        return False

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

        if not await check_routing(interaction, "invest", getattr(self.bot, "config_service", None)):
            return
        if await self._check_frozen(interaction):
            return

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

        if self.ledger and result.get("amount", 0) > 0:
            await self.ledger.log(
                action          = "invest",
                amount          = result["amount"],
                from_label      = f"<@{discord_id}>",
                to_label        = "Infernal Markets",
                guild_id        = guild_id,
                from_discord_id = discord_id,
                wallet_before   = result["new_balance"] + result["amount"],
                wallet_after    = result["new_balance"],
                action_type     = "invest",
            )

    # ─── /portfolio ────────────────────────────────────────────────────────────

    @app_commands.command(name="portfolio", description="View your active and matured investments.")
    async def portfolio(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        if not await check_routing(interaction, "portfolio", getattr(self.bot, "config_service", None)):
            return

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

        if not await check_routing(interaction, "collect", getattr(self.bot, "config_service", None)):
            return
        if await self._check_frozen(interaction):
            return

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

        if self.ledger and result.get("total_payout", 0) > 0:
            await self.ledger.log(
                action          = "collect",
                amount          = result["total_payout"],
                from_label      = "Infernal Markets",
                to_label        = f"<@{discord_id}>",
                guild_id        = guild_id,
                from_discord_id = discord_id,
                wallet_after    = result["new_balance"],
                action_type     = "grind",
            )

    # ─── /withdraw ─────────────────────────────────────────────────────────────

    @app_commands.command(name="withdraw", description="Withdraw all active investments early. A 20% penalty applies.")
    async def withdraw(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        if not await check_routing(interaction, "withdraw", getattr(self.bot, "config_service", None)):
            return
        if await self._check_frozen(interaction):
            return

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

        if self.ledger and result.get("total_payout", 0) > 0:
            await self.ledger.log(
                action          = "withdraw",
                amount          = result["total_payout"],
                from_label      = "Infernal Markets (Early)",
                to_label        = f"<@{discord_id}>",
                guild_id        = guild_id,
                from_discord_id = discord_id,
                wallet_after    = result["new_balance"],
                action_type     = "grind",
            )
