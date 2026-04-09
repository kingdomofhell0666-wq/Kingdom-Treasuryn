import random
from typing import Dict, Any, List
from ..database import Database
from .transaction_service import TransactionService
from .rank_service import RankService


class EconomyService:
    def __init__(self, db: Database):
        self.db         = db
        self.tx_service = TransactionService(db)
        self.rank_service = RankService()

    GRIND_OUTCOMES = [
        (0.60, 250, 350, "common"),
        (0.80, 100, 200, "meager"),
        (0.90, 0,   0,   "failure"),
        (0.97, 400, 600, "rich"),
        (1.00, 800, 1200, "jackpot"),
    ]
    TRIBUTE_BASE_MIN       = 500
    TRIBUTE_BASE_MAX       = 700
    TRIBUTE_GRIND_BONUS    = 200
    TRIBUTE_GRIND_THRESHOLD = 5

    async def _get_active_perks(self, guild_id: str, discord_id: str) -> List[dict]:
        return await self.db.get_active_perks(guild_id, discord_id)

    async def grind(self, guild_id: str, discord_id: str, username: str) -> Dict[str, Any]:
        user  = await self.db.upsert_user(guild_id, discord_id, username)
        perks = await self._get_active_perks(guild_id, discord_id)

        boost_perk = next((p for p in perks if p["perk_type"] == "grind_boost"), None)
        if boost_perk:
            gross         = random.randint(400, 1200)
            outcome_label = "rich" if gross < 800 else "jackpot"
            await self.db.consume_perk(boost_perk["id"])
        else:
            roll          = random.random()
            gross         = 0
            outcome_label = "failure"
            for chance, low, high, label in self.GRIND_OUTCOMES:
                if roll < chance:
                    gross         = random.randint(low, high) if high > 0 else 0
                    outcome_label = label
                    break

        bonus_perk = next((p for p in perks if p["perk_type"] == "grind_bonus"), None)
        flat_bonus = 0
        if bonus_perk and gross > 0:
            flat_bonus = int(bonus_perk["perk_value"])
            gross     += flat_bonus
            await self.db.consume_perk(bonus_perk["id"])

        ceiling_perk = next((p for p in perks if p["perk_type"] == "grind_ceiling"), None)
        if ceiling_perk and gross > 0:
            gross += int(ceiling_perk["perk_value"])
            await self.db.consume_perk(ceiling_perk["id"])

        base_tax_rate      = self.rank_service.get_tax_rate(user["rank"])
        effective_tax_rate = base_tax_rate

        exempt_perk = next((p for p in perks if p["perk_type"] == "tax_exempt"), None)
        if exempt_perk and gross > 0:
            effective_tax_rate = 0.0
            await self.db.consume_perk(exempt_perk["id"])
        else:
            reduction_perk = next((p for p in perks if p["perk_type"] == "tax_reduction"), None)
            if reduction_perk and gross > 0:
                effective_tax_rate = max(0.0, base_tax_rate - reduction_perk["perk_value"])
                await self.db.consume_perk(reduction_perk["id"])

        tax_amount = int(gross * effective_tax_rate)
        net        = gross - tax_amount

        if net > 0 or tax_amount > 0:
            await self.tx_service.grind_reward(guild_id, discord_id, gross, tax_amount, net)

        await self.db.increment_grind_count(guild_id, discord_id)
        updated = await self.db.get_user(guild_id, discord_id)

        return {
            "success": outcome_label != "failure",
            "outcome_label": outcome_label,
            "gross": gross, "flat_bonus": flat_bonus,
            "base_tax_rate": base_tax_rate, "effective_tax_rate": effective_tax_rate,
            "tax_amount": tax_amount, "net": net,
            "new_balance": updated["balance"] if updated else 0,
        }

    async def tribute(self, guild_id: str, discord_id: str, username: str) -> Dict[str, Any]:
        user  = await self.db.upsert_user(guild_id, discord_id, username)
        perks = await self._get_active_perks(guild_id, discord_id)

        base      = random.randint(self.TRIBUTE_BASE_MIN, self.TRIBUTE_BASE_MAX)
        grind_24h = await self.db.get_grind_count_24h(guild_id, discord_id)
        bonus     = self.TRIBUTE_GRIND_BONUS if grind_24h >= self.TRIBUTE_GRIND_THRESHOLD else 0
        gross     = base + bonus

        tax_rate = self.rank_service.get_tax_rate(user["rank"])
        exempt_perk = next((p for p in perks if p["perk_type"] == "tax_exempt"), None)
        if exempt_perk:
            tax_rate = 0.0
            await self.db.consume_perk(exempt_perk["id"])

        tax = int(gross * tax_rate)
        net = gross - tax

        await self.tx_service.tribute_reward(guild_id, discord_id, gross, tax, net)
        updated = await self.db.get_user(guild_id, discord_id)

        return {
            "gross": gross, "bonus": bonus,
            "tax_amount": tax, "tax_rate": tax_rate,
            "net": net, "new_balance": updated["balance"] if updated else 0,
        }

    async def transfer(self, guild_id: str, sender_id: str, sender_name: str, recipient_id: str, recipient_name: str, amount: int) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")
        if sender_id == recipient_id:
            raise ValueError("You cannot transfer to yourself.")
        sender = await self.db.upsert_user(guild_id, sender_id, sender_name)
        if sender["balance"] < amount:
            raise ValueError(f"Insufficient funds. You have **{sender['balance']:,} DC**.")
        await self.db.upsert_user(guild_id, recipient_id, recipient_name)

        TAX_RATE       = 0.02
        tax            = int(amount * TAX_RATE)
        net_to_recipient = amount - tax

        await self.tx_service.transfer_funds(guild_id, sender_id, recipient_id, amount, tax, net_to_recipient)
        updated = await self.db.get_user(guild_id, sender_id)

        return {
            "amount": amount, "tax_on_transfer": tax,
            "net_to_recipient": net_to_recipient,
            "sender_balance": updated["balance"] if updated else 0,
        }
