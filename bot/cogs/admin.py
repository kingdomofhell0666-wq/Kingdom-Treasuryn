"""
Kingdom Treasury — Admin Economy Commands
Requires: bot owner | server owner | administrator permission
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from ..utils.result_cards import generate_treasury_card
from ..utils.card_generator import fetch_avatar

_VOID   = 0x0A0A0A
_CRIMSON = 0xB22222
_GOLD    = 0xFFD700


# ─── Permission gate ──────────────────────────────────────────────────────────

async def _is_admin(interaction: discord.Interaction) -> bool:
    try:
        app_info = await interaction.client.application_info()
        if interaction.user.id == app_info.owner.id:
            return True
    except Exception:
        pass
    if not interaction.guild:
        return False
    if interaction.user.id == interaction.guild.owner_id:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    return False


def _denied() -> discord.Embed:
    return discord.Embed(
        title="🔒  Access Denied",
        description="*You do not hold authority over the Treasury.*",
        color=_VOID,
    )


def _err(msg: str) -> discord.Embed:
    return discord.Embed(
        title="⚠  Invalid Decree",
        description=f"*{msg}*",
        color=_CRIMSON,
    )


# ─── Cog ──────────────────────────────────────────────────────────────────────

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    # ── /add-dc ───────────────────────────────────────────────────────────────

    @app_commands.command(name="add-dc", description="[Admin] Grant DevilCoins to a user.")
    @app_commands.describe(user="The soul to receive the grant.", amount="Amount to grant.")
    async def add_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return
        if amount <= 0:
            await interaction.followup.send(embed=_err("Amount must be greater than zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        await self.db.upsert_user(guild_id, discord_id, user.display_name)
        await self.db.update_balance(guild_id, discord_id, amount)
        updated = await self.db.get_user(guild_id, discord_id)
        new_bal = updated["balance"] if updated else 0

        await self.db.log_transaction(
            guild_id, "admin_add_dc",
            f"admin:{admin_id}", f"user:{discord_id}",
            amount, f"Admin grant to {user.display_name}",
        )

        embed = discord.Embed(
            title="⚖  Treasury Decree — Funds Granted",
            description=f"*The Treasury has granted additional wealth to {user.mention}.*",
            color=_GOLD,
        )
        embed.add_field(name="Granted",      value=f"**+{amount:,} DC**",  inline=True)
        embed.add_field(name="New Balance",  value=f"**{new_bal:,} DC**",   inline=True)
        embed.add_field(name="Recipient",    value=user.mention,             inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /remove-dc ────────────────────────────────────────────────────────────

    @app_commands.command(name="remove-dc", description="[Admin] Seize DevilCoins from a user.")
    @app_commands.describe(user="The soul to seize from.", amount="Amount to seize.")
    async def remove_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return
        if amount <= 0:
            await interaction.followup.send(embed=_err("Amount must be greater than zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        target      = await self.db.upsert_user(guild_id, discord_id, user.display_name)
        current_bal = target.get("balance", 0)
        actual      = min(amount, current_bal)

        await self.db.set_balance(guild_id, discord_id, max(0, current_bal - amount))
        updated = await self.db.get_user(guild_id, discord_id)
        new_bal = updated["balance"] if updated else 0

        await self.db.log_transaction(
            guild_id, "admin_remove_dc",
            f"user:{discord_id}", f"admin:{admin_id}",
            actual, f"Admin seizure from {user.display_name}",
        )

        embed = discord.Embed(
            title="☠  Treasury Decree — Funds Seized",
            description=f"*DevilCoins have been seized from {user.mention}.*",
            color=_CRIMSON,
        )
        embed.add_field(name="Seized",       value=f"**−{actual:,} DC**",   inline=True)
        embed.add_field(name="New Balance",  value=f"**{new_bal:,} DC**",    inline=True)
        embed.add_field(name="Target",       value=user.mention,              inline=True)
        if actual < amount:
            embed.add_field(
                name="⚠  Clamped",
                value=f"Wallet only held **{current_bal:,} DC** — balance floored to 0.",
                inline=False,
            )
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /set-dc ───────────────────────────────────────────────────────────────

    @app_commands.command(name="set-dc", description="[Admin] Set a user's wallet to an exact amount.")
    @app_commands.describe(user="The soul whose ledger will be rewritten.", amount="The exact new balance.")
    async def set_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return
        if amount < 0:
            await interaction.followup.send(embed=_err("Balance cannot be set below zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        target  = await self.db.upsert_user(guild_id, discord_id, user.display_name)
        old_bal = target.get("balance", 0)
        delta   = amount - old_bal

        await self.db.set_balance(guild_id, discord_id, amount)
        await self.db.log_transaction(
            guild_id, "admin_set_dc",
            f"admin:{admin_id}", f"user:{discord_id}",
            abs(delta), f"Admin ledger rewrite for {user.display_name} → {amount:,} DC",
        )

        embed = discord.Embed(
            title="📜  Treasury Decree — Ledger Rewritten",
            description=f"*The ledger has been rewritten for {user.mention}.*",
            color=_GOLD,
        )
        embed.add_field(name="Previous",    value=f"**{old_bal:,} DC**",  inline=True)
        embed.add_field(name="New Balance", value=f"**{amount:,} DC**",   inline=True)
        embed.add_field(name="Target",      value=user.mention,            inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /reset-user-economy ───────────────────────────────────────────────────

    @app_commands.command(name="reset-user-economy", description="[Admin] Fully reset a user's economy in this server.")
    @app_commands.describe(user="The soul whose record will be erased.")
    async def reset_user_economy(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        # Ensure user row exists before resetting
        await self.db.upsert_user(guild_id, discord_id, user.display_name)
        await self.db.admin_reset_user(guild_id, discord_id)
        await self.db.log_transaction(
            guild_id, "admin_reset_user",
            f"admin:{admin_id}", f"user:{discord_id}",
            0, f"Full economy reset for {user.display_name}",
        )

        embed = discord.Embed(
            title="💀  Royal Decree — Account Reset",
            description=(
                f"*By royal decree, the record of {user.mention} has been erased.*\n"
                f"*The Kingdom remembers nothing.*"
            ),
            color=_VOID,
        )
        embed.add_field(name="Wallet",      value="**0 DC**",       inline=True)
        embed.add_field(name="Rank",        value="**Forsaken**",   inline=True)
        embed.add_field(name="Cooldowns",   value="**Cleared**",    inline=True)
        embed.add_field(name="Risk Score",  value="**0**",          inline=True)
        embed.add_field(name="Investments", value="**Voided**",     inline=True)
        embed.add_field(name="Perks",       value="**Removed**",    inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /treasury ─────────────────────────────────────────────────────────────

    @app_commands.command(name="treasury", description="View the total reserves of the Kingdom Treasury.")
    async def treasury(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        guild_id = str(interaction.guild_id)
        balance  = await self.bot.treasury_service.get_balance(guild_id)

        # Use caller's skin for the card theme
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name
        user_data  = await self.db.upsert_user(guild_id, discord_id, username)
        skin_id    = user_data.get("equipped_skin") or "default"

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_treasury_card(
            balance = balance,
            skin_id = skin_id,
        ))
        card_embed = discord.Embed(color=_GOLD)
        card_embed.set_image(url="attachment://treasury.png")
        await interaction.followup.send(
            embed=card_embed, file=discord.File(card_buf, filename="treasury.png")
        )
