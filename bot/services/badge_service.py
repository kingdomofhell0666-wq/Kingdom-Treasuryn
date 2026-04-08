"""
BadgeService — automatic badge award engine.

Evaluates all auto-unlock badge conditions against a user's current state
and awards any newly earned badges. Returns the list of newly awarded Badge
objects so cogs can announce them.

Manual badges (founder, branded_soul, void_walker, etc.) are awarded via
grant_badge() by admins or event systems.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from ..database import Database
from ..utils.badges import BADGES_CATALOG, Badge, AUTO_UNLOCK_TYPES
from ..services.rank_service import RANK_DICT


class BadgeService:
    def __init__(self, db: Database):
        self.db = db

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _parse_badges(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    def _account_age_days(self, created_at: Optional[str]) -> int:
        if not created_at:
            return 0
        try:
            dt = datetime.fromisoformat(created_at).replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).days
        except Exception:
            return 0

    def _rank_index(self, rank_name: str) -> int:
        entry = RANK_DICT.get(rank_name)
        return entry["index"] if entry else 0

    def _check_condition(self, badge: Badge, user: dict) -> bool:
        t = badge.unlock_type
        th = badge.unlock_threshold

        if t == "balance_gte":
            return user.get("balance", 0) >= th
        if t == "taxes_gte":
            return user.get("taxes_paid", 0) >= th
        if t == "grind_count_gte":
            return user.get("grind_count", 0) >= th
        if t == "tribute_count_gte":
            return user.get("tribute_count", 0) >= th
        if t == "rank_index_gte":
            return self._rank_index(user.get("rank", "Forsaken")) >= th
        if t == "account_age_days":
            return self._account_age_days(user.get("created_at")) >= th
        # jackpot / cerberus_cleared / manual — handled via explicit grant_badge
        return False

    # ─── Public API ───────────────────────────────────────────────────────────

    async def check_and_award(self, discord_id: str) -> List[Badge]:
        """
        Check all auto-unlock badges against the user's current state.
        Returns a list of Badge objects that were newly awarded in this call.
        """
        user = await self.db.get_user(discord_id)
        if not user:
            return []

        owned = set(self._parse_badges(user.get("owned_badges")))
        newly_awarded: List[Badge] = []

        for badge_id, badge in BADGES_CATALOG.items():
            if badge_id in owned:
                continue
            if badge.unlock_type not in AUTO_UNLOCK_TYPES:
                continue
            if badge.unlock_type in ("jackpot", "cerberus_cleared", "manual"):
                continue
            if self._check_condition(badge, user):
                owned.add(badge_id)
                newly_awarded.append(badge)

        if newly_awarded:
            await self.db.set_owned_badges(discord_id, json.dumps(list(owned)))

        return newly_awarded

    async def grant_badge(self, discord_id: str, badge_id: str) -> bool:
        """
        Explicitly award a badge (jackpot, cerberus_cleared, or manual).
        Returns True if newly awarded, False if already owned.
        """
        if badge_id not in BADGES_CATALOG:
            return False
        user = await self.db.get_user(discord_id)
        if not user:
            return False

        owned = set(self._parse_badges(user.get("owned_badges")))
        if badge_id in owned:
            return False

        owned.add(badge_id)
        await self.db.set_owned_badges(discord_id, json.dumps(list(owned)))
        return True

    async def get_owned_badges(self, discord_id: str) -> List[str]:
        user = await self.db.get_user(discord_id)
        if not user:
            return []
        return self._parse_badges(user.get("owned_badges"))
