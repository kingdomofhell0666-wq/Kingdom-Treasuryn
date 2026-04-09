import asyncio
import random as _random
import os
import discord
from discord import app_commands
from discord.ext import commands

from ..services import EconomyService, CooldownService, AuditService, TreasuryService, BadgeService
from ..services.rank_service import RankService
from ..services.transaction_service import TransactionService
from ..services.cerberus_service import CerberusService
from ..utils.embeds import EmbedFactory
from ..utils.badges import BADGES_CATALOG
from ..ui import MarketView, AscendConfirmView


# ── Infernal Mines animation copy ─────────────────────────────────────────────

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

MINE_ENTRY_TEXTS = [
    "*Descending into the depths...*",
    "*The darkness pulls you downward...*",
    "*The gates of the Infernal Mines creak open...*",
    "*You step past the threshold into the abyss...*",
    "*The heat rises as you descend...*",
    "*The mine swallows you whole...*",
]

MINE_SEARCH_TEXTS = [
    "*The veins are being tested...*",
    "*The stone trembles underfoot...*",
    "*A deeper vein calls from below...*",
    "*The darkness responds to your strike...*",
    "*Your pickaxe rings against ancient rock...*",
    "*Shadows shift in the hellfire light...*",
    "*The ore whispers of its worth...*",
    "*Something stirs deep within the seam...*",
]

