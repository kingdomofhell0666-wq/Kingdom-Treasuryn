import json
from typing import List
from ..database import Database
from ..utils.badges import BADGES_CATALOG, Badge

AUTO_UNLOCK_TYPES = {
    "balance_gte", "taxes_gte", "grind_count_gte",
    "tribute_count_gte", "rank_index_gte", "account_age_days",
}

RANK_ORDER = [
    "Forsaken","Vermin","Corrupted","Mythology","Folklore","Eschatology",
    "Demonology","Archangel","Archdemon","Knight","Baron","Viscount",
    "Count","Marquis","Duke","Chancellor",
]


class BadgeService:
    def __init__(self, db: Database):
        self.db = db

    def _parse_badges(self, raw) -> List[str]:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    def _check_condition(self, badge: Badge, user: dict) -> bool:
        ut = badge.unlock_type
        uv = badge.unlock_threshold   # field is unlock_threshold, not unlock_value
        if ut == "balance_gte":
            return user.get("balance", 0) >= uv
        if ut == "taxes_gte":
            return user.get("taxes_paid", 0) >= uv
        if ut == "grind_count_gte":
            return user.get("grind_count", 0) >= uv
        if ut == "tribute_count_gte":
            return user.get("tribute_count", 0) >= uv
        if ut == "rank_index_gte":
            rank = user.get("rank", "Forsaken")
            idx  = RANK_ORDER.index(rank) if rank in RANK_ORDER else 0
            return idx >= uv
        if ut == "account_age_days":
            from datetime import datetime, timezone
            created = user.get("created_at")
            if not created:
                return False
            dt    = datetime.fromisoformat(created).replace(tzinfo=timezone.utc)
            delta = (datetime.now(timezone.utc) - dt).days
            return delta >= uv
        return False

    async def check_and_award(self, guild_id: str, discord_id: str) -> List[Badge]:
        user = await self.db.get_user(guild_id, discord_id)
        if not user:
            return []
        owned         = set(self._parse_badges(user.get("owned_badges")))
        newly_awarded = []
        for badge_id, badge in BADGES_CATALOG.items():
            if badge_id in owned:
                continue
            if badge.unlock_type not in AUTO_UNLOCK_TYPES:
                continue
            if self._check_condition(badge, user):
                owned.add(badge_id)
                newly_awarded.append(badge)
        if newly_awarded:
            await self.db.set_owned_badges(guild_id, discord_id, json.dumps(list(owned)))
        return newly_awarded

    async def grant_badge(self, guild_id: str, discord_id: str, badge_id: str) -> bool:
        if badge_id not in BADGES_CATALOG:
            return False
        user = await self.db.get_user(guild_id, discord_id)
        if not user:
            return False
        owned = set(self._parse_badges(user.get("owned_badges")))
        if badge_id in owned:
            return False
        owned.add(badge_id)
        await self.db.set_owned_badges(guild_id, discord_id, json.dumps(list(owned)))
        return True

    async def get_owned_badges(self, guild_id: str, discord_id: str) -> List[str]:
        user = await self.db.get_user(guild_id, discord_id)
        if not user:
            return []
        return self._parse_badges(user.get("owned_badges"))
