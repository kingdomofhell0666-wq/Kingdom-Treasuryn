import discord
from discord import app_commands
from discord.ext import commands

from ..services.blackmarket_service import BlackMarketService
from ..utils.embeds import EmbedFactory
from ..utils.routing import check_routing
from ..ui import BlackMarketView


class BlackMarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def market(self) -> BlackMarketService:
        return self.bot.blackmarket_service

    @app_commands.command(name="blackmarket", description="Browse forbidden items of power. Rotates every 6 hours.")
    async def blackmarket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await check_routing(interaction, "blackmarket", getattr(self.bot, "config_service", None)):
            return

        guild_id = str(interaction.guild_id)
        items    = self.market.get_active_items()

        async def buy_callback(inter: discord.Interaction, item_id: int):
            discord_id = str(inter.user.id)
            username   = inter.user.display_name

            # Freeze gate
            user_row = await self.bot.db.get_user(guild_id, discord_id)
            if user_row and user_row.get("is_frozen"):
                frozen_embed = discord.Embed(
                    description="*Cerberus has sealed your ledger.*",
                    color=0x0A0A0A,
                )
                await inter.response.send_message(embed=frozen_embed, ephemeral=True)
                return

            try:
                result = await self.market.purchase(guild_id, discord_id, username, item_id)
            except ValueError as e:
                await inter.response.send_message(embed=EmbedFactory.error(str(e)), ephemeral=True)
                return
            embed = EmbedFactory.blackmarket_purchase(
                item=result["item"], cost=result["cost"], new_balance=result["new_balance"],
                old_risk=result["old_risk"], new_risk=result["new_risk"], risk_delta=result["risk_delta"],
            )
            await inter.response.send_message(embed=embed, ephemeral=True)

        view  = BlackMarketView(items, buy_callback)
        embed = view.build_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