ENTRY_COLOR  = 0x1A0000
SEARCH_COLOR = 0x3D0000


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):              return self.bot.db
    @property
    def economy(self):         return self.bot.economy_service
    @property
    def cooldown(self):        return self.bot.cooldown_service
    @property
    def audit(self):           return self.bot.audit_service
    @property
    def treasury(self):        return self.bot.treasury_service
    @property
    def rank_service(self):    return self.bot.rank_service
    @property
    def cerberus(self):        return self.bot.cerberus_service
    @property
    def badge_service(self):   return self.bot.badge_service

    # ─── Badge announce helper ────────────────────────────────

    async def _announce_badges(self, interaction: discord.Interaction, new_badges: list):
        if not new_badges:
            return
        lines = [f"{b.icon}  **{b.name}**  ·  *{b.description}*" for b in new_badges]
        embed = discord.Embed(title="🏅  Badge Unlocked", description="\n".join(lines), color=0xFFD700)
        embed.set_footer(text="Earned — not purchased.  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed)

    # ─── Cerberus follow-up helper ────────────────────────────

    async def _run_cerberus(self, interaction: discord.Interaction, guild_id: str, discord_id: str):
        audit = await self.cerberus.check_and_run_audit(guild_id, discord_id)
        if audit and audit["triggered"]:
            outcome = audit["outcome"]
            if outcome == "penalized":
                audit_embed = EmbedFactory.cerberus_penalty(audit["penalty"], audit["penalty_pct"], audit["risk_delta"])
            elif outcome == "immune":
                audit_embed = EmbedFactory.cerberus_immune()
            else:
                await self.badge_service.grant_badge(guild_id, discord_id, "cerberus_guard")
                audit_embed = EmbedFactory.cerberus_cleared(audit["risk_delta"])
            await interaction.followup.send(embed=audit_embed)

    # ─── /grind ───────────────────────────────────────────────

    @app_commands.command(name="grind", description="Descend into the Infernal Mines.")
    async def grind(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        # ── Cooldown gate ──────────────────────────────────────
        ready, remaining = await self.cooldown.check_cooldown(guild_id, discord_id, "grind")
        if not ready:
            embed = EmbedFactory.cooldown_error("grind", self.cooldown.format_remaining(remaining))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(guild_id, discord_id, "grind")

        # ── Compute result immediately ─────────────────────────
        try:
            result = await self.economy.grind(guild_id, discord_id, username)
        except Exception as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        # ── Phase 1 — ENTRY ───────────────────────────────────
        entry_embed = discord.Embed(
            title="⛏  Infernal Mines",
            description=_random.choice(MINE_ENTRY_TEXTS),
            color=ENTRY_COLOR,
        )
        entry_embed.set_image(url="attachment://mine_entry.png")
        entry_embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

        entry_path = os.path.join(_ASSETS, "mine_entry.png")
        entry_file = discord.File(entry_path, filename="mine_entry.png")
        msg = await interaction.followup.send(embed=entry_embed, file=entry_file)

        # ── Phase 2 — SEARCH ──────────────────────────────────
        await asyncio.sleep(2.0)

        search_embed = discord.Embed(
            title="⛏  Infernal Mines",
            description=_random.choice(MINE_SEARCH_TEXTS),
            color=SEARCH_COLOR,
        )
        # Preserve the uploaded image URL from the first message
        if msg.attachments:
            search_embed.set_image(url=msg.attachments[0].url)
        search_embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await msg.edit(embed=search_embed)

        # ── Phase 3 — RESULT REVEAL ───────────────────────────
        await asyncio.sleep(1.5)

        result_embed = EmbedFactory.grind_result(result)
        await msg.edit(embed=result_embed, attachments=[])

        # ── Post-result: badges + audit ────────────────────────
        if result.get("outcome_label") == "jackpot":
            await self.badge_service.grant_badge(guild_id, discord_id, "high_roller")
        new_badges = await self.badge_service.check_and_award(guild_id, discord_id)
        await self._announce_badges(interaction, new_badges)
        await self._run_cerberus(interaction, guild_id, discord_id)

    # ─── /tribute ─────────────────────────────────────────────

    @app_commands.command(name="tribute", description="Receive tribute from the realm. Once per day.")
    async def tribute(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        ready, remaining = await self.cooldown.check_cooldown(guild_id, discord_id, "tribute")
        if not ready:
            embed = EmbedFactory.cooldown_error("tribute", self.cooldown.format_remaining(remaining))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(guild_id, discord_id, "tribute")

        try:
            result = await self.economy.tribute(guild_id, discord_id, username)
        except Exception as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        await interaction.followup.send(embed=EmbedFactory.tribute_result(result))

        await self.db.increment_tribute_count(guild_id, discord_id)
        new_badges = await self.badge_service.check_and_award(guild_id, discord_id)
        await self._announce_badges(interaction, new_badges)
        await self._run_cerberus(interaction, guild_id, discord_id)

    # ─── /transfer ────────────────────────────────────────────

    @app_commands.command(name="transfer", description="Transfer DevilCoins to another soul.")
    @app_commands.describe(recipient="The soul to receive the transfer.", amount="Amount of DevilCoins to transfer.")
    async def transfer(self, interaction: discord.Interaction, recipient: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=False)

        guild_id       = str(interaction.guild_id)
        sender_id      = str(interaction.user.id)
        sender_name    = interaction.user.display_name
        recipient_id   = str(recipient.id)
        recipient_name = recipient.display_name

        try:
            result = await self.economy.transfer(guild_id, sender_id, sender_name, recipient_id, recipient_name, amount)
        except ValueError as e:
            await interaction.followup.send(embed=EmbedFactory.error(str(e)), ephemeral=True)
            return

        embed = EmbedFactory.transfer_success(
            sender_name, recipient_name,
            result["amount"], result["tax_on_transfer"], result["net_to_recipient"], result["sender_balance"],
        )
        await interaction.followup.send(embed=embed)

    # ─── /vault ───────────────────────────────────────────────

    @app_commands.command(name="vault", description="View the total reserves of the Kingdom Treasury.")
    async def vault(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id = str(interaction.guild_id)
        balance  = await self.treasury.get_balance(guild_id)
        await interaction.followup.send(embed=EmbedFactory.vault(balance))

    # ─── /market ──────────────────────────────────────────────

    @app_commands.command(name="market", description="Browse all purchasable ranks.")
    async def market(self, interaction: discord.Interaction):
        purchasable = self.rank_service.get_purchasable_ranks()
        view  = MarketView(purchasable)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    # ─── /ascend ──────────────────────────────────────────────

    @app_commands.command(name="ascend", description="Purchase a rank and ascend the hierarchy.")
    @app_commands.describe(rank_name="The rank you wish to ascend to (must be the next rank).")
    async def ascend(self, interaction: discord.Interaction, rank_name: str):
        await interaction.response.defer(ephemeral=False)

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        if not self.rank_service.rank_exists(rank_name):
            await interaction.followup.send(embed=EmbedFactory.error(f"The rank **{rank_name}** does not exist."), ephemeral=True)
            return

        if not self.rank_service.is_purchasable(rank_name):
            await interaction.followup.send(embed=EmbedFactory.error("That rank cannot be purchased."), ephemeral=True)
            return

        user = await self.db.upsert_user(guild_id, discord_id, username)
        current_rank = user.get("rank", "Forsaken")

        if not self.rank_service.can_ascend_to(current_rank, rank_name):
            next_rank = self.rank_service.get_next_rank(current_rank)
            msg = f"You must ascend in order. Your next rank is **{next_rank}**." if next_rank else "No further ascension is possible."
            await interaction.followup.send(embed=EmbedFactory.error(msg), ephemeral=True)
            return

        cost = self.rank_service.get_rank_cost(rank_name)
        if user["balance"] < cost:
            needed = cost - user["balance"]
            await interaction.followup.send(embed=EmbedFactory.error(f"Your coffers fall short by **{needed:,} DC**.\nAscension to **{rank_name}** costs **{cost:,} DC**."), ephemeral=True)
            return

        confirm_embed = EmbedFactory.ascend_confirm(rank_name, cost, user["balance"])

        async def do_ascend(inter: discord.Interaction):
            tx_service = TransactionService(self.db)
            await tx_service.ascension_payment(guild_id, discord_id, rank_name, cost)
            updated    = await self.db.get_user(guild_id, discord_id)
            new_balance = updated["balance"] if updated else 0
            await inter.followup.send(embed=EmbedFactory.ascend_success(rank_name, cost, new_balance))
            new_badges = await self.badge_service.check_and_award(guild_id, discord_id)
            await self._announce_badges(inter, new_badges)

        view = AscendConfirmView(rank_name, cost, do_ascend)
        await interaction.followup.send(embed=confirm_embed, view=view)
