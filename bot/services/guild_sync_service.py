"""
GuildSyncService — pushes guild channel + role data from Discord into PostgreSQL.

Triggered by:
  - on_ready       (all guilds the bot is in)
  - on_guild_join  (a new guild)
  - on_guild_available (after reconnect / re-identification)

This keeps the dashboard's channel/role selectors accurate without any
round-trip to the Discord API from the API server.

Only text channels (type 0) and announcement channels (type 5) are stored,
since those are the only ones that matter for bot posting.

All DB writes use upsert-style logic: INSERT → conflict on (guild_id, channel_id)
→ UPDATE name/type/category.  Stale rows (channels/roles deleted in Discord) are
cleaned up after each full sync.
"""

import asyncio
import logging
import os
from typing import List, Optional

import discord

logger = logging.getLogger("kingdom_treasury")

# Channel types we store
_TEXT_TYPES = {0, 5}  # 0 = text, 5 = announcement


class GuildSyncService:
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
                self._pool = await asyncpg.create_pool(url, min_size=1, max_size=3)
                logger.info("GuildSyncService connected to PostgreSQL.")
            except Exception as exc:
                logger.warning(f"GuildSyncService: cannot connect to PostgreSQL: {exc}")
                self._pool = None
        return self._pool

    # ── Public API ────────────────────────────────────────────────────────────

    async def sync_guild(self, guild: discord.Guild):
        """Sync channels and roles for a single guild."""
        guild_id = str(guild.id)
        try:
            await asyncio.gather(
                self._sync_channels(guild_id, guild.channels),
                self._sync_roles(guild_id, guild.roles),
            )
            logger.info(
                f"GuildSync: guild={guild_id} ({guild.name})  "
                f"channels={len(guild.channels)}  roles={len(guild.roles)}"
            )
        except Exception as exc:
            logger.warning(f"GuildSync failed for guild {guild_id}: {exc}")

    async def sync_all(self, guilds: List[discord.Guild]):
        """Sync all guilds (called from on_ready)."""
        tasks = [self.sync_guild(g) for g in guilds]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"GuildSync: completed initial sync for {len(guilds)} guild(s).")

    # ── Channels ──────────────────────────────────────────────────────────────

    async def _sync_channels(self, guild_id: str, channels):
        pool = await self._get_pool()
        if pool is None:
            return

        text_channels = [
            c for c in channels
            if isinstance(c, (discord.TextChannel, discord.ForumChannel))
            or getattr(c, "type", None) in (discord.ChannelType.text, discord.ChannelType.news)
        ]

        if not text_channels:
            return

        async with pool.acquire() as conn:
            # Upsert each channel
            for ch in text_channels:
                ch_type = "announcement" if getattr(ch, "type", None) == discord.ChannelType.news else "text"
                parent_id = str(ch.category_id) if getattr(ch, "category_id", None) else None
                await conn.execute(
                    """
                    INSERT INTO guild_channels
                        (guild_id, channel_id, channel_name, channel_type, parent_category_id, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (guild_id, channel_id)
                    DO UPDATE SET
                        channel_name      = EXCLUDED.channel_name,
                        channel_type      = EXCLUDED.channel_type,
                        parent_category_id = EXCLUDED.parent_category_id,
                        updated_at        = NOW()
                    """,
                    guild_id, str(ch.id), ch.name, ch_type, parent_id,
                )

            # Remove stale channels (deleted from Discord)
            live_ids = [str(c.id) for c in text_channels]
            await conn.execute(
                """
                DELETE FROM guild_channels
                WHERE guild_id = $1
                  AND channel_id <> ALL($2::text[])
                """,
                guild_id, live_ids,
            )

    # ── Roles ─────────────────────────────────────────────────────────────────

    async def _sync_roles(self, guild_id: str, roles):
        pool = await self._get_pool()
        if pool is None:
            return

        # Exclude @everyone
        real_roles = [r for r in roles if r.name != "@everyone"]
        if not real_roles:
            return

        async with pool.acquire() as conn:
            for role in real_roles:
                await conn.execute(
                    """
                    INSERT INTO guild_roles
                        (guild_id, role_id, role_name, position, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (guild_id, role_id)
                    DO UPDATE SET
                        role_name  = EXCLUDED.role_name,
                        position   = EXCLUDED.position,
                        updated_at = NOW()
                    """,
                    guild_id, str(role.id), role.name, role.position,
                )

            # Remove stale roles
            live_ids = [str(r.id) for r in real_roles]
            await conn.execute(
                """
                DELETE FROM guild_roles
                WHERE guild_id = $1
                  AND role_id <> ALL($2::text[])
                """,
                guild_id, live_ids,
            )

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
