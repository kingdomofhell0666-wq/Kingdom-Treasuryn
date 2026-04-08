import discord
from discord.ext import commands
import logging

from .database import Database
from .services import (
    EconomyService,
    RankService,
    CooldownService,
    TransactionService,
    TreasuryService,
    AuditService,
    CerberusService,
    BlackMarketService,
    InvestmentService,
    CosmeticService,
    BadgeService,
)

logger = logging.getLogger("kingdom_treasury")


class KingdomTreasuryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix="!kt_",
            intents=intents,
            help_command=None,
        )

        self.db: Database = Database()

        self.rank_service = RankService()
        self.economy_service: EconomyService = None
        self.cooldown_service: CooldownService = None
        self.transaction_service: TransactionService = None
        self.treasury_service: TreasuryService = None
        self.audit_service: AuditService = None
        self.cerberus_service: CerberusService = None
        self.blackmarket_service: BlackMarketService = None
        self.investment_service: InvestmentService = None
        self.cosmetic_service: CosmeticService = None
        self.badge_service: BadgeService = None

    async def setup_hook(self):
        await self.db.connect()

        self.economy_service = EconomyService(self.db)
        self.cooldown_service = CooldownService(self.db)
        self.transaction_service = TransactionService(self.db)
        self.treasury_service = TreasuryService(self.db)
        self.audit_service = AuditService(self.db)
        self.cerberus_service = CerberusService(self.db)
        self.blackmarket_service = BlackMarketService(self.db)
        self.investment_service = InvestmentService(self.db)
        self.cosmetic_service = CosmeticService(self.db)
        self.badge_service = BadgeService(self.db)

        from .cogs.economy import EconomyCog
        from .cogs.profile import ProfileCog
        from .cogs.investment import InvestmentCog
        from .cogs.blackmarket import BlackMarketCog
        from .cogs.cosmetics import CosmeticsCog

        await self.add_cog(EconomyCog(self))
        await self.add_cog(ProfileCog(self))
        await self.add_cog(InvestmentCog(self))
        await self.add_cog(BlackMarketCog(self))
        await self.add_cog(CosmeticsCog(self))

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

    async def close(self):
        await self.db.close()
        await super().close()
