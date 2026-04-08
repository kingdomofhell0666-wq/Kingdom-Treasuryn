import random
from typing import Dict, Any
from ..database import Database
from .transaction_service import TransactionService
from .rank_service import RankService


class EconomyService:
    def __init__(self, db: Database):
        self.db = db
        self.tx_service = TransactionService(db)
        self.rank_service = RankService()

    GRIND_SUCCESS_CHANCE = 0.90
    GRIND_REWARD_MIN = 250
    GRIND_REWARD_MAX = 350

    TRIBUTE_BASE_MIN = 500
    TRIBUTE_BASE_MAX = 700
    TRIBUTE_GRIND_BONUS = 200
    TRIBUTE_GRIND_THRESHOLD = 5

    async def grind(self, discord_id: str, username: str) -> Dict[str, Any]:
        user = await self.db.upsert_user(discord_id, username)

        success = random.random() < self.GRIND_SUCCESS_CHANCE
        gross = random.randint(self.GRIND_REWARD_MIN, self.GRIND_REWARD_MAX) if success else 0

        tax_rate = self.rank_service.get_tax_rate(user["rank"])
        tax_amount = int(gross * tax_rate)
        net = gross - tax_amount

        if net > 0:
            await self.tx_service.grind_reward(discord_id, gross, tax_amount, net)

        await self.db.increment_grind_count(discord_id)

        updated_user = await self.db.get_user(discord_id)

        return {
            "success": success,
            "gross": gross,
            "tax_rate": tax_rate,
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
