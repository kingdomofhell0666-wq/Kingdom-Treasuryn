import discord
from discord import app_commands
from discord.ext import commands

from ..services.blackmarket_service import BlackMarketService
from ..utils.embeds import EmbedFactory
from ..ui import BlackMarketView


class BlackMarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def market(self) -> BlackMarketService:
        return self.bot.blackmarket_service

    # ─── /blackmarket ─────────────────────────────────────────

    @app_commands.command(
        name="blackmarket",
        description="Browse forbidden items of power. Rotates every 6 hours.",
    )
    async def blackmarket(self, interaction: discord.Interaction):
        items = self.market.get_active_items()

        async def buy_callback(inter: discord.Interaction, item_id: int):
            discord_id = str(inter.user.id)
            username = inter.user.display_name
            try:
                result = await self.market.purchase(discord_id, username, item_id)
            except ValueError as e:
                embed = EmbedFactory.error(str(e))
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            embed = EmbedFactory.blackmarket_purchase(
                item=result["item"],
                cost=result["cost"],
                new_balance=result["new_balance"],
                old_risk=result["old_risk"],
                new_risk=result["new_risk"],
                risk_delta=result["risk_delta"],
            )
            await inter.response.send_message(embed=embed, ephemeral=True)

        view = BlackMarketView(items, buy_callback)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
