import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from ..services import AuditService
from ..services.cosmetic_service import CosmeticService
from ..utils.embeds import EmbedFactory
from ..utils.card_generator import generate_card, fetch_avatar
from ..utils.skins import get_skin
from ..ui import IdentityView


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):              return self.bot.db
    @property
    def audit(self):           return self.bot.audit_service
    @property
    def cosmetics(self):       return self.bot.cosmetic_service

    @app_commands.command(name="identity", description="View your Kingdom Identity Card, or inspect another soul's.")
    @app_commands.describe(user="The soul whose identity you wish to inspect.")
    async def identity(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=False)

        guild_id     = str(interaction.guild_id)
        target       = user or interaction.user
        is_own_card  = target.id == interaction.user.id
        discord_id   = str(target.id)
        username     = target.display_name

        user_data    = await self.db.upsert_user(guild_id, discord_id, username)
        kingdom_rank = await self.audit.get_kingdom_rank(guild_id, discord_id)

        skin_id        = user_data.get("equipped_skin") or "default"
        skin           = get_skin(skin_id)
        equipped_title = user_data.get("equipped_title") or "Unmarked"

        import json as _json
        try:
            badges = _json.loads(user_data.get("owned_badges") or "[]")
        except Exception:
            badges = []

        risk       = user_data.get("risk_score", 0)
        taxes      = user_data.get("taxes_paid", 0)
        if risk >= 51:
            audit_state = "flagged"
        elif risk <= 20 and taxes > 0:
            audit_state = "cleared"
        else:
            audit_state = "neutral"

        avatar_url = None
        try:
            avatar_url = target.display_avatar.with_size(128).url
        except Exception:
            pass
        avatar_bytes = await fetch_avatar(avatar_url)

        try:
            card_buf  = generate_card(
                username=target.name,
                display_name=target.display_name,
                equipped_title=equipped_title,
                rank=user_data.get("rank", "Forsaken"),
                balance=user_data.get("balance", 0),
                kingdom_rank=kingdom_rank,
                taxes_paid=user_data.get("taxes_paid", 0),
                risk_score=risk,
                skin_id=skin_id,
                avatar_bytes=avatar_bytes,
                footer_flavor=skin.footer_flavor.strip('"'),
                badges=badges,
                audit_state=audit_state,
            )
            card_file = discord.File(card_buf, filename="identity.png")
            embed     = discord.Embed(color=skin.color)
            embed.set_image(url="attachment://identity.png")
            if not is_own_card:
                embed.set_footer(text=f"Identity of {username}  ·  Kingdom Treasury")
            view = IdentityView(is_own_card=is_own_card)
            await interaction.followup.send(embed=embed, file=card_file, view=view)
        except Exception:
            import logging
            logging.getLogger("kingdom_treasury").exception("Card generation failed")
            embed = EmbedFactory.identity(
                user_data=user_data, kingdom_rank=kingdom_rank,
                avatar_url=avatar_url,
                mention=target.mention if not is_own_card else None,
            )
            view = IdentityView(is_own_card=is_own_card)
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="wealth", description="Check your current balance.")
    async def wealth(self, interaction: discord.Interaction):
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name
        user_data  = await self.db.upsert_user(guild_id, discord_id, username)
        await interaction.response.send_message(embed=EmbedFactory.wealth(user_data))
