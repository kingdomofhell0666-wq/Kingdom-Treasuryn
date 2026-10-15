import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from ..services import AuditService
from ..services.cosmetic_service import CosmeticService
from ..utils.embeds import EmbedFactory
from ..utils.card_generator import generate_card, fetch_avatar
from ..utils.result_cards import generate_wealth_card
from ..utils.skins import get_skin, detect_rank_from_roles
from ..utils.identity_variant import resolve_identity_card_variant
from ..utils.permissions import (
    IDENTITY_CARD_CHANNEL_ID,
    identity_card_required_embed,
    is_identity_card_exempt,
)
from ..utils.routing import check_routing


class IdentityCardCreateModal(discord.ui.Modal, title="Create your Demon Identity Card"):
    card_name = discord.ui.TextInput(
        label="Nom affiché sur ta carte",
        placeholder="Entre le nom de ton profil Discord",
        required=True,
        min_length=1,
        max_length=32,
    )

    def __init__(self, cog: "ProfileCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        card_name = self.card_name.value.strip()
        if not card_name:
            await interaction.response.send_message(
                "Le nom de la carte ne peut pas être vide.", ephemeral=True
            )
            return
        if interaction.guild is None or interaction.channel_id != IDENTITY_CARD_CHANNEL_ID:
            await interaction.response.send_message(
                embed=identity_card_required_embed(), ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)
        discord_id = str(interaction.user.id)
        if await self.cog.db.has_identity_card(guild_id, discord_id):
            await interaction.response.send_message(
                "Ta carte d’identité existe déjà. Utilise `/identity` pour l’afficher.",
                ephemeral=True,
            )
            return

        await self.cog.db.upsert_user(
            guild_id, discord_id, interaction.user.display_name
        )
        await self.cog.db.set_identity_display_name(guild_id, discord_id, card_name)
        await ProfileCog.identity.callback(self.cog, interaction)


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):           return self.bot.db
    @property
    def audit(self):        return self.bot.audit_service
    @property
    def cosmetics(self):    return self.bot.cosmetic_service

    @app_commands.command(
        name="createid",
        description="Create your Demon Identity Card before using Kingdom Treasury.",
    )
    async def create_identity_card(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.channel_id != IDENTITY_CARD_CHANNEL_ID:
            await interaction.response.send_message(
                embed=identity_card_required_embed(), ephemeral=True
            )
            return

        guild_id = str(interaction.guild.id)
        discord_id = str(interaction.user.id)
        if await self.db.has_identity_card(guild_id, discord_id):
            await interaction.response.send_message(
                "Ta carte d’identité existe déjà. Utilise `/identity` pour l’afficher.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(IdentityCardCreateModal(self))

    @app_commands.command(name="identity", description="View your Kingdom Identity Card, or inspect another soul's.")
    @app_commands.describe(user="The soul whose identity you wish to inspect.")
    async def identity(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=False)

        if not await check_routing(interaction, "identity", getattr(self.bot, "config_service", None)):
            return

        guild_id    = str(interaction.guild_id)
        target      = user or interaction.user
        is_own_card = target.id == interaction.user.id
        discord_id  = str(target.id)
        exempt      = is_identity_card_exempt(interaction)

        if not is_own_card and not exempt:
            if not await self.db.has_identity_card(guild_id, str(interaction.user.id)):
                await interaction.followup.send(
                    embed=identity_card_required_embed(),
                    ephemeral=True,
                )
                return
        if (
            is_own_card
            and not exempt
            and interaction.channel_id != IDENTITY_CARD_CHANNEL_ID
        ):
            await interaction.followup.send(
                embed=identity_card_required_embed(),
                ephemeral=True,
            )
            return

        # The stored rank is the fallback when no economy rank role is present.
        user_data = await self.db.upsert_user(guild_id, discord_id, target.display_name)
        live_rank = detect_rank_from_roles(target.roles) or user_data.get("rank", "Unranked")
        card_display_name = user_data.get("identity_display_name") or target.display_name

        # ── Hierarchy variant — full group + eligibility + classification ────
        member_role_ids = [str(r.id) for r in target.roles]
        card_variant    = resolve_identity_card_variant(member_role_ids, live_rank)

        # ── Kingdom Rank — only for eligible groups (Nobility + Members) ────
        # Shows the user's live weekly rank position (weekly activity → weekly DC
        # earned → eligible rank as tiebreaker).  Non-eligible hierarchy groups
        # (Owners, Royal Family, Council, Legion) receive kingdom_rank=0 which
        # the card renders as "EXEMPT".
        if card_variant.kingdom_rank_eligible:
            kingdom_rank = await self.db.get_weekly_kingdom_rank_position(guild_id, discord_id)
            if kingdom_rank == 0:
                kingdom_rank = 1   # user is in DB but no one ranks above them yet
        else:
            kingdom_rank = 0       # generate_card shows "EXEMPT" for kr_eligible=False

        # ── Equipped cosmetics ───────────────────────────────────────────────
        skin_id        = user_data.get("equipped_skin") or "default"
        skin           = get_skin(skin_id)
        equipped_title = user_data.get("equipped_title") or "Unmarked"
        equipped_relic = user_data.get("equipped_relic") or ""

        equipped_badges = []
        try:
            import json as _json
            equipped_badges = _json.loads(user_data.get("equipped_badges") or "[]")
        except Exception:
            equipped_badges = []

        # ── Avatar bytes ────────────────────────────────────────────────────
        avatar_url = None
        try:
            avatar_url = target.display_avatar.with_size(128).url
        except Exception:
            pass
        avatar_bytes = await fetch_avatar(avatar_url)

        # ── Generate card image ─────────────────────────────────────────────
        try:
            card_buf = generate_card(
                username       = target.name,
                display_name   = card_display_name,
                equipped_title = equipped_title,
                rank           = live_rank,
                balance        = user_data.get("balance", 0),
                kingdom_rank   = kingdom_rank,
                taxes_paid     = user_data.get("taxes_paid", 0),
                skin_id        = skin_id,
                avatar_bytes   = avatar_bytes,
                footer_flavor  = skin.footer_flavor.strip('"'),
                card_variant   = card_variant,
                relic_id       = equipped_relic,
                equipped_badges= equipped_badges,
            )
            card_file = discord.File(card_buf, filename="identity.png")
            embed     = discord.Embed(color=skin.color)
            embed.set_image(url="attachment://identity.png")
            if not is_own_card:
                embed.set_footer(text=f"Identity of {target.display_name}  ·  Kingdom Treasury")
            await interaction.followup.send(embed=embed, file=card_file)
        except Exception:
            import logging
            logging.getLogger("kingdom_treasury").exception("Card generation failed")
            embed = EmbedFactory.identity(
                user_data    = user_data,
                kingdom_rank = kingdom_rank,
                avatar_url   = avatar_url,
                mention      = target.mention if not is_own_card else None,
            )
            await interaction.followup.send(embed=embed)

        if is_own_card and interaction.channel_id == IDENTITY_CARD_CHANNEL_ID:
            await self.db.mark_identity_card_created(guild_id, discord_id)

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

        # Live Discord role wins; otherwise use the stored economy rank.
        live_rank    = detect_rank_from_roles(interaction.user.roles) or user_data.get("rank", "Unranked")
        member_role_ids = [str(r.id) for r in interaction.user.roles]
        card_variant_w  = resolve_identity_card_variant(member_role_ids, live_rank)
        if card_variant_w.kingdom_rank_eligible:
            kingdom_rank = await self.db.get_weekly_kingdom_rank_position(guild_id, discord_id)
            if kingdom_rank == 0:
                kingdom_rank = 1
        else:
            kingdom_rank = 0    # generate_wealth_card renders 0 as "EXEMPT"

        try:
            avatar_url = interaction.user.display_avatar.with_size(128).url
        except Exception:
            avatar_url = None
        avatar_bytes = await fetch_avatar(avatar_url)

        skin_id  = user_data.get("equipped_skin") or "default"

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_wealth_card(
            username     = username,
            rank         = live_rank,
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
