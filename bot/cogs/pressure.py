"""
PressureCog — Scheduled economy pressure tasks.

Tasks:
  - Daily tax collection (once per 24 h, guarded by meta key)
  - Rank downgrade check (every hour; 72 h cooldown per user enforced by PressureService)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from discord.ext import commands, tasks

from ..services.pressure_service import PressureService

logger = logging.getLogger("kingdom_treasury")


class PressureCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot      = bot
        self.pressure = PressureService()

    async def cog_load(self):
        self._pressure_loop.start()

    def cog_unload(self):
        self._pressure_loop.cancel()

    @tasks.loop(minutes=60)
    async def _pressure_loop(self):
        """
        Runs every 60 minutes.
        - Tax: fires once per 24 h (meta-key guard).
        - Downgrade: fires every loop; 72 h cooldown enforced per-user.
        """
        await self.bot.wait_until_ready()
        now_utc = datetime.now(timezone.utc)

        # ── Tax collection ────────────────────────────────────────────────────
        last_tax_str = await self.bot.db.get_meta("last_tax_collected")
        should_tax   = True
        if last_tax_str:
            try:
                last_dt = datetime.fromisoformat(last_tax_str)
                if (now_utc - last_dt).total_seconds() < 86_400:
                    should_tax = False
            except Exception:
                pass

        if should_tax:
            for guild in self.bot.guilds:
                gid = str(guild.id)
                try:
                    total, count = await self.pressure.collect_and_announce_taxes(self.bot, gid)
                    if total > 0:
                        logger.info(
                            f"[Pressure] Tax collected guild={gid}: {total:,} DC from {count} souls"
                        )
                except Exception as exc:
                    logger.error(f"[Pressure] Tax collection failed guild={gid}: {exc}")
            await self.bot.db.set_meta("last_tax_collected", now_utc.isoformat())

        # ── Downgrade check ───────────────────────────────────────────────────
        for guild in self.bot.guilds:
            gid = str(guild.id)
            try:
                await self.pressure.check_downgrades(self.bot, gid)
            except Exception as exc:
                logger.error(f"[Pressure] Downgrade check failed guild={gid}: {exc}")

    @_pressure_loop.before_loop
    async def _before_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
