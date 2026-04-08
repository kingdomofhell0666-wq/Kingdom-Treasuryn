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


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @property
    def economy(self) -> EconomyService:
        return self.bot.economy_service

    @property
    def cooldown(self) -> CooldownService:
        return self.bot.cooldown_service

    @property
    def audit(self) -> AuditService:
        return self.bot.audit_service

    @property
    def treasury(self) -> TreasuryService:
        return self.bot.treasury_service

    @property
    def rank_service(self) -> RankService:
        return self.bot.rank_service

    @property
    def cerberus(self) -> CerberusService:
        return self.bot.cerberus_service

    @property
    def badge_service(self) -> BadgeService:
        return self.bot.badge_service

    # ─── Badge announce helper ────────────────────────────────
    async def _announce_badges(
        self,
        interaction: discord.Interaction,
        new_badges: list,
    ):
        if not new_badges:
            return
        lines = []
        for b in new_badges:
            lines.append(f"{b.icon}  **{b.name}**  ·  *{b.description}*")
        embed = discord.Embed(
            title="🏅  Badge Unlocked",
            description="\n".join(lines),
            color=0xFFD700,
        )
        embed.set_footer(text="Earned — not purchased.  ·  Kingdom Treasury")
        await interaction.followup.send(embed=embed)

    # ─── /grind ───────────────────────────────────────────────

    @app_commands.command(name="grind", description="Descend into the Infernal Mines.")
    async def grind(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        ready, remaining = await self.cooldown.check_cooldown(discord_id, "grind")
        if not ready:
            remaining_str = self.cooldown.format_remaining(remaining)
            embed = EmbedFactory.cooldown_error("grind", remaining_str)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(discord_id, "grind")

        try:
            result = await self.economy.grind(discord_id, username)
        except Exception as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.grind_result(result)
        await interaction.followup.send(embed=embed)

        # ── Badge hooks ──
        # Jackpot grants the high_roller badge explicitly
        if result.get("outcome_label") == "jackpot":
            await self.badge_service.grant_badge(discord_id, "high_roller")
        new_badges = await self.badge_service.check_and_award(discord_id)
        await self._announce_badges(interaction, new_badges)

        # ── Cerberus audit check (fires silently after the main response) ──
        audit = await self.cerberus.check_and_run_audit(discord_id)
        if audit and audit["triggered"]:
            outcome = audit["outcome"]
            if outcome == "penalized":
                audit_embed = EmbedFactory.cerberus_penalty(
                    audit["penalty"], audit["penalty_pct"], audit["risk_delta"]
                )
            elif outcome == "immune":
                audit_embed = EmbedFactory.cerberus_immune()
            else:
                # Grant cerberus_guard badge on audit clearance
                await self.badge_service.grant_badge(discord_id, "cerberus_guard")
                audit_embed = EmbedFactory.cerberus_cleared(audit["risk_delta"])
            await interaction.followup.send(embed=audit_embed)

    # ─── /tribute ─────────────────────────────────────────────

    @app_commands.command(name="tribute", description="Receive tribute from the realm. Once per day.")
    async def tribute(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        ready, remaining = await self.cooldown.check_cooldown(discord_id, "tribute")
        if not ready:
            remaining_str = self.cooldown.format_remaining(remaining)
            embed = EmbedFactory.cooldown_error("tribute", remaining_str)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await self.cooldown.set_cooldown(discord_id, "tribute")

        try:
            result = await self.economy.tribute(discord_id, username)
        except Exception as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.tribute_result(result)
        await interaction.followup.send(embed=embed)

        # ── Badge hooks ──
        await self.db.increment_tribute_count(discord_id)
        new_badges = await self.badge_service.check_and_award(discord_id)
        await self._announce_badges(interaction, new_badges)

        # ── Cerberus audit check ──
        audit = await self.cerberus.check_and_run_audit(discord_id)
        if audit and audit["triggered"]:
            outcome = audit["outcome"]
            if outcome == "penalized":
                audit_embed = EmbedFactory.cerberus_penalty(
                    audit["penalty"], audit["penalty_pct"], audit["risk_delta"]
                )
            elif outcome == "immune":
                audit_embed = EmbedFactory.cerberus_immune()
            else:
                await self.badge_service.grant_badge(discord_id, "cerberus_guard")
                audit_embed = EmbedFactory.cerberus_cleared(audit["risk_delta"])
            await interaction.followup.send(embed=audit_embed)

    # ─── /transfer ────────────────────────────────────────────

    @app_commands.command(name="transfer", description="Transfer DevilCoins to another soul.")
    @app_commands.describe(
        recipient="The soul to receive the transfer.",
        amount="Amount of DevilCoins to transfer.",
    )
    async def transfer(
        self,
        interaction: discord.Interaction,
        recipient: discord.Member,
        amount: int,
    ):
        await interaction.response.defer(ephemeral=False)

        sender_id = str(interaction.user.id)
        sender_name = interaction.user.display_name
        recipient_id = str(recipient.id)
        recipient_name = recipient.display_name

        try:
            result = await self.economy.transfer(
                sender_id, sender_name, recipient_id, recipient_name, amount
            )
        except ValueError as e:
            embed = EmbedFactory.error(str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = EmbedFactory.transfer_success(
            sender_name,
            recipient_name,
            result["amount"],
            result["tax_on_transfer"],
            result["net_to_recipient"],
            result["sender_balance"],
        )
        await interaction.followup.send(embed=embed)

    # ─── /vault ───────────────────────────────────────────────

    @app_commands.command(name="vault", description="View the total reserves of the Kingdom Treasury.")
    async def vault(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        balance = await self.treasury.get_balance()
        embed = EmbedFactory.vault(balance)
        await interaction.followup.send(embed=embed)

    # ─── /market ──────────────────────────────────────────────

    @app_commands.command(name="market", description="Browse all purchasable ranks.")
    async def market(self, interaction: discord.Interaction):
        purchasable = self.rank_service.get_purchasable_ranks()
        view = MarketView(purchasable)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    # ─── /ascend ──────────────────────────────────────────────

    @app_commands.command(name="ascend", description="Purchase a rank and ascend the hierarchy.")
    @app_commands.describe(rank_name="The rank you wish to ascend to (must be the next rank).")
    async def ascend(self, interaction: discord.Interaction, rank_name: str):
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)
        username = interaction.user.display_name

        if not self.rank_service.rank_exists(rank_name):
            embed = EmbedFactory.error(
                f"The rank **{rank_name}** does not exist in the Kingdom's records."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if not self.rank_service.is_purchasable(rank_name):
            embed = EmbedFactory.error("That rank cannot be purchased. It is beyond commerce.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        user = await self.db.upsert_user(discord_id, username)
        current_rank = user.get("rank", "Forsaken")

        if not self.rank_service.can_ascend_to(current_rank, rank_name):
            next_rank = self.rank_service.get_next_rank(current_rank)
            if next_rank:
                embed = EmbedFactory.error(
                    f"You must ascend in order. Your next rank is **{next_rank}**."
                )
            else:
                embed = EmbedFactory.error("You have reached the pinnacle. No further ascension is possible.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        cost = self.rank_service.get_rank_cost(rank_name)
        if user["balance"] < cost:
            needed = cost - user["balance"]
            embed = EmbedFactory.error(
                f"Your coffers fall short by **{needed:,} DC**.\n"
                f"Ascension to **{rank_name}** requires **{cost:,} DC**."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        confirm_embed = EmbedFactory.ascend_confirm(rank_name, cost, user["balance"])

        async def do_ascend(inter: discord.Interaction):
            tx_service = TransactionService(self.db)
            await tx_service.ascension_payment(discord_id, rank_name, cost)
            updated_user = await self.db.get_user(discord_id)
            new_balance = updated_user["balance"] if updated_user else 0
            success_embed = EmbedFactory.ascend_success(rank_name, cost, new_balance)
            await inter.followup.send(embed=success_embed)
            # ── Badge hooks (rank-gated badges check after ascension) ──
            new_badges = await self.badge_service.check_and_award(discord_id)
            await self._announce_badges(inter, new_badges)

        view = AscendConfirmView(rank_name, cost, do_ascend)
        await interaction.followup.send(embed=confirm_embed, view=view)
