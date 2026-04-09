"""
ConfigService — reads guild configuration from the shared PostgreSQL database.

Every method caches for CACHE_TTL seconds to avoid hammering the DB on every
bot command.  The cache is per-guild so one guild's updates don't stale-out others.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kingdom_treasury")

CACHE_TTL = 30  # seconds


class _Cache:
    def __init__(self):
        self._data: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        ts, val = entry
        if time.monotonic() - ts > CACHE_TTL:
            del self._data[key]
            return None
        return val

    def set(self, key: str, val: Any):
        self._data[key] = (time.monotonic(), val)

    def invalidate_guild(self, guild_id: str):
        keys = [k for k in self._data if k.startswith(f"{guild_id}:")]
        for k in keys:
            del self._data[k]


_cache = _Cache()


class ConfigService:
    def __init__(self):
        self._pool = None
        self._lock = asyncio.Lock()

    async def _get_pool(self):
        if self._pool is not None:
            return self._pool
        async with self._lock:
            if self._pool is not None:
                return self._pool
            try:
                import asyncpg
                url = os.environ.get("DATABASE_URL", "")
                self._pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
                logger.info("ConfigService connected to PostgreSQL.")
            except Exception as e:
                logger.warning(f"ConfigService: could not connect to PostgreSQL: {e}")
                self._pool = None
        return self._pool

    async def _query_one(self, sql: str, *args) -> Optional[Dict]:
        pool = await self._get_pool()
        if pool is None:
            return None
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(sql, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.warning(f"ConfigService query error: {e}")
            return None

    async def _query_all(self, sql: str, *args) -> List[Dict]:
        pool = await self._get_pool()
        if pool is None:
            return []
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, *args)
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"ConfigService query error: {e}")
            return []

    # ── Guild config (currency name/icon, economy params) ─────────────────────

    async def get_guild_config(self, guild_id: str) -> Dict:
        key = f"{guild_id}:config"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT * FROM guild_configs WHERE guild_id = $1", guild_id
        )
        result = row or {
            "guild_id": guild_id,
            "currency_name": "DevilCoins",
            "currency_icon": "🪙",
            "timezone": "UTC",
            "grind_cooldown_seconds": 3600,
            "tribute_cooldown_seconds": 86400,
            "grind_min_reward": 50,
            "grind_max_reward": 500,
            "tribute_min_reward": 100,
            "tribute_max_reward": 800,
            "black_market_risk_pct": 0.35,
            "investment_tax_rate": 0.08,
        }
        _cache.set(key, result)
        return result

    # ── Command routing ────────────────────────────────────────────────────────

    async def get_command_routing(self, guild_id: str) -> Dict[str, Optional[str]]:
        key = f"{guild_id}:routing"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        rows = await self._query_all(
            "SELECT command_name, channel_id, is_global FROM command_routing WHERE guild_id = $1",
            guild_id,
        )
        result = {r["command_name"]: r["channel_id"] for r in rows if not r["is_global"]}
        _cache.set(key, result)
        return result

    async def check_channel_allowed(self, guild_id: str, command_name: str, channel_id: str) -> bool:
        routing = await self.get_command_routing(guild_id)
        required_channel = routing.get(command_name)
        if required_channel is None:
            return True
        return str(channel_id) == str(required_channel)

    # ── Command permissions ────────────────────────────────────────────────────

    async def get_command_permissions(self, guild_id: str, command_name: str) -> Optional[Dict]:
        key = f"{guild_id}:perms:{command_name}"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT * FROM command_permissions WHERE guild_id = $1 AND command_name = $2",
            guild_id, command_name,
        )
        _cache.set(key, row)
        return row

    async def check_user_permission(
        self,
        guild_id: str,
        command_name: str,
        user_role_ids: List[str],
        channel_id: str,
    ) -> bool:
        perms = await self.get_command_permissions(guild_id, command_name)
        if perms is None:
            return True

        denied_roles    = perms.get("denied_roles", []) or []
        allowed_roles   = perms.get("allowed_roles", []) or []
        denied_channels  = perms.get("denied_channels", []) or []
        allowed_channels = perms.get("allowed_channels", []) or []

        for role_id in user_role_ids:
            if role_id in denied_roles:
                return False

        if allowed_roles and not any(r in allowed_roles for r in user_role_ids):
            return False

        if channel_id in denied_channels:
            return False

        if allowed_channels and channel_id not in allowed_channels:
            return False

        return True

    # ── Rank-role mappings ────────────────────────────────────────────────────

    async def get_rank_role_mapping(self, guild_id: str, rank_name: str) -> Optional[Dict]:
        key = f"{guild_id}:rank_role:{rank_name}"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT * FROM rank_role_mapping WHERE guild_id = $1 AND rank_name = $2",
            guild_id, rank_name,
        )
        _cache.set(key, row)
        return row

    async def get_all_rank_role_mappings(self, guild_id: str) -> List[Dict]:
        key = f"{guild_id}:rank_roles_all"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        rows = await self._query_all(
            "SELECT * FROM rank_role_mapping WHERE guild_id = $1", guild_id
        )
        _cache.set(key, rows)
        return rows

    # ── Ascension cooldown ────────────────────────────────────────────────────

    async def get_rank_cooldown(self, guild_id: str, rank_name: str) -> int:
        key = f"{guild_id}:rank_cooldown:{rank_name}"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT cooldown_seconds FROM rank_cooldown_settings WHERE guild_id = $1 AND rank_name = $2",
            guild_id, rank_name,
        )
        result = row["cooldown_seconds"] if row else 0
        _cache.set(key, result)
        return result

    # ── Ascension announcements ───────────────────────────────────────────────

    async def get_ascension_announcement_settings(self, guild_id: str) -> Optional[Dict]:
        key = f"{guild_id}:ascension_announce"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT * FROM ascension_announcement_settings WHERE guild_id = $1", guild_id
        )
        _cache.set(key, row)
        return row

    # ── Leaderboard settings ──────────────────────────────────────────────────

    async def get_leaderboard_settings_for_guild(self, guild_id: str) -> Optional[Dict]:
        """
        Return the leaderboard_settings row for a single guild, or None if
        no row exists.  Used by the bot-first resolver in leaderboard.py.
        """
        key = f"{guild_id}:leaderboard"
        cached = _cache.get(key)
        if cached is not None:
            return cached

        row = await self._query_one(
            "SELECT * FROM leaderboard_settings WHERE guild_id = $1", guild_id
        )
        _cache.set(key, row)
        return row

    async def get_all_leaderboard_settings(self) -> List[Dict]:
        """Legacy method — returns all guilds with dashboard-enabled leaderboards."""
        rows = await self._query_all(
            "SELECT * FROM leaderboard_settings WHERE enabled = TRUE AND post_channel_id IS NOT NULL"
        )
        return rows

    async def upsert_last_posted_at(self, guild_id: str):
        """
        Create or update the last_posted_at timestamp for a guild.
        Safe to call even when no leaderboard_settings row exists yet.
        """
        pool = await self._get_pool()
        if pool is None:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO leaderboard_settings (guild_id, last_posted_at)
                    VALUES ($1, NOW())
                    ON CONFLICT (guild_id)
                    DO UPDATE SET last_posted_at = NOW()
                    """,
                    guild_id,
                )
            _cache.invalidate_guild(guild_id)
        except Exception as e:
            logger.warning(f"ConfigService upsert_last_posted_at error: {e}")

    async def update_last_posted_at(self, guild_id: str):
        """Kept for backwards compatibility — delegates to upsert."""
        await self.upsert_last_posted_at(guild_id)

    def invalidate_guild(self, guild_id: str):
        """Immediately drop all cached entries for a guild so the next query hits the DB."""
        _cache.invalidate_guild(guild_id)

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
