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
from ..utils.grind_card import generate_grind_card
from ..utils.card_generator import fetch_avatar
from ..ui import MarketView, AscendConfirmView, MineEntryView


# ── Infernal Mines copy ────────────────────────────────────────────────────────

_ASSETS     = os.path.join(os.path.dirname(__file__), "..", "assets")
ENTRY_COLOR  = 0x1A0000
SEARCH_COLOR = 0x3D0000
WALK_COLOR   = 0x0D0D0D

# Entry screen — atmospheric descriptions
_MINE_DESCRIPTIONS = [
    (
        "*The entrance breathes heat.*\n\n"
        "*The deeper you go, the less returns.*\n"
        "*Some return richer. Some return empty.*\n"
        "*Some… do not return the same.*"
    ),
    (
        "*The gates to the Infernal Mines stand open.*\n\n"
        "*The stone walls pulse with ancient heat.*\n"
        "*The Kingdom expects its share.*\n"
        "*Whatever you find below — it will take its cut.*"
    ),
    (
        "*The mine demands a decision.*\n\n"
        "*Beyond this threshold, the rules of the surface no longer apply.*\n"
        "*Wealth lies in the dark.*\n"
        "*So does risk.*"
    ),
    (
        "*A foul wind carries the scent of sulfur.*\n\n"
        "*The pickaxe is yours. The mine is old.*\n"
        "*It has swallowed many who entered confident.*\n"
        "*Do you step forward?*"
    ),
]

# Phase 1 — "entering" animation text
_ENTER_TEXTS = [
    "*You step into the abyss…*",
    "*The mine closes behind you…*",
    "*The darkness swallows your silhouette…*",
    "*The heat intensifies with each step…*",
    "*You descend past the threshold…*",
]

# Phase 2 — "searching" animation text
_SEARCH_TEXTS = [
    "*The darkness responds to your presence…*",
    "*The veins are being tested…*",
    "*The stone trembles underfoot…*",
    "*Your pickaxe strikes ancient rock…*",
    "*Something stirs deep within the seam…*",
    "*The ore whispers of its worth…*",
    "*Shadows shift in the hellfire light…*",
]

