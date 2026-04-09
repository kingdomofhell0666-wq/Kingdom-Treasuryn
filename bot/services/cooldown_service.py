from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from ..database import Database


_FALLBACK_COOLDOWNS = {
    "grind":   timedelta(minutes=30),
    "tribute": timedelta(hours=24),
}


class CooldownService:
    def __init__(self, db: Database, config_service=None):
        self.db             = db
        self.config_service = config_service

    async def _get_duration(self, guild_id: str, action: str) -> timedelta:
        """
        Return the cooldown duration for `action` in `guild_id`.
        Reads grind_cooldown_seconds / tribute_cooldown_seconds from
        guild_configs (via ConfigService) when available, otherwise
        falls back to the hardcoded defaults.
        """
        if self.config_service and guild_id:
            try:
                cfg = await self.config_service.get_guild_config(guild_id)
                if action == "grind":
                    secs = int(cfg.get("grind_cooldown_seconds") or 1800)
                    return timedelta(seconds=secs)
                if action == "tribute":
                    secs = int(cfg.get("tribute_cooldown_seconds") or 86400)
                    return timedelta(seconds=secs)
            except Exception:
                pass
        return _FALLBACK_COOLDOWNS.get(action, timedelta(hours=1))

    async def check_cooldown(
        self, guild_id: str, discord_id: str, action: str
    ) -> Tuple[bool, Optional[timedelta]]:
        last_used = await self.db.get_cooldown(guild_id, discord_id, action)
        if last_used is None:
            return True, None
        cooldown_duration = await self._get_duration(guild_id, action)
        elapsed = datetime.now(timezone.utc) - last_used
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
