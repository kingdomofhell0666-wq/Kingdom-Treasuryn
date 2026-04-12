from ..database import Database


class TransactionService:
    def __init__(self, db: Database):
        self.db = db

    async def grind_reward(self, guild_id: str, discord_id: str, gross: int, tax: int, net: int):
        user = f"user:{discord_id}"
        await self.db.log_transaction(guild_id, "grind_gross", "kingdom_mint", user, gross, "Infernal mines yield")
        if tax > 0:
            await self.db.log_transaction(guild_id, "grind_tax", user, "treasury", tax, "Kingdom tax on grind")
            await self.db.update_treasury(guild_id, tax)
            await self.db.add_taxes_paid(guild_id, discord_id, tax)
        if net > 0:
            await self.db.update_balance(guild_id, discord_id, net)

    async def tribute_reward(self, guild_id: str, discord_id: str, gross: int, tax: int, net: int):
        user = f"user:{discord_id}"
        # Deduct the full gross from the Treasury (tax stays in treasury, net goes to user)
        await self.db.update_treasury(guild_id, -gross)
        await self.db.log_transaction(guild_id, "tribute_gross", "treasury", user, gross, "Tribute paid from Kingdom Treasury")
        if tax > 0:
            await self.db.update_treasury(guild_id, tax)
            await self.db.log_transaction(guild_id, "tribute_tax", user, "treasury", tax, "Kingdom tax returned to Treasury")
            await self.db.add_taxes_paid(guild_id, discord_id, tax)
        if net > 0:
            await self.db.update_balance(guild_id, discord_id, net)

    async def transfer_funds(self, guild_id: str, sender_id: str, recipient_id: str, amount: int, tax: int, net_to_recipient: int):
        sender    = f"user:{sender_id}"
        recipient = f"user:{recipient_id}"
        await self.db.log_transaction(guild_id, "transfer", sender, recipient, amount, "Wealth transfer")
        await self.db.update_balance(guild_id, sender_id, -amount)
        if tax > 0:
            await self.db.log_transaction(guild_id, "transfer_tax", sender, "treasury", tax, "Transfer levy")
            await self.db.update_treasury(guild_id, tax)
            await self.db.add_taxes_paid(guild_id, sender_id, tax)
        await self.db.update_balance(guild_id, recipient_id, net_to_recipient)

    async def ascension_payment(self, guild_id: str, discord_id: str, rank_name: str, cost: int):
        user         = f"user:{discord_id}"
        treasury_cut = int(cost * 0.10)
        burned       = cost - treasury_cut
        await self.db.log_transaction(guild_id, "ascend_debit", user, "treasury", cost, f"Ascension to {rank_name}")
        await self.db.update_balance(guild_id, discord_id, -cost)
        await self.db.log_transaction(guild_id, "ascend_treasury", "kingdom_mint", "treasury", treasury_cut, f"Treasury cut: {rank_name}")
        await self.db.update_treasury(guild_id, treasury_cut)
        await self.db.log_transaction(guild_id, "ascend_burn", user, "void", burned, f"Burned on ascension to {rank_name}")
        await self.db.set_rank(guild_id, discord_id, rank_name)
