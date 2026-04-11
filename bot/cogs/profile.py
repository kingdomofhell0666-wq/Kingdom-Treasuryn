import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from ..services import AuditService
from ..services.cosmetic_service import CosmeticService
from ..utils.embeds import EmbedFactory
from ..utils.card_generator import generate_card, fetch_avatar
from ..utils.result_cards import generate_wealth_card
from ..utils.skins import get_skin
from ..utils.identity_variant import resolve_identity_card_variant
from ..utils.routing import check_routing


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

        if not await check_routing(interaction, "identity", getattr(self.bot, "config_service", None)):
            return

        guild_id     = str(interaction.guild_id)
        target       = user or interaction.user
        is_own_card  = target.id == interaction.user.id
        discord_id   = str(target.id)
        username     = target.display_name

        user_data    = await self.db.upsert_user(guild_id, discord_id, username)
        kingdom_rank = await self.audit.get_kingdom_rank(guild_id, discord_id)

        skin_id         = user_data.get("equipped_skin") or "default"
        skin            = get_skin(skin_id)
        equipped_title  = user_data.get("equipped_title") or "Unmarked"
        equipped_relic  = user_data.get("equipped_relic") or ""
        equipped_badges = []
        try:
            import json as _json
            equipped_badges = _json.loads(user_data.get("equipped_badges") or "[]")
        except Exception:
            equipped_badges = []

        public_rank = user_data.get("rank", "Forsaken")
        member_role_ids = [str(r.id) for r in target.roles]
        card_variant = resolve_identity_card_variant(member_role_ids, public_rank)

        risk  = user_data.get("risk_score", 0)
        taxes = user_data.get("taxes_paid", 0)
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
                rank=public_rank,
                balance=user_data.get("balance", 0),
                kingdom_rank=kingdom_rank,
                taxes_paid=user_data.get("taxes_paid", 0),
                risk_score=risk,
                skin_id=skin_id,
                avatar_bytes=avatar_bytes,
                footer_flavor=skin.footer_flavor.strip('"'),
                audit_state=audit_state,
                card_variant=card_variant,
                relic_id=equipped_relic,
                equipped_badges=equipped_badges,
            )
            card_file = discord.File(card_buf, filename="identity.png")
            embed     = discord.Embed(color=skin.color)
            embed.set_image(url="attachment://identity.png")
            if not is_own_card:
                embed.set_footer(text=f"Identity of {username}  ·  Kingdom Treasury")
            await interaction.followup.send(embed=embed, file=card_file)
        except Exception:
            import logging
            logging.getLogger("kingdom_treasury").exception("Card generation failed")
            embed = EmbedFactory.identity(
                user_data=user_data, kingdom_rank=kingdom_rank,
                avatar_url=avatar_url,
                mention=target.mention if not is_own_card else None,
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="wealth", description="Check your current balance.")
    async def wealth(self, interaction: discord.Interaction):
        import asyncio
        await interaction.response.defer(ephemeral=False)

        if not await check_routing(interaction, "wealth", getattr(self.bot, "config_service", None)):
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name
        user_data  = await self.db.upsert_user(guild_id, discord_id, username)

        kingdom_rank = await self.audit.get_kingdom_rank(guild_id, discord_id)

        try:
            avatar_url = interaction.user.display_avatar.with_size(128).url
        except Exception:
            avatar_url = None
        avatar_bytes = await fetch_avatar(avatar_url)

        skin_id = user_data.get("equipped_skin") or "default"

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_wealth_card(
            username     = username,
            rank         = user_data.get("rank", "Forsaken"),
            balance      = user_data.get("balance", 0),
            taxes_paid   = user_data.get("taxes_paid", 0),
            kingdom_rank = kingdom_rank,
            risk_score   = user_data.get("risk_score", 0),
            avatar_bytes = avatar_bytes,
            skin_id      = skin_id,
        ))
        card_embed = discord.Embed(color=0xFFD700)
        card_embed.set_image(url="attachment://wealth_result.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="wealth_result.png")
        )
