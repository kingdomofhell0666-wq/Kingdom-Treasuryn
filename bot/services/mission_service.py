"""
Kingdom Mission Service — business logic for mission lifecycle.

Entry points (called by cog / view):
  create_mission()    — admin creates a mission
  accept_mission()    — user clicks Accept (full validation chain)
  complete_mission()  — admin marks a participant complete and pays reward
  expire_mission()    — background task sets status → 'expired'
  delete_mission()    — admin hard-deletes a mission

All DC movements are REAL database operations.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("kingdom_treasury")

# Canonical rank order — lower index = lower rank
_RANK_INDEX: dict[str, int] = {
    "Unranked": -1,
    "Forsaken": 0, "Vermin": 1, "Corrupted": 2, "Folklore": 3,
    "Mythology": 4, "Demonology": 5, "Eschatology": 6, "Archangel": 7,
    "Archdemon": 8, "Knight": 9, "Baron": 10, "Viscount": 11,
    "Count": 12, "Marquis": 13, "Duke": 14,
}

MISSION_CHANNEL_ID = "1488258105216209016"


def parse_duration(raw: str) -> Optional[int]:
    """Parse '10m' / '1h' / '24h' / '3d' → seconds.  Returns None on error."""
    s = raw.strip().lower()
    try:
        if s.endswith("m"): return int(s[:-1]) * 60
        if s.endswith("h"): return int(s[:-1]) * 3600
        if s.endswith("d"): return int(s[:-1]) * 86400
    except ValueError:
        pass
    return None


def is_expired(mission: dict) -> bool:
    exp = mission.get("expires_at")
    if not exp:
        return False
    try:
        exp_dt = datetime.fromisoformat(exp).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= exp_dt
    except Exception:
        return False


def remaining_seconds(mission: dict) -> Optional[int]:
    exp = mission.get("expires_at")
    if not exp:
        return None
    try:
        exp_dt = datetime.fromisoformat(exp).replace(tzinfo=timezone.utc)
        secs = (exp_dt - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(secs))
    except Exception:
        return None


def format_remaining(mission: dict) -> str:
    secs = remaining_seconds(mission)
    if secs is None:
        return "No limit"
    if secs <= 0:
        return "Expired"
    h, rem = divmod(secs, 3600)
    m = rem // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


class MissionService:
    def __init__(self, db):
        self.db = db

    # ──────────────────────────────────────────────────────────────────────────
    # Admin actions
    # ──────────────────────────────────────────────────────────────────────────

    async def create_mission(
        self,
        guild_id:         str,
        title:            str,
        reward:           int,
        duration_str:     Optional[str],
        max_participants: Optional[int],
        required_rank:    Optional[str],
        entry_cost:       int,
        description:      Optional[str] = None,
        repeat_limit:     Optional[int] = None,
    ) -> dict:
        """Create a new mission record and return it."""
        expires_at = None
        if duration_str:
            secs = parse_duration(duration_str)
            if secs is None:
                raise ValueError(f"Invalid duration '{duration_str}'. Use: 10m, 1h, 24h, 3d")
            exp_dt = datetime.now(timezone.utc).replace(microsecond=0)
            from datetime import timedelta
            exp_dt += timedelta(seconds=secs)
            expires_at = exp_dt.strftime("%Y-%m-%d %H:%M:%S")

        mission = await self.db.create_mission(
            guild_id         = guild_id,
            title            = title,
            reward           = reward,
            expires_at       = expires_at,
            max_participants = max_participants,
            required_rank    = required_rank,
            entry_cost       = entry_cost,
            channel_id       = MISSION_CHANNEL_ID,
            description      = description,
            repeat_limit     = repeat_limit,
        )
        logger.info(
            f"[MISSION] created id={mission['id']} guild={guild_id} "
            f"title={title!r} reward={reward} entry={entry_cost}"
        )
        return mission

    async def delete_mission(self, mission_id: int) -> bool:
        """Mark a mission as deleted.  Returns False if not found."""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return False
        await self.db.set_mission_status(mission_id, "deleted")
        return True

    async def expire_mission(self, mission_id: int):
        await self.db.set_mission_status(mission_id, "expired")

    # ──────────────────────────────────────────────────────────────────────────
    # User action: accept
    # ──────────────────────────────────────────────────────────────────────────

    async def accept_mission(
        self,
        guild_id:   str,
        discord_id: str,
        username:   str,
        mission_id: int,
    ) -> dict:
        """
        Full validation chain for accepting a mission.
        Returns {"ok": True, ...} or {"ok": False, "reason": str}.
        On success, handles entry fee deduction automatically.
        """
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return {"ok": False, "reason": "This mission no longer exists."}
        if mission["status"] != "active":
            return {"ok": False, "reason": "This mission is no longer available."}
        if is_expired(mission):
            return {"ok": False, "reason": "This mission has expired."}

        # Slots
        if mission["max_participants"] is not None:
            count = await self.db.count_mission_participants(mission_id)
            if count >= mission["max_participants"]:
                return {"ok": False, "reason": "This mission is no longer available."}

        # Already accepted
        existing = await self.db.get_mission_participant(mission_id, discord_id)
        if existing:
            if existing["status"] == "completed":
                return {"ok": False, "reason": "You have already completed this mission."}
            return {"ok": False, "reason": "You have already accepted this mission."}

        # Rank requirement
        required_rank = mission.get("required_rank")
        if required_rank:
            user = await self.db.get_user(guild_id, discord_id)
            user_rank  = user.get("rank", "Unranked") if user else "Unranked"
            req_idx    = _RANK_INDEX.get(required_rank, 0)
            user_idx   = _RANK_INDEX.get(user_rank, -1)
            if user_idx < req_idx:
                return {"ok": False, "reason": "You are not worthy of this task."}

        # Entry cost
        entry_cost = mission.get("entry_cost", 0) or 0
        wallet_before = 0
        if entry_cost > 0:
            await self.db.upsert_user(guild_id, discord_id, username)
            user = await self.db.get_user(guild_id, discord_id)
            wallet_before = user.get("balance", 0) if user else 0
            if wallet_before < entry_cost:
                return {
                    "ok": False,
                    "reason": (
                        f"Insufficient funds. Entry requires **{entry_cost:,}** <:devilcoinStack:1492184333392412692> "
                        f"and you have **{wallet_before:,}** <:devilcoinStack:1492184333392412692>."
                    ),
                }
            treasury_before = await self.db.get_treasury_balance(guild_id)
            await self.db.update_balance(guild_id, discord_id, -entry_cost)
            await self.db.update_treasury(guild_id, entry_cost)
            await self.db.log_transaction(
                guild_id,
                "mission_entry_fee",
                f"user:{discord_id}",
                "treasury",
                entry_cost,
                (
                    f"Mission #{mission_id} entry — {mission['title']!r} | "
                    f"wallet_before={wallet_before} wallet_after={wallet_before - entry_cost} "
                    f"treasury_before={treasury_before} treasury_after={treasury_before + entry_cost}"
                ),
            )
            logger.info(
                f"[MISSION ENTRY] mission={mission_id} user={discord_id} "
                f"entry_cost={entry_cost} wallet_before={wallet_before}"
            )

        await self.db.add_mission_participant(mission_id, guild_id, discord_id)
        return {"ok": True, "entry_cost": entry_cost}

    # ──────────────────────────────────────────────────────────────────────────
    # Admin action: complete (pay reward)
    # ──────────────────────────────────────────────────────────────────────────

    async def complete_mission(
        self,
        guild_id:   str,
        discord_id: str,
        mission_id: int,
    ) -> dict:
        """
        Admin-validates a participant's completion and pays the reward from Treasury.
        Returns {"ok": True, "reward": int} or {"ok": False, "reason": str}.
        """
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return {"ok": False, "reason": "Mission not found."}
        if mission["status"] not in ("active",):
            return {"ok": False, "reason": f"Mission is {mission['status']} — cannot complete."}
        if is_expired(mission):
            return {"ok": False, "reason": "Mission has expired — cannot complete."}

        participant = await self.db.get_mission_participant(mission_id, discord_id)
        if not participant:
            return {"ok": False, "reason": "This user has not accepted this mission."}
        if participant["status"] == "completed":
            return {"ok": False, "reason": "This user has already been paid for this mission."}

        reward           = mission["reward"]
        treasury_before  = await self.db.get_treasury_balance(guild_id)
        if treasury_before < reward:
            return {
                "ok": False,
                "reason": (
                    f"Treasury has insufficient funds. "
                    f"Reward: **{reward:,}** <:devilcoinStack:1492184333392412692>, Treasury: **{treasury_before:,}** <:devilcoinStack:1492184333392412692>."
                ),
            }

        user = await self.db.get_user(guild_id, discord_id)
        wallet_before = user.get("balance", 0) if user else 0

        await self.db.update_treasury(guild_id, -reward)
        await self.db.update_balance(guild_id, discord_id, reward)
        await self.db.complete_mission_participant(mission_id, discord_id)
        await self.db.log_transaction(
            guild_id,
            "mission_reward",
            "treasury",
            f"user:{discord_id}",
            reward,
            (
                f"Mission #{mission_id} reward — {mission['title']!r} | "
                f"wallet_before={wallet_before} wallet_after={wallet_before + reward} "
                f"treasury_before={treasury_before} treasury_after={treasury_before - reward}"
            ),
        )
        logger.info(
            f"[MISSION COMPLETE] mission={mission_id} user={discord_id} "
            f"reward={reward} treasury_before={treasury_before}"
        )
        return {"ok": True, "reward": reward}
