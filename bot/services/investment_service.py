import random
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from ..database import Database


INVESTMENT_TYPES = {
    "safe": {
        "label": "Safe",
        "description": "Stable returns. No risk. Slow accumulation.",
        "maturity_hours": 1,
        "return_min": 0.05, "return_max": 0.10,
        "success_chance": 1.0, "loss_pct": 0.0, "min_amount": 100,
    },
    "medium": {
        "label": "Medium Risk",
        "description": "Moderate returns with a chance of partial loss.",
        "maturity_hours": 6,
        "return_min": 0.20, "return_max": 0.35,
        "success_chance": 0.75, "loss_pct": 0.15, "min_amount": 500,
    },
    "risky": {
        "label": "High Risk",
        "description": "Extreme potential. Extreme danger. The abyss does not guarantee return.",
        "maturity_hours": 24,
        "return_min": 0.50, "return_max": 0.80,
        "success_chance": 0.50, "loss_pct": 0.35, "min_amount": 1_000,
    },
}


class InvestmentService:
    def __init__(self, db: Database):
        self.db = db

    def get_types(self) -> Dict[str, dict]:
        return INVESTMENT_TYPES

    def _compute_payout(self, inv_type: str, principal: int) -> tuple:
        cfg     = INVESTMENT_TYPES[inv_type]
        success = random.random() < cfg["success_chance"]
        if success:
            rate   = random.uniform(cfg["return_min"], cfg["return_max"])
            profit = int(principal * rate)
            return principal + profit, profit, True
        else:
            loss   = int(principal * cfg["loss_pct"])
            return max(0, principal - loss), -loss, False

    async def invest(self, guild_id: str, discord_id: str, username: str, inv_type: str, amount: int) -> Dict[str, Any]:
        if inv_type not in INVESTMENT_TYPES:
            raise ValueError(f"Unknown investment type: **{inv_type}**. Choose `safe`, `medium`, or `risky`.")
        cfg = INVESTMENT_TYPES[inv_type]
        if amount < cfg["min_amount"]:
            raise ValueError(f"The minimum for **{cfg['label']}** is **{cfg['min_amount']:,}** <:devilcoinStack:1492184333392412692>.")
        user = await self.db.upsert_user(guild_id, discord_id, username)
        if user["balance"] < amount:
            raise ValueError("Insufficient funds in your coffers.")
        now         = datetime.now(timezone.utc)
        matures_at  = now + timedelta(hours=cfg["maturity_hours"])
        matures_str = matures_at.strftime("%Y-%m-%d %H:%M:%S")
        await self.db.update_balance(guild_id, discord_id, -amount)
        await self.db.log_transaction(guild_id, "investment_open", f"user:{discord_id}", "kingdom_mint", amount, f"Investment opened: {inv_type}")
        inv_id      = await self.db.create_investment(guild_id, discord_id, inv_type, amount, matures_str)
        updated     = await self.db.get_user(guild_id, discord_id)
        return {
            "id": inv_id, "inv_type": inv_type, "label": cfg["label"],
            "amount": amount, "matures_at": matures_at,
            "maturity_hours": cfg["maturity_hours"],
            "new_balance":    updated["balance"]           if updated else 0,
            "rank":           updated.get("rank", "Forsaken") if updated else "Forsaken",
            "equipped_skin":  updated.get("equipped_skin") if updated else None,
        }

    async def get_portfolio(self, guild_id: str, discord_id: str) -> List[Dict[str, Any]]:
        investments = await self.db.get_active_investments(guild_id, discord_id)
        now    = datetime.now(timezone.utc)
        result = []
        for inv in investments:
            matures_at = datetime.fromisoformat(inv["matures_at"]).replace(tzinfo=timezone.utc)
            matured    = now >= matures_at
            result.append({**inv, "matured": matured, "remaining": matures_at - now if not matured else timedelta(0), "matures_at_dt": matures_at})
        return result

    async def collect(self, guild_id: str, discord_id: str) -> Dict[str, Any]:
        matured = await self.db.get_matured_investments(guild_id, discord_id)
        if not matured:
            raise ValueError("No matured investments to collect. Check `/portfolio`.")
        total_payout = 0
        results      = []
        for inv in matured:
            payout, profit, success = self._compute_payout(inv["inv_type"], inv["principal"])
            await self.db.settle_investment(inv["id"], payout, "collected")
            await self.db.update_balance(guild_id, discord_id, payout)
            await self.db.log_transaction(guild_id, "investment_collect", "kingdom_mint", f"user:{discord_id}", payout, f"Investment settled: {inv['inv_type']}")
            total_payout += payout
            results.append({"id": inv["id"], "inv_type": inv["inv_type"], "principal": inv["principal"], "payout": payout, "profit": profit, "success": success})
        updated = await self.db.get_user(guild_id, discord_id)
        return {
            "results": results, "total_payout": total_payout,
            "new_balance":   updated["balance"]           if updated else 0,
            "rank":          updated.get("rank", "Forsaken") if updated else "Forsaken",
            "equipped_skin": updated.get("equipped_skin") if updated else None,
        }

    async def withdraw_early(self, guild_id: str, discord_id: str) -> Dict[str, Any]:
        investments = await self.db.get_active_investments(guild_id, discord_id)
        now         = datetime.now(timezone.utc)
        active      = [inv for inv in investments if now < datetime.fromisoformat(inv["matures_at"]).replace(tzinfo=timezone.utc)]
        if not active:
            raise ValueError("No active investments to withdraw. Check `/portfolio` for matured ones.")
        PENALTY_PCT  = 0.20
        total_payout = 0
        results      = []
        for inv in active:
            payout  = int(inv["principal"] * (1 - PENALTY_PCT))
            penalty = inv["principal"] - payout
            await self.db.settle_investment(inv["id"], payout, "withdrawn")
            await self.db.update_balance(guild_id, discord_id, payout)
            await self.db.log_transaction(guild_id, "investment_withdraw", "kingdom_mint", f"user:{discord_id}", payout, f"Early withdrawal: {inv['inv_type']} (20% penalty)")
            await self.db.log_transaction(guild_id, "investment_penalty", f"user:{discord_id}", "void", penalty, "Early withdrawal penalty burned")
            total_payout += payout
            results.append({"id": inv["id"], "inv_type": inv["inv_type"], "principal": inv["principal"], "payout": payout, "penalty": penalty})
        updated = await self.db.get_user(guild_id, discord_id)
        return {
            "results": results, "total_payout": total_payout, "count": len(results),
            "new_balance":   updated["balance"]           if updated else 0,
            "rank":          updated.get("rank", "Forsaken") if updated else "Forsaken",
            "equipped_skin": updated.get("equipped_skin") if updated else None,
        }
