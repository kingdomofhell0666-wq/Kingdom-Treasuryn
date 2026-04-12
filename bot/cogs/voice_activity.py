"""
VoiceActivityCog — tracks how long eligible members spend in voice channels.

On join  → record join timestamp in memory.
On leave → compute elapsed seconds, flush to DB immediately.
Every 5m → flush all currently-active sessions (so a bot restart doesn't lose
           the entire week's voice time for users currently in VC).

Only members who are registered in the bot's economy DB accumulate time.
Staff-hierarchy exclusion happens at the leaderboard query level, not here —
tracking extra data is harmless.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Tuple

import discord
from discord.ext import commands, tasks

logger = logging.getLogger("kingdom_treasury")

# How often (in minutes) to flush active sessions to DB as a safety checkpoint.
FLUSH_INTERVAL_MINUTES = 5


class VoiceActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Nested dict: guild_id_str → {member_id_int: join_datetime_utc}
        self._sessions: Dict[str, Dict[int, datetime]] = {}
        self._flush_loop.start()

    def cog_unload(self):
        self._flush_loop.cancel()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _join(self, guild_id: str, member_id: int):
        """Record that a member just entered a voice channel."""
        guild_sessions = self._sessions.setdefault(guild_id, {})
        if member_id not in guild_sessions:
            guild_sessions[member_id] = datetime.now(timezone.utc)

    def _leave(self, guild_id: str, member_id: int) -> int:
        """
        Record that a member just left a voice channel.
        Returns the number of whole seconds they were active (0 if no session).
        """
        guild_sessions = self._sessions.get(guild_id, {})
        join_time = guild_sessions.pop(member_id, None)
        if join_time is None:
            return 0
        elapsed = (datetime.now(timezone.utc) - join_time).total_seconds()
        return max(0, int(elapsed))

    async def _flush_member(self, guild_id: str, member_id: int, seconds: int):
        """Write accumulated seconds to the DB if the user row exists."""
        if seconds <= 0:
            return
        try:
            user = await self.bot.db.get_user(guild_id, str(member_id))
            if user is not None:
                await self.bot.db.add_weekly_active_seconds(
                    guild_id, str(member_id), seconds
                )
        except Exception as exc:
            logger.warning(
                f"[VoiceActivity] flush failed for "
                f"guild={guild_id} member={member_id}: {exc}"
            )

    # ── Voice state event ─────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild_id = str(member.guild.id)

        was_in_voice = before.channel is not None
        now_in_voice = after.channel is not None

        if not was_in_voice and now_in_voice:
            # Member joined a voice channel
            self._join(guild_id, member.id)

        elif was_in_voice and not now_in_voice:
            # Member left voice entirely
            seconds = self._leave(guild_id, member.id)
            await self._flush_member(guild_id, member.id, seconds)

        elif was_in_voice and now_in_voice and before.channel != after.channel:
            # Member switched channels — leave the old one, join the new one.
            # Compute time in the old channel and record it, then restart timer.
            guild_sessions = self._sessions.get(guild_id, {})
            join_time = guild_sessions.get(member.id)
            if join_time is not None:
                elapsed = max(
                    0,
                    int((datetime.now(timezone.utc) - join_time).total_seconds()),
                )
                guild_sessions[member.id] = datetime.now(timezone.utc)
                await self._flush_member(guild_id, member.id, elapsed)

    # ── Periodic flush ────────────────────────────────────────────────────────

    @tasks.loop(minutes=FLUSH_INTERVAL_MINUTES)
    async def _flush_loop(self):
        """
        Save active voice sessions to DB without ending them.
        Resets the join timestamp to now so duration stays accurate.
        """
        now = datetime.now(timezone.utc)
        for guild_id, guild_sessions in list(self._sessions.items()):
            for member_id, join_time in list(guild_sessions.items()):
                elapsed = max(0, int((now - join_time).total_seconds()))
                if elapsed > 0:
                    guild_sessions[member_id] = now  # reset checkpoint
                    await self._flush_member(guild_id, member_id, elapsed)

    @_flush_loop.before_loop
    async def _before_flush(self):
        await self.bot.wait_until_ready()
        # Seed sessions for any members already in voice when bot starts.
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            for vc in guild.voice_channels:
                for member in vc.members:
                    if not member.bot:
                        self._join(guild_id, member.id)
        logger.info(
            "[VoiceActivity] seeded active voice sessions from current guild state."
        )
