from ..database import Database


class TransactionService:
    def __init__(self, db: Database):
        self.db = db

    async def grind_reward(self, discord_id: str, gross: int, tax: int, net: int):
        user = f"user:{discord_id}"
        await self.db.log_transaction("grind_gross", "kingdom_mint", user, gross, "Infernal mines yield")
        if tax > 0:
            await self.db.log_transaction("grind_tax", user, "treasury", tax, "Kingdom tax on grind")
            await self.db.update_treasury(tax)
            await self.db.add_taxes_paid(discord_id, tax)
        if net > 0:
            await self.db.update_balance(discord_id, net)

    async def tribute_reward(self, discord_id: str, gross: int, tax: int, net: int):
        user = f"user:{discord_id}"
        await self.db.log_transaction("tribute_gross", "kingdom_mint", user, gross, "Tribute from the realm")
        if tax > 0:
            await self.db.log_transaction("tribute_tax", user, "treasury", tax, "Kingdom tax on tribute")
            await self.db.update_treasury(tax)
            await self.db.add_taxes_paid(discord_id, tax)
        if net > 0:
            await self.db.update_balance(discord_id, net)

    async def transfer_funds(
        self,
        sender_id: str,
        recipient_id: str,
        amount: int,
        tax: int,
        net_to_recipient: int,
    ):
        sender = f"user:{sender_id}"
        recipient = f"user:{recipient_id}"
        await self.db.log_transaction("transfer", sender, recipient, amount, "Wealth transfer")
        await self.db.update_balance(sender_id, -amount)
        if tax > 0:
            await self.db.log_transaction("transfer_tax", sender, "treasury", tax, "Transfer levy")
            await self.db.update_treasury(tax)
            await self.db.add_taxes_paid(sender_id, tax)
        await self.db.update_balance(recipient_id, net_to_recipient)

    async def ascension_payment(self, discord_id: str, rank_name: str, cost: int):
        user = f"user:{discord_id}"
        treasury_cut = int(cost * 0.10)
        burned = cost - treasury_cut

        await self.db.log_transaction(
            "ascend_debit", user, "treasury", cost,
            f"Ascension to {rank_name}"
        )
        await self.db.update_balance(discord_id, -cost)

        await self.db.log_transaction(
            "ascend_treasury", "kingdom_mint", "treasury", treasury_cut,
            f"Treasury cut from ascension: {rank_name}"
        )
        await self.db.update_treasury(treasury_cut)

        await self.db.log_transaction(
            "ascend_burn", user, "void", burned,
            f"Burned on ascension to {rank_name}"
        )
        await self.db.set_rank(discord_id, rank_name)
