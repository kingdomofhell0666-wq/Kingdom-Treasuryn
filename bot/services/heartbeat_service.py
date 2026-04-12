"""
HeartbeatService — sends periodic liveness pulses from the bot to the
Kingdom Treasury Dashboard API.

The internal endpoint is POST /internal/heartbeat, protected by a bearer
token derived from SESSION_SECRET (same formula as the API server uses).

Heartbeat interval: every 10 seconds.
"""

import asyncio
import hashlib
import logging
import os
import time

import aiohttp

logger = logging.getLogger("kingdom_treasury")

HEARTBEAT_INTERVAL = 10  # seconds
HEARTBEAT_URL = "http://localhost:8080/internal/heartbeat"


def _compute_internal_token() -> str:
    """Derive the internal API token — must match the Node.js formula."""
    secret = os.environ.get("SESSION_SECRET", "dev-secret-change-me")
    return hashlib.sha256(f"{secret}:internal".encode()).hexdigest()


class HeartbeatService:
    """
    Sends heartbeat POSTs to the dashboard API every HEARTBEAT_INTERVAL seconds.
    Attach to the bot via `bot.heartbeat_service = HeartbeatService(bot)` and
    call `asyncio.create_task(bot.heartbeat_service.run())` in on_ready.
    """

    def __init__(self, bot) -> None:
        self.bot   = bot
        self._token = _compute_internal_token()
        self._start_time = time.monotonic()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _uptime_seconds(self) -> int:
        return int(time.monotonic() - self._start_time)

    def _db_status(self) -> str:
        """Best-effort check of the SQLite connection state."""
        try:
            db = getattr(self.bot, "db", None)
            if db is None:
                return "unavailable"
            # Database.db.py stores the aiosqlite connection as _db
            if getattr(db, "_db", None) is None:
                return "disconnected"
            return "connected"
        except Exception:
            return "unknown"

    def _scheduler_status(self) -> str:
        """Check whether the bot's background loops are running."""
        try:
            loop = getattr(self.bot, "_heartbeat_loop", None)
            if loop is None:
                return "unavailable"
            return "running" if loop.is_running() else "stopped"
        except Exception:
            return "unknown"

    # ── Main heartbeat send ────────────────────────────────────────────────

    async def send(self) -> None:
        """Send one heartbeat pulse to the dashboard API."""
        if not self.bot.is_ready() or self.bot.user is None:
            return

        payload = {
            "bot_user_id":         str(self.bot.user.id),
            "bot_username":        str(self.bot.user),
            "guild_count":         len(self.bot.guilds),
            "latency_ms":          round(self.bot.latency * 1000),
            "uptime_seconds":      self._uptime_seconds(),
            "shard_id":            0,
            "scheduler_status":    self._scheduler_status(),
            "db_status":           self._db_status(),
            "command_count_today": None,  # Phase 3: wire real counter
        }

        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    HEARTBEAT_URL, json=payload, headers=headers,
                ) as resp:
                    if resp.status == 200:
                        logger.debug(
                            "Heartbeat sent — latency=%dms guilds=%d uptime=%ds",
                            payload["latency_ms"],
                            payload["guild_count"],
                            payload["uptime_seconds"],
                        )
                    elif resp.status == 401:
                        logger.warning(
                            "Heartbeat auth failure — token mismatch. "
                            "Ensure SESSION_SECRET matches between bot and API server."
                        )
                    else:
                        body = await resp.text()
                        logger.warning(
                            "Heartbeat non-200 response: %s — %s",
                            resp.status, body[:200],
                        )
        except aiohttp.ClientConnectorError:
            logger.debug("Heartbeat: API server not reachable (may still be starting)")
        except asyncio.TimeoutError:
            logger.debug("Heartbeat: request timed out")
        except Exception as exc:  # noqa: BLE001
            logger.debug("Heartbeat send error: %s", exc)

    # ── Background runner ──────────────────────────────────────────────────

    async def run(self) -> None:
        """Background loop — runs forever until cancelled."""
        logger.info("HeartbeatService started (interval=%ds)", HEARTBEAT_INTERVAL)
        while True:
            try:
                await self.send()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Heartbeat loop exception: %s", exc)
            await asyncio.sleep(HEARTBEAT_INTERVAL)
