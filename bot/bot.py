import os
import asyncio
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timezone

from .database import Database
from .services import (
    EconomyService, RankService, CooldownService, TransactionService,
    TreasuryService, AuditService, CerberusService,
    InvestmentService, CosmeticService, AscensionAnnouncementService,
)
from .services.config_service import ConfigService
from .services.guild_sync_service import GuildSyncService
from .services.cerberus_aggression import CerberusAggression
from .services.mission_service import MissionService
from .services.ledger_service import LedgerService
from .services.pressure_service import PressureService
from .services.heartbeat_service import HeartbeatService

logger = logging.getLogger("kingdom_treasury")


class KingdomTreasuryBot(commands.Bot):
    def __init__(self):
        intents               = discord.Intents.default()
        intents.members       = True
        intents.voice_states  = True

        super().__init__(command_prefix="!kt_", intents=intents, help_command=None)

        self.db: Database = Database()
        self.config_service: ConfigService = ConfigService()
        self.guild_sync_service: GuildSyncService = GuildSyncService()

        self.rank_service                    = RankService()
        self.ascension_announcement_service  = AscensionAnnouncementService()
        self.cerberus_aggression             = CerberusAggression()   # in-memory, always available
        self.economy_service                 = None
        self.cooldown_service                = None
        self.transaction_service             = None
        self.treasury_service                = None
        self.audit_service                   = None
        self.cerberus_service                = None
        self.investment_service              = None
        self.cosmetic_service                = None
        self.mission_service                 = None
        self.ledger_service: LedgerService    = None
        self.pressure_service: PressureService = None
        self.heartbeat_service: HeartbeatService = HeartbeatService(self)

    async def setup_hook(self):
        await self.db.connect()

        # ── Token fingerprint check ──────────────────────────────────────────
        token = os.environ.get("DISCORD_BOT_TOKEN", "")
        current_fp = Database.compute_token_fingerprint(token)
        stored_fp  = await self.db.get_meta("token_fingerprint")
        force_reset = os.environ.get("FULL_RESET_ON_START", "").lower() in ("1", "true", "yes")

        if force_reset:
            logger.error(
                "FULL_RESET_ON_START was requested but ignored: startup must never "
                "wipe economy data. Use an explicit, audited admin action instead."
            )
        elif stored_fp and stored_fp != current_fp:
            logger.warning(
                f"Token fingerprint mismatch (stored={stored_fp}, current={current_fp}). "
                "Preserving all economy data; token changes are not a reset trigger."
            )

        await self.db.set_meta("token_fingerprint", current_fp)

        # ── Services ─────────────────────────────────────────────────────────
        self.economy_service     = EconomyService(self.db, config_service=self.config_service)
        self.cooldown_service    = CooldownService(self.db, config_service=self.config_service)
        self.transaction_service = TransactionService(self.db)
        self.treasury_service    = TreasuryService(self.db)
        self.audit_service       = AuditService(self.db)
        self.cerberus_service    = CerberusService(self.db)
        self.investment_service  = InvestmentService(self.db)
        self.cosmetic_service    = CosmeticService(self.db)
        self.mission_service     = MissionService(self.db)
        self.ledger_service      = LedgerService(self)   # must come after bot is usable
        self.pressure_service    = PressureService()     # stateless — only needs bot.db at runtime

        # ── Cogs ─────────────────────────────────────────────────────────────
        from .cogs.economy        import EconomyCog
        from .cogs.profile        import ProfileCog
        from .cogs.investment     import InvestmentCog
        from .cogs.cosmetics      import CosmeticsCog
        from .cogs.admin          import AdminCog
        from .cogs.leaderboard    import LeaderboardCog
        from .cogs.missions       import MissionsCog
        from .cogs.freeze         import FreezeCog
        from .cogs.pressure       import PressureCog
        from .cogs.voice_activity import VoiceActivityCog

        await self.add_cog(EconomyCog(self))
        await self.add_cog(ProfileCog(self))
        await self.add_cog(InvestmentCog(self))
        await self.add_cog(CosmeticsCog(self))
        await self.add_cog(AdminCog(self))
        await self.add_cog(LeaderboardCog(self))
        await self.add_cog(MissionsCog(self))
        await self.add_cog(FreezeCog(self))
        await self.add_cog(PressureCog(self))
        await self.add_cog(VoiceActivityCog(self))

        await self.tree.sync()
        logger.info("Command tree synchronized.")

    async def on_ready(self):
        logger.info(f"Kingdom Treasury online — {self.user} ({self.user.id})")
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="every transaction in the Kingdom",
            ),
        )
        await self.db.set_meta("start_time", datetime.now(timezone.utc).isoformat())
        if not self._heartbeat_loop.is_running():
            self._heartbeat_loop.start()
        # Start dashboard heartbeat service
        asyncio.create_task(self.heartbeat_service.run())
        # Sync all guild structures into PostgreSQL so the dashboard
        # always has up-to-date channel/role data.
        asyncio.create_task(self.guild_sync_service.sync_all(list(self.guilds)))
        # Seed canonical role IDs for all guilds (DO NOTHING on conflict, so
        # manual dashboard overrides are preserved across restarts).
        asyncio.create_task(self._seed_canonical_roles())

    async def _seed_canonical_roles(self):
        """Seed hardcoded canonical role IDs into the DB for all guilds."""
        for guild in self.guilds:
            guild_id = str(guild.id)
            try:
                await self.config_service.seed_canonical_role_mappings(guild_id)
            except Exception as exc:
                logger.warning(f"Canonical role seed failed for guild={guild_id}: {exc}")

    async def on_guild_join(self, guild: discord.Guild):
        """Immediately sync a newly joined guild's channels and roles."""
        logger.info(f"Joined guild {guild.id} ({guild.name}) — syncing channels+roles.")
        asyncio.create_task(self.guild_sync_service.sync_guild(guild))

    async def on_guild_available(self, guild: discord.Guild):
        """Called when a guild becomes available after a reconnect — re-sync."""
        asyncio.create_task(self.guild_sync_service.sync_guild(guild))

    @tasks.loop(seconds=30)
    async def _heartbeat_loop(self):
        await self.db.set_meta("last_heartbeat", datetime.now(timezone.utc).isoformat())

    async def on_guild_remove(self, guild: discord.Guild):
        """Preserve guild data when the bot leaves; deletion requires explicit action."""
        guild_id = str(guild.id)
        logger.info(
            f"Removed from guild {guild_id} ({guild.name}) — "
            "economy data preserved for a future return or explicit admin action."
        )

    async def close(self):
        await self.db.close()
        await self.config_service.close()
        await self.guild_sync_service.close()
        await super().close()
