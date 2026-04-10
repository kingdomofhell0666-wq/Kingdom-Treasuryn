"""
Kingdom Treasury — Admin Economy Commands

Permission tiers (enforced at Discord-level visibility AND backend):
  • Admin-only  : /add-dc  /set-dc  /reset-user-economy
                  /treasury-add  /treasury-remove  /treasury-set
                  /unfreeze
  • Kingdom staff (Sovereign→Legates): /treasury  /mission  /freeze
  • Extended  (+ Centurion/Legionnaires): /remove-dc
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from ..utils.permissions import (
    is_admin_user,
    is_extended_staff,
    is_kingdom_or_admin,
    denied_generic,
)
from ..utils.result_cards import generate_treasury_card
from ..utils.card_generator import fetch_avatar

_VOID    = 0x0A0A0A
_CRIMSON = 0xB22222
_GOLD    = 0xFFD700


def _err(msg: str) -> discord.Embed:
    return discord.Embed(
        title       = "⚠  Invalid Decree",
        description = f"*{msg}*",
        color       = _CRIMSON,
    )


# ─── Cog ──────────────────────────────────────────────────────────────────────

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @property
    def ledger(self):
        return getattr(self.bot, "ledger_service", None)

    # ── /add-dc ───────────────────────────────────────────────────────────────

    @app_commands.command(name="add-dc", description="[Admin] Grant DevilCoins to a user.")
    @app_commands.describe(user="The soul to receive the grant.", amount="Amount to grant.")
    @app_commands.default_permissions(administrator=True)
    async def add_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return
        if amount <= 0:
            await interaction.followup.send(embed=_err("Amount must be greater than zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        u_before = await self.db.upsert_user(guild_id, discord_id, user.display_name)
        bal_before = u_before.get("balance", 0)
        await self.db.update_balance(guild_id, discord_id, amount)
        updated  = await self.db.get_user(guild_id, discord_id)
        new_bal  = updated["balance"] if updated else 0

        await self.db.log_transaction(
            guild_id, "admin_add_dc",
            f"admin:{admin_id}", f"user:{discord_id}",
            amount, f"Admin grant to {user.display_name}",
        )

        embed = discord.Embed(
            title       = "⚖  Treasury Decree — Funds Granted",
            description = f"*The Treasury has granted additional wealth to {user.mention}.*",
            color       = _GOLD,
        )
        embed.add_field(name="Granted",     value=f"**+{amount:,} DC**",  inline=True)
        embed.add_field(name="New Balance", value=f"**{new_bal:,} DC**",   inline=True)
        embed.add_field(name="Recipient",   value=user.mention,             inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger:
            await self.ledger.log(
                action          = "add_dc",
                amount          = amount,
                from_label      = f"Treasury (Admin {interaction.user.display_name})",
                to_label        = f"<@{discord_id}>",
                guild_id        = guild_id,
                wallet_before   = bal_before,
                wallet_after    = new_bal,
                action_type     = "treasury",
            )

    # ── /remove-dc ────────────────────────────────────────────────────────────

    @app_commands.command(name="remove-dc", description="[Staff] Seize DevilCoins from a user.")
    @app_commands.describe(user="The soul to seize from.", amount="Amount to seize.")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not (is_extended_staff(interaction) or is_admin_user(interaction)):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
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
            title       = "☠  Treasury Decree — Funds Seized",
            description = f"*DevilCoins have been seized from {user.mention}.*",
            color       = _CRIMSON,
        )
        embed.add_field(name="Seized",      value=f"**−{actual:,} DC**",  inline=True)
        embed.add_field(name="New Balance", value=f"**{new_bal:,} DC**",   inline=True)
        embed.add_field(name="Target",      value=user.mention,             inline=True)
        if actual < amount:
            embed.add_field(
                name    = "⚠  Clamped",
                value   = f"Wallet only held **{current_bal:,} DC** — balance floored to 0.",
                inline  = False,
            )
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger and actual > 0:
            await self.ledger.log(
                action          = "remove_dc",
                amount          = actual,
                from_label      = f"<@{discord_id}>",
                to_label        = f"Kingdom Void (Admin {interaction.user.display_name})",
                guild_id        = guild_id,
                from_discord_id = discord_id,
                wallet_before   = current_bal,
                wallet_after    = new_bal,
                action_type     = "transfer",
            )

    # ── /set-dc ───────────────────────────────────────────────────────────────

    @app_commands.command(name="set-dc", description="[Admin] Set a user's wallet to an exact amount.")
    @app_commands.describe(user="The soul whose ledger will be rewritten.", amount="The exact new balance.")
    @app_commands.default_permissions(administrator=True)
    async def set_dc(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
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
            title       = "📜  Treasury Decree — Ledger Rewritten",
            description = f"*The ledger has been rewritten for {user.mention}.*",
            color       = _GOLD,
        )
        embed.add_field(name="Previous",    value=f"**{old_bal:,} DC**",  inline=True)
        embed.add_field(name="New Balance", value=f"**{amount:,} DC**",   inline=True)
        embed.add_field(name="Target",      value=user.mention,            inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /reset-user-economy ───────────────────────────────────────────────────

    @app_commands.command(name="reset-user-economy", description="[Admin] Fully reset a user's economy in this server.")
    @app_commands.describe(user="The soul whose record will be erased.")
    @app_commands.default_permissions(administrator=True)
    async def reset_user_economy(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)
        admin_id   = str(interaction.user.id)

        await self.db.upsert_user(guild_id, discord_id, user.display_name)
        await self.db.admin_reset_user(guild_id, discord_id)
        await self.db.log_transaction(
            guild_id, "admin_reset_user",
            f"admin:{admin_id}", f"user:{discord_id}",
            0, f"Full economy reset for {user.display_name}",
        )

        embed = discord.Embed(
            title       = "💀  Royal Decree — Account Reset",
            description = (
                f"*By royal decree, the record of {user.mention} has been erased.*\n"
                f"*The Kingdom remembers nothing.*"
            ),
            color = _VOID,
        )
        embed.add_field(name="Wallet",     value="**0 DC**",     inline=True)
        embed.add_field(name="Rank",       value="**Forsaken**", inline=True)
        embed.add_field(name="Cooldowns",  value="**Cleared**",  inline=True)
        embed.add_field(name="Risk Score", value="**0**",        inline=True)
        embed.add_field(name="Investments",value="**Voided**",   inline=True)
        embed.add_field(name="Perks",      value="**Removed**",  inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /treasury ─────────────────────────────────────────────────────────────

    @app_commands.command(name="treasury", description="View the total reserves of the Kingdom Treasury.")
    @app_commands.default_permissions(manage_guild=True)
    async def treasury(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not is_kingdom_or_admin(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        balance   = await self.bot.treasury_service.get_balance(guild_id)
        user_data = await self.db.upsert_user(guild_id, discord_id, username)
        skin_id   = user_data.get("equipped_skin") or "default"

        loop     = asyncio.get_event_loop()
        card_buf = await loop.run_in_executor(None, lambda: generate_treasury_card(
            balance = balance,
            skin_id = skin_id,
        ))
        card_embed = discord.Embed(color=_GOLD)
        card_embed.set_image(url="attachment://treasury.png")
        await interaction.followup.send(
            embed=card_embed,
            file=discord.File(card_buf, filename="treasury.png"),
            ephemeral=False,
        )

    # ── /treasury-add ─────────────────────────────────────────────────────────

    @app_commands.command(name="treasury-add", description="[Admin] Add funds directly to the Kingdom Treasury.")
    @app_commands.describe(amount="Amount to deposit into the Treasury.", note="Optional note.")
    @app_commands.default_permissions(administrator=True)
    async def treasury_add(self, interaction: discord.Interaction, amount: int, note: str = ""):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return
        if amount <= 0:
            await interaction.followup.send(embed=_err("Amount must be greater than zero."), ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        bal_before = await self.bot.treasury_service.get_balance(guild_id)
        await self.bot.treasury_service.deposit(guild_id, amount, note or "Admin treasury deposit")
        bal_after = await self.bot.treasury_service.get_balance(guild_id)

        embed = discord.Embed(
            title       = "⚖  Treasury Decree — Funds Added",
            description = f"*{amount:,} DC has been added to the Kingdom Treasury.*",
            color       = _GOLD,
        )
        embed.add_field(name="Added",    value=f"**+{amount:,} DC**",  inline=True)
        embed.add_field(name="Previous", value=f"**{bal_before:,} DC**", inline=True)
        embed.add_field(name="New",      value=f"**{bal_after:,} DC**",  inline=True)
        if note:
            embed.add_field(name="Note", value=note, inline=False)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger:
            await self.ledger.log(
                action           = "treasury_add",
                amount           = amount,
                from_label       = f"Admin ({interaction.user.display_name})",
                to_label         = "Kingdom Treasury",
                guild_id         = guild_id,
                treasury_before  = bal_before,
                treasury_after   = bal_after,
                action_type      = "treasury",
            )

    # ── /treasury-remove ──────────────────────────────────────────────────────

    @app_commands.command(name="treasury-remove", description="[Admin] Remove funds from the Kingdom Treasury.")
    @app_commands.describe(amount="Amount to withdraw from the Treasury.", note="Optional note.")
    @app_commands.default_permissions(administrator=True)
    async def treasury_remove(self, interaction: discord.Interaction, amount: int, note: str = ""):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return
        if amount <= 0:
            await interaction.followup.send(embed=_err("Amount must be greater than zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        bal_before = await self.bot.treasury_service.get_balance(guild_id)
        if amount > bal_before:
            await interaction.followup.send(
                embed=_err(f"Treasury only holds **{bal_before:,} DC**. Cannot remove **{amount:,} DC**."),
                ephemeral=True,
            )
            return

        await self.bot.treasury_service.withdraw(guild_id, amount, note or "Admin treasury withdrawal")
        bal_after = await self.bot.treasury_service.get_balance(guild_id)

        embed = discord.Embed(
            title       = "☠  Treasury Decree — Funds Removed",
            description = f"*{amount:,} DC has been removed from the Kingdom Treasury.*",
            color       = _CRIMSON,
        )
        embed.add_field(name="Removed",  value=f"**−{amount:,} DC**",   inline=True)
        embed.add_field(name="Previous", value=f"**{bal_before:,} DC**", inline=True)
        embed.add_field(name="New",      value=f"**{bal_after:,} DC**",  inline=True)
        if note:
            embed.add_field(name="Note", value=note, inline=False)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger:
            await self.ledger.log(
                action           = "treasury_remove",
                amount           = amount,
                from_label       = "Kingdom Treasury",
                to_label         = f"Admin ({interaction.user.display_name})",
                guild_id         = guild_id,
                treasury_before  = bal_before,
                treasury_after   = bal_after,
                action_type      = "treasury",
            )

    # ── /treasury-set ─────────────────────────────────────────────────────────

    @app_commands.command(name="treasury-set", description="[Admin] Set the Kingdom Treasury to an exact amount.")
    @app_commands.describe(amount="The exact new Treasury balance.")
    @app_commands.default_permissions(administrator=True)
    async def treasury_set(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)

        if not is_admin_user(interaction):
            await interaction.followup.send(embed=denied_generic(), ephemeral=True)
            return
        if amount < 0:
            await interaction.followup.send(embed=_err("Treasury balance cannot be set below zero."), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        bal_before = await self.bot.treasury_service.get_balance(guild_id)
        delta      = amount - bal_before

        if delta > 0:
            await self.bot.treasury_service.deposit(guild_id, delta, "Admin treasury set")
        elif delta < 0:
            await self.bot.treasury_service.withdraw(guild_id, abs(delta), "Admin treasury set")

        embed = discord.Embed(
            title       = "📜  Treasury Decree — Balance Set",
            description = f"*The Kingdom Treasury has been rewritten to **{amount:,} DC**.*",
            color       = _GOLD,
        )
        embed.add_field(name="Previous", value=f"**{bal_before:,} DC**", inline=True)
        embed.add_field(name="New",      value=f"**{amount:,} DC**",     inline=True)
        embed.set_footer(text=f"Decree by {interaction.user.display_name}  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed, ephemeral=True)

        if self.ledger and delta != 0:
            await self.ledger.log(
                action           = "treasury_set",
                amount           = abs(delta),
                from_label       = f"Admin ({interaction.user.display_name})",
                to_label         = "Kingdom Treasury",
                guild_id         = guild_id,
                treasury_before  = bal_before,
                treasury_after   = amount,
                action_type      = "treasury",
            )
