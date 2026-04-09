from typing import List, Dict
from ..database import Database


class AuditService:
    def __init__(self, db: Database):
        self.db = db

    async def get_user_transactions(self, guild_id: str, discord_id: str, limit: int = 10) -> List[Dict]:
        return await self.db.get_all_transactions(guild_id, discord_id, limit)

    async def get_leaderboard(self, guild_id: str, limit: int = 10) -> List[Dict]:
        return await self.db.get_leaderboard(guild_id, limit)

    async def get_kingdom_rank(self, guild_id: str, discord_id: str) -> int:
        return await self.db.get_kingdom_rank(guild_id, discord_id)
