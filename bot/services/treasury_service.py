from ..database import Database


class TreasuryService:
    def __init__(self, db: Database):
        self.db = db

    async def get_balance(self, guild_id: str) -> int:
        return await self.db.get_treasury_balance(guild_id)

    async def deposit(self, guild_id: str, amount: int, note: str = "Treasury deposit"):
        await self.db.update_treasury(guild_id, amount)
        await self.db.log_transaction(guild_id, "treasury_deposit", "kingdom_mint", "treasury", amount, note)

    async def withdraw(self, guild_id: str, amount: int, note: str = "Treasury withdrawal"):
        balance = await self.db.get_treasury_balance(guild_id)
        if amount > balance:
            raise ValueError("The Treasury does not hold sufficient reserves.")
        await self.db.update_treasury(guild_id, -amount)
        await self.db.log_transaction(guild_id, "treasury_withdraw", "treasury", "void", amount, note)
