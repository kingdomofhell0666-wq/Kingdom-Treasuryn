import random
from typing import Tuple, Dict, Any
from ..database import Database
from .transaction_service import TransactionService
from .rank_service import RankService


class EconomyService:
    def __init__(self, db: Database):
        self.db = db
        self.tx_service = TransactionService(db)
        self.rank_service = RankService()

    GRIND_OUTCOMES = [
        (0.60, (250, 350)),
        (0.20, (100, 200)),
        (0.10, (0, 0)),
        (0.07, (400, 600)),
        (0.03, (800, 1200)),
    ]

    async def grind(self, discord_id: str, username: str) -> Dict[str, Any]:
        user = await self.db.upsert_user(discord_id, username)

        roll = random.random()
        cumulative = 0.0
        gross = 0
        outcome_label = "failure"

        for chance, (low, high) in self.GRIND_OUTCOMES:
            cumulative += chance
            if roll < cumulative:
                if low == 0 and high == 0:
                    gross = 0
                    outcome_label = "failure"
                elif high <= 200:
                    gross = random.randint(low, high)
                    outcome_label = "meager"
                elif high <= 350:
                    gross = random.randint(low, high)
                    outcome_label = "common"
                elif high <= 600:
                    gross = random.randint(low, high)
                    outcome_label = "rich"
                else:
                    gross = random.randint(low, high)
                    outcome_label = "legendary"
                break

        tax_rate = self.rank_service.get_tax_rate(user["rank"])
        tax_amount = int(gross * tax_rate)
        net = gross - tax_amount

        if net > 0:
            await self.tx_service.grind_reward(discord_id, gross, tax_amount, net)

        await self.db.increment_grind_count(discord_id)

        updated_user = await self.db.get_user(discord_id)

        return {
            "gross": gross,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "net": net,
            "outcome_label": outcome_label,
            "new_balance": updated_user["balance"] if updated_user else 0,
        }

    async def tribute(self, discord_id: str, username: str) -> Dict[str, Any]:
        await self.db.upsert_user(discord_id, username)

        base = random.randint(1000, 2000)
        grind_count = await self.db.get_grind_count_24h(discord_id)
        bonus = 200 if grind_count >= 5 else 0
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
        self, sender_id: str, sender_name: str, recipient_id: str, recipient_name: str, amount: int
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
        updated_recipient = await self.db.get_user(recipient_id)

        return {
            "amount": amount,
            "tax_on_transfer": tax_on_transfer,
            "net_to_recipient": net_to_recipient,
            "sender_balance": updated_sender["balance"] if updated_sender else 0,
        }
