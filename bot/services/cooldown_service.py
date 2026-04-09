from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from ..database import Database


COOLDOWNS = {
    "grind":   timedelta(minutes=30),
    "tribute": timedelta(hours=24),
}


class CooldownService:
    def __init__(self, db: Database):
        self.db = db

    async def check_cooldown(self, guild_id: str, discord_id: str, action: str) -> Tuple[bool, Optional[timedelta]]:
        last_used = await self.db.get_cooldown(guild_id, discord_id, action)
        if last_used is None:
            return True, None
        cooldown_duration = COOLDOWNS.get(action)
        if cooldown_duration is None:
            return True, None
        elapsed   = datetime.now(timezone.utc) - last_used
        if elapsed >= cooldown_duration:
            return True, None
        return False, cooldown_duration - elapsed

    async def set_cooldown(self, guild_id: str, discord_id: str, action: str):
        await self.db.set_cooldown(guild_id, discord_id, action)

    def format_remaining(self, remaining: timedelta) -> str:
        total = int(remaining.total_seconds())
        hours, rem = divmod(total, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if hours:   parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        if seconds and not hours: parts.append(f"{seconds}s")
        return " ".join(parts) if parts else "moments"
