from typing import List, Dict
from ..database import Database


class AuditService:
    def __init__(self, db: Database):
        self.db = db

    async def get_user_transactions(self, discord_id: str, limit: int = 10) -> List[Dict]:
        return await self.db.get_all_transactions(discord_id, limit)

    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        return await self.db.get_leaderboard(limit)

    async def get_kingdom_rank(self, discord_id: str) -> int:
        return await self.db.get_kingdom_rank(discord_id)
