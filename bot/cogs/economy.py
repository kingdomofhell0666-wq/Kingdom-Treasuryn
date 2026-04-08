import discord
from discord import app_commands
from discord.ext import commands

from ..services import EconomyService, CooldownService, AuditService
from ..services.rank_service import RankService
from ..utils.embeds import EmbedFactory
from ..ui import MarketView


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @property
    def economy(self) -> EconomyService:
        return self.bot.economy_service

    @property
    def cooldown(self) -> CooldownService:
        return self.bot.cooldown_service

    @property
    def audit(self) -> AuditService:
        return self.bot.audit_service

    @property
    def rank_service(self) -> RankService:
        return self.bot.rank_service

    @app_commands.command(name="grind", description="Descend into the mines and extract DevilCoins.")
    async def grind(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        ready, remaining = await self.cooldown.check_cooldown(discord_id, "grind")
        if not ready:
            remaining_str = self.cooldown.format_remaining(remaining)
            embed = EmbedFactory.cooldown_error("grind", remaining_str)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(discord_id, "grind")

        try:
            result = await self.economy.grind(discord_id, username)
        except Exception as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.grind_success(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="tribute", description="Receive tribute from the realm. Once per day.")
    async def tribute(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        ready, remaining = await self.cooldown.check_cooldown(discord_id, "tribute")
        if not ready:
            remaining_str = self.cooldown.format_remaining(remaining)
            embed = EmbedFactory.cooldown_error("tribute", remaining_str)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(discord_id, "tribute")

        try:
            result = await self.economy.tribute(discord_id, username)
        except Exception as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.tribute_success(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="transfer", description="Transfer DevilCoins to another soul.")
    @app_commands.describe(
        recipient="The soul to receive the transfer.",
        amount="Amount of DevilCoins to transfer.",
    )
    async def transfer(
        self,
        interaction: discord.Interaction,
        recipient: discord.Member,
        amount: int,
    ):
        await interaction.response.defer(ephemeral=False)

        sender_id = str(interaction.user.id)
        sender_name = interaction.user.display_name
        recipient_id = str(recipient.id)
        recipient_name = recipient.display_name

        try:
            result = await self.economy.transfer(
                sender_id, sender_name, recipient_id, recipient_name, amount
            )
        except ValueError as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.transfer_success(
            sender_name,
            recipient_name,
            result["amount"],
            result["tax_on_transfer"],
            result["net_to_recipient"],
            result["sender_balance"],
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="market", description="View the Kingdom's rank market.")
    async def market(self, interaction: discord.Interaction):
        purchasable = self.rank_service.get_purchasable_ranks()
        view = MarketView(purchasable)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="ascend", description="Ascend to a higher rank in the Kingdom.")
    @app_commands.describe(rank_name="The rank you wish to ascend to.")
    async def ascend(self, interaction: discord.Interaction, rank_name: str):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        if not self.rank_service.rank_exists(rank_name):
            embed = EmbedFactory.error(f"The rank '{rank_name}' is not recognized by the Kingdom.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if not self.rank_service.is_purchasable(rank_name):
            embed = EmbedFactory.error("That rank cannot be purchased. It is beyond commerce.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        cost = self.rank_service.get_rank_cost(rank_name)
        user = await self.db.upsert_user(discord_id, username)

        if user["balance"] < cost:
            needed = cost - user["balance"]
            embed = EmbedFactory.error(
                f"Your coffers are insufficient. You require {needed:,} more DC to ascend to **{rank_name}**."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        from ..services.transaction_service import TransactionService
        tx_service = TransactionService(self.db)
        await tx_service.ascension_payment(discord_id, rank_name, cost)

        updated_user = await self.db.get_user(discord_id)
        new_balance = updated_user["balance"] if updated_user else 0

        embed = EmbedFactory.ascend_success(rank_name, cost, new_balance)
        await interaction.followup.send(embed=embed)
