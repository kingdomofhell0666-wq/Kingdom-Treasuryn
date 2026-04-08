import random
from typing import Optional, Dict, Any
from ..database import Database


class CerberusService:
    """
    The Cerberus Audit System.

    Each user carries a risk_score (0–100).
    After grind or tribute, there is a chance of a random audit.
    Audit triggers → cleared or penalized (wallet deduction).
    """

    # At risk_score=100, there is a 30% audit chance per eligible action.
    AUDIT_CHANCE_PER_RISK = 0.003  # 0.3% per point

    PENALTY_MIN_PCT = 0.10
    PENALTY_MAX_PCT = 0.30

    def __init__(self, db: Database):
        self.db = db

    def _audit_probability(self, risk_score: int) -> float:
        return min(risk_score * self.AUDIT_CHANCE_PER_RISK, 0.50)

    async def check_and_run_audit(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """
        Called after grind/tribute. Returns an audit result dict if triggered, else None.
        """
        user = await self.db.get_user(discord_id)
        if not user:
            return None

        risk_score = user.get("risk_score", 0)
        if risk_score <= 0:
            return None

        prob = self._audit_probability(risk_score)
        if random.random() >= prob:
            return None

        # Check for audit immunity perk
        perks = await self.db.get_active_perks(discord_id)
        for perk in perks:
            if perk["perk_type"] == "audit_immunity":
                await self.db.consume_perk(perk["id"])
                await self.db.adjust_risk_score(discord_id, -3)
                return {
                    "triggered": True,
                    "outcome": "immune",
                    "penalty": 0,
                    "risk_delta": -3,
                }

        # Determine outcome
        cleared = random.random() < 0.65  # 65% chance of being cleared

        if cleared:
            await self.db.adjust_risk_score(discord_id, -5)
            return {
                "triggered": True,
                "outcome": "cleared",
                "penalty": 0,
                "risk_delta": -5,
            }
        else:
            # Refresh balance
            user = await self.db.get_user(discord_id)
            balance = user.get("balance", 0)
            pct = random.uniform(self.PENALTY_MIN_PCT, self.PENALTY_MAX_PCT)
            penalty = int(balance * pct)
            penalty = max(penalty, 1) if balance > 0 else 0

            if penalty > 0:
                await self.db.update_balance(discord_id, -penalty)
                await self.db.update_treasury(penalty)
                await self.db.log_transaction(
                    "cerberus_penalty",
                    f"user:{discord_id}",
                    "treasury",
                    penalty,
                    f"Cerberus audit penalty ({int(pct * 100)}%)",
                )

            await self.db.adjust_risk_score(discord_id, -5)
            return {
                "triggered": True,
                "outcome": "penalized",
                "penalty": penalty,
                "penalty_pct": pct,
                "risk_delta": -5,
            }
