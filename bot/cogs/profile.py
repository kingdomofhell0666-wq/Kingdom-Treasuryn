import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from ..services import AuditService
from ..services.cosmetic_service import CosmeticService
from ..utils.embeds import EmbedFactory
from ..ui import IdentityView


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @property
    def audit(self) -> AuditService:
        return self.bot.audit_service

    @property
    def cosmetics(self) -> CosmeticService:
        return self.bot.cosmetic_service

    @app_commands.command(
        name="identity",
        description="View your Kingdom Identity Card, or inspect another soul's.",
    )
    @app_commands.describe(user="The soul whose identity you wish to inspect.")
    async def identity(
        self, interaction: discord.Interaction, user: Optional[discord.Member] = None
    ):
        await interaction.response.defer(ephemeral=False)

        target = user or interaction.user
        is_own_card = target.id == interaction.user.id
        discord_id = str(target.id)
        username = target.display_name

        user_data = await self.db.upsert_user(discord_id, username)
        kingdom_rank = await self.audit.get_kingdom_rank(discord_id)

        avatar_url = None
        try:
            avatar_url = target.display_avatar.url
        except Exception:
            pass

        mention = target.mention if not is_own_card else None

        embed = EmbedFactory.identity(
            user_data=user_data,
            kingdom_rank=kingdom_rank,
            avatar_url=avatar_url,
            mention=mention,
        )
        view = IdentityView(is_own_card=is_own_card)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="wealth", description="Check your current balance.")
    async def wealth(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        user_data = await self.db.upsert_user(discord_id, username)

        embed = EmbedFactory.wealth(user_data)
        await interaction.response.send_message(embed=embed)
