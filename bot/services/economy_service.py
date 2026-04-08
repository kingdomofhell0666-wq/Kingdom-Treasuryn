import random
from typing import Dict, Any, List
from ..database import Database
from .transaction_service import TransactionService
from .rank_service import RankService


class EconomyService:
    def __init__(self, db: Database):
        self.db = db
        self.tx_service = TransactionService(db)
        self.rank_service = RankService()

    # ─── Grind outcomes: (cumulative_chance, (low, high, label)) ──────────
    GRIND_OUTCOMES = [
        (0.60, 250, 350, "common"),
        (0.80, 100, 200, "meager"),
        (0.90, 0,   0,   "failure"),
        (0.97, 400, 600, "rich"),
        (1.00, 800, 1200, "jackpot"),
    ]

    TRIBUTE_BASE_MIN = 500
    TRIBUTE_BASE_MAX = 700
    TRIBUTE_GRIND_BONUS = 200
    TRIBUTE_GRIND_THRESHOLD = 5

    async def _get_active_perks(self, discord_id: str) -> List[dict]:
        return await self.db.get_active_perks(discord_id)

    async def grind(self, discord_id: str, username: str) -> Dict[str, Any]:
        user = await self.db.upsert_user(discord_id, username)
        perks = await self._get_active_perks(discord_id)

        # Check for grind_boost perk (forced rich/jackpot)
        boost_perk = next((p for p in perks if p["perk_type"] == "grind_boost"), None)
        if boost_perk:
            gross = random.randint(400, 1200)
            outcome_label = "rich" if gross < 800 else "jackpot"
            await self.db.consume_perk(boost_perk["id"])
        else:
            roll = random.random()
            cumulative = 0.0
            gross = 0
            outcome_label = "failure"
            for chance, low, high, label in self.GRIND_OUTCOMES:
                if roll < chance:
                    gross = random.randint(low, high) if high > 0 else 0
                    outcome_label = label
                    break
                cumulative = chance

        # Check for grind_bonus perk (flat bonus DC)
        bonus_perk = next((p for p in perks if p["perk_type"] == "grind_bonus"), None)
        flat_bonus = 0
        if bonus_perk and gross > 0:
            flat_bonus = int(bonus_perk["perk_value"])
            gross += flat_bonus
            await self.db.consume_perk(bonus_perk["id"])

        # Check for grind_ceiling perk (+N to max reward)
        ceiling_perk = next((p for p in perks if p["perk_type"] == "grind_ceiling"), None)
        if ceiling_perk and gross > 0:
            gross += int(ceiling_perk["perk_value"])
            await self.db.consume_perk(ceiling_perk["id"])

        # Tax calculation — check for exemption/reduction perks
        base_tax_rate = self.rank_service.get_tax_rate(user["rank"])
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
        net = gross - tax_amount

        if net > 0 or tax_amount > 0:
            await self.tx_service.grind_reward(discord_id, gross, tax_amount, net)

        await self.db.increment_grind_count(discord_id)
        updated_user = await self.db.get_user(discord_id)

        return {
            "success": outcome_label != "failure",
            "outcome_label": outcome_label,
            "gross": gross,
            "flat_bonus": flat_bonus,
            "base_tax_rate": base_tax_rate,
            "effective_tax_rate": effective_tax_rate,
            "tax_amount": tax_amount,
            "net": net,
            "new_balance": updated_user["balance"] if updated_user else 0,
        }

    async def tribute(self, discord_id: str, username: str) -> Dict[str, Any]:
        await self.db.upsert_user(discord_id, username)

        base = random.randint(self.TRIBUTE_BASE_MIN, self.TRIBUTE_BASE_MAX)
        grind_count = await self.db.get_grind_count_24h(discord_id)
        bonus = self.TRIBUTE_GRIND_BONUS if grind_count >= self.TRIBUTE_GRIND_THRESHOLD else 0
        gross = base + bonus

        user = await self.db.get_user(discord_id)
        tax_rate = self.rank_service.get_tax_rate(user["rank"])
        tax_amount = int(gross * tax_rate)
        net = gross - tax_amount

        await self.tx_service.tribute_reward(discord_id, gross, tax_amount, net)

        updated_user = await self.db.get_user(discord_id)
        return {
            "gross": gross,
            "bonus": bonus,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "net": net,
            "new_balance": updated_user["balance"] if updated_user else 0,
        }

    async def transfer(
        self,
        sender_id: str,
        sender_name: str,
        recipient_id: str,
        recipient_name: str,
        amount: int,
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("The amount must be greater than zero.")
        if sender_id == recipient_id:
            raise ValueError("You cannot transfer wealth to yourself.")

        sender = await self.db.upsert_user(sender_id, sender_name)
        await self.db.upsert_user(recipient_id, recipient_name)

        if sender["balance"] < amount:
            raise ValueError("Insufficient funds in your coffers.")

        tax_on_transfer = int(amount * 0.02)
        net_to_recipient = amount - tax_on_transfer

        await self.tx_service.transfer_funds(
            sender_id, recipient_id, amount, tax_on_transfer, net_to_recipient
        )

        updated_sender = await self.db.get_user(sender_id)
        return {
            "amount": amount,
            "tax_on_transfer": tax_on_transfer,
            "net_to_recipient": net_to_recipient,
            "sender_balance": updated_sender["balance"] if updated_sender else 0,
        }
