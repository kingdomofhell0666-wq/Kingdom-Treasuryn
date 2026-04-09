import random
from typing import Optional, Dict, Any
from ..database import Database


class CerberusService:
    AUDIT_CHANCE_PER_RISK = 0.003
    PENALTY_MIN_PCT       = 0.10
    PENALTY_MAX_PCT       = 0.30

    def __init__(self, db: Database):
        self.db = db

    def _audit_probability(self, risk_score: int) -> float:
        return min(risk_score * self.AUDIT_CHANCE_PER_RISK, 0.50)

    async def check_and_run_audit(self, guild_id: str, discord_id: str) -> Optional[Dict[str, Any]]:
        user = await self.db.get_user(guild_id, discord_id)
        if not user:
            return None
        risk_score = user.get("risk_score", 0)
        if risk_score <= 0:
            return None
        if random.random() >= self._audit_probability(risk_score):
            return None

        # Immunity perk check
        perks = await self.db.get_active_perks(guild_id, discord_id)
        for perk in perks:
            if perk["perk_type"] == "audit_immunity":
                await self.db.consume_perk(perk["id"])
                await self.db.adjust_risk_score(guild_id, discord_id, -3)
                return {"triggered": True, "outcome": "immune", "penalty": 0, "risk_delta": -3}

        cleared = random.random() < 0.65
        if cleared:
            await self.db.adjust_risk_score(guild_id, discord_id, -5)
            return {"triggered": True, "outcome": "cleared", "penalty": 0, "risk_delta": -5}
        else:
            user    = await self.db.get_user(guild_id, discord_id)
            balance = user.get("balance", 0)
            pct     = random.uniform(self.PENALTY_MIN_PCT, self.PENALTY_MAX_PCT)
            penalty = max(int(balance * pct), 1) if balance > 0 else 0
            if penalty > 0:
                await self.db.update_balance(guild_id, discord_id, -penalty)
                await self.db.update_treasury(guild_id, penalty)
                await self.db.log_transaction(
                    guild_id, "cerberus_penalty",
                    f"user:{discord_id}", "treasury",
                    penalty, f"Cerberus audit penalty ({int(pct * 100)}%)",
                )
            await self.db.adjust_risk_score(guild_id, discord_id, -5)
            return {"triggered": True, "outcome": "penalized", "penalty": penalty, "penalty_pct": pct, "risk_delta": -5}
