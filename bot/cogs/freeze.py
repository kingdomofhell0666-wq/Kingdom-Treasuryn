"""
Kingdom Treasury — /freeze and /unfreeze commands.
"""
import discord
from discord import app_commands
from discord.ext import commands

from ..utils.permissions import (
    is_freeze_authorized,
    is_admin_user,
    is_freeze_exempt,
    denied_freeze,
    denied_unfreeze,
)

_ICE  = 0x00BFFF
_GOLD = 0xFFD700


class FreezeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @property
    def ledger(self):
        return getattr(self.bot, "ledger_service", None)

    # ── /freeze ───────────────────────────────────────────────────────────────

    @app_commands.command(
        name="freeze",
        description="[Staff] Seal a user's ledger — blocking all economy use.",
    )
    @app_commands.describe(
        user   = "The soul whose ledger will be sealed.",
        reason = "Optional reason for the freeze.",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def freeze(
        self,
        interaction: discord.Interaction,
        user:   discord.Member,
        reason: str = "",
    ):
        await interaction.response.defer(ephemeral=True)

        if not is_freeze_authorized(interaction):
            await interaction.followup.send(embed=denied_freeze(), ephemeral=True)
            return

        if is_freeze_exempt(user):
            await interaction.followup.send(
                embed=discord.Embed(
                    description="*The ledger of Kingdom staff cannot be sealed.*",
                    color=0x0A0A0A,
                ).set_footer(text="Kingdom Treasury  ·  Kingdom of Hell"),
                ephemeral=True,
            )
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)

        await self.db.upsert_user(guild_id, discord_id, user.display_name)
        await self.db.freeze_user(
            guild_id   = guild_id,
            discord_id = discord_id,
            reason     = reason or "Sealed by staff",
            frozen_by  = str(interaction.user.id),
        )

        embed = discord.Embed(
            title       = "❄️  Ledger Sealed",
            description = (
                f"*The ledger of {user.mention} has been sealed.*\n"
                f"*They may no longer conduct economy operations.*"
            ),
            color = _ICE,
        )
        if reason:
            embed.add_field(name="Reason",    value=reason,                    inline=False)
        embed.add_field(name="Sealed by",     value=interaction.user.mention,  inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger:
            await self.ledger.log_freeze(
                target   = user,
                executor = interaction.user.mention,
                reason   = reason,
                auto     = False,
            )

    # ── /unfreeze ─────────────────────────────────────────────────────────────

    @app_commands.command(
        name="unfreeze",
        description="[Admin] Lift the seal from a user's ledger.",
    )
    @app_commands.describe(user="The soul whose ledger seal will be lifted.")
    @app_commands.default_permissions(administrator=True)
    async def unfreeze(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_unfreeze(), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)

        await self.db.upsert_user(guild_id, discord_id, user.display_name)
        await self.db.unfreeze_user(guild_id, discord_id)

        embed = discord.Embed(
            title       = "🔓  Seal Lifted",
            description = (
                f"*The ledger of {user.mention} has been reopened.*\n"
                f"*Cerberus has lifted the seal.*"
            ),
            color = _GOLD,
        )
        embed.add_field(name="Lifted by", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger:
            await self.ledger.log_unfreeze(
                target   = user,
                executor = interaction.user.mention,
            )