# Walk away
_WALKAWAY_DESCRIPTIONS = [
    (
        "*You turn your back on the mine.*\n\n"
        "*The Kingdom remembers cowardice… and restraint.*"
    ),
    (
        "*The gates remain open — but you do not enter.*\n\n"
        "*Perhaps wisdom. Perhaps fear.*\n"
        "*The mine will be here.*"
    ),
    (
        "*You step back.*\n\n"
        "*The mine watches you leave.*\n"
        "*It always watches.*"
    ),
]


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):            return self.bot.db
    @property
    def economy(self):       return self.bot.economy_service
    @property
    def cooldown(self):      return self.bot.cooldown_service
    @property
    def audit(self):         return self.bot.audit_service
    @property
    def treasury(self):      return self.bot.treasury_service
    @property
    def rank_service(self):  return self.bot.rank_service
    @property
    def cerberus(self):      return self.bot.cerberus_service
    @property
    def badge_service(self): return self.bot.badge_service

    # ─── Badge announce helper ────────────────────────────────

    async def _announce_badges(self, inter: discord.Interaction, new_badges: list):
        if not new_badges:
            return
        lines = [f"{b.icon}  **{b.name}**  ·  *{b.description}*" for b in new_badges]
        embed = discord.Embed(title="🏅  Badge Unlocked", description="\n".join(lines), color=0xFFD700)
        embed.set_footer(text="Earned — not purchased.  ·  Kingdom Treasury")
        await inter.followup.send(embed=embed)

    # ─── Cerberus helper ──────────────────────────────────────

    async def _run_cerberus(self, inter: discord.Interaction, guild_id: str, discord_id: str):
        audit = await self.cerberus.check_and_run_audit(guild_id, discord_id)
        if audit and audit["triggered"]:
            outcome = audit["outcome"]
            if outcome == "penalized":
                embed = EmbedFactory.cerberus_penalty(audit["penalty"], audit["penalty_pct"], audit["risk_delta"])
            elif outcome == "immune":
                embed = EmbedFactory.cerberus_immune()
            else:
                await self.badge_service.grant_badge(guild_id, discord_id, "cerberus_guard")
                embed = EmbedFactory.cerberus_cleared(audit["risk_delta"])
            await inter.followup.send(embed=embed)

    # ─── /grind ───────────────────────────────────────────────

    @app_commands.command(name="grind", description="Descend into the Infernal Mines.")
    async def grind(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name

        # ── Cooldown gate (checked before entry screen) ───────
        ready, remaining = await self.cooldown.check_cooldown(guild_id, discord_id, "grind")
        if not ready:
            embed = EmbedFactory.cooldown_error("grind", self.cooldown.format_remaining(remaining))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # ── Build entry screen ────────────────────────────────
        view = MineEntryView(owner_id=interaction.user.id)

        entry_embed = discord.Embed(
            title="⛏  Infernal Mines",
            description=_random.choice(_MINE_DESCRIPTIONS),
            color=ENTRY_COLOR,
        )
        entry_embed.set_image(url="attachment://mine_entry.png")
        entry_embed.set_footer(text="Choose wisely.  ·  Kingdom Treasury  ·  Kingdom of Hell")

        entry_path = os.path.join(_ASSETS, "mine_entry.png")
        entry_file = discord.File(entry_path, filename="mine_entry.png")
        msg = await interaction.followup.send(embed=entry_embed, file=entry_file, view=view)
        view.message = msg

        # ── Enter callback ────────────────────────────────────

        async def on_enter(inter: discord.Interaction):
            # Cooldown is set NOW — the commitment is made
            await self.cooldown.set_cooldown(guild_id, discord_id, "grind")

            # Compute result before animation begins
            try:
                result = await self.economy.grind(guild_id, discord_id, username)
            except Exception as e:
                await inter.response.edit_message(
                    embed=EmbedFactory.error(str(e)), view=None, attachments=[]
                )
                return

            # ── Phase 1: entering ─────────────────────────────
            p1 = discord.Embed(
                title="⛏  Infernal Mines",
                description=_random.choice(_ENTER_TEXTS),
                color=ENTRY_COLOR,
            )
            # Preserve the uploaded image via its CDN URL
            if msg.attachments:
                p1.set_image(url=msg.attachments[0].url)
            p1.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await inter.response.edit_message(embed=p1, view=None)

            # ── Phase 2: searching ────────────────────────────
            await asyncio.sleep(2.0)
            p2 = discord.Embed(
                title="⛏  Infernal Mines",
                description=_random.choice(_SEARCH_TEXTS),
                color=SEARCH_COLOR,
            )
            if msg.attachments:
                p2.set_image(url=msg.attachments[0].url)
            p2.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await inter.message.edit(embed=p2)

            # ── Phase 3: generate + reveal result card ────────
            await asyncio.sleep(1.5)

            outcome = result.get("outcome_label", "common")

            # Fetch avatar (async HTTP, fast)
            try:
                avatar_url = inter.user.display_avatar.with_size(128).url
            except Exception:
                avatar_url = None
            avatar_bytes = await fetch_avatar(avatar_url)

            # Generate card in thread pool — keeps event loop free
            loop = asyncio.get_event_loop()
            card_buf = await loop.run_in_executor(None, lambda: generate_grind_card(
                username     = username,
                rank         = result.get("rank", "Forsaken"),
                outcome      = outcome,
                extraction   = result["gross"],
                flat_bonus   = result.get("flat_bonus", 0),
                tax          = result["tax_amount"],
                eff_rate     = result["effective_tax_rate"],
                net          = result["net"],
                balance      = result["new_balance"],
                avatar_bytes = avatar_bytes,
                skin_id      = result.get("equipped_skin"),
            ))

            # Minimal embed — image is the entire reward display
            _CARD_COLORS = {
                "failure": 0x0A0A0A, "meager": 0x6B0000,
                "common":  0xB22222, "rich":   0xCC7700, "jackpot": 0xFFD700,
            }
            card_embed = discord.Embed(color=_CARD_COLORS.get(outcome, 0xB22222))
            card_embed.set_image(url="attachment://grind_result.png")

            card_file = discord.File(card_buf, filename="grind_result.png")
            await inter.edit_original_response(embed=card_embed, attachments=[card_file])

            # ── Post-result: badges + audit ───────────────────
            if outcome == "jackpot":
                await self.badge_service.grant_badge(guild_id, discord_id, "high_roller")
            new_badges = await self.badge_service.check_and_award(guild_id, discord_id)
            await self._announce_badges(inter, new_badges)
            await self._run_cerberus(inter, guild_id, discord_id)

        # ── Walk away callback ────────────────────────────────

        async def on_walk_away(inter: discord.Interaction):
            walk_embed = discord.Embed(
                title="⛏  Infernal Mines",
                description=_random.choice(_WALKAWAY_DESCRIPTIONS),
                color=WALK_COLOR,
            )
            walk_embed.set_footer(
                text="No coins lost. None gained.  ·  Kingdom Treasury  ·  Kingdom of Hell"
            )
            await inter.response.edit_message(embed=walk_embed, view=None, attachments=[])

        view.set_enter_callback(on_enter)
        view.set_walk_callback(on_walk_away)

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
