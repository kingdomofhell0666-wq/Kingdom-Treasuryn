from ..database import Database


class TreasuryService:
    def __init__(self, db: Database):
        self.db = db

    async def get_balance(self) -> int:
        return await self.db.get_treasury_balance()

    async def deposit(self, amount: int, note: str = "Treasury deposit"):
        await self.db.update_treasury(amount)
        await self.db.log_transaction("treasury_deposit", "kingdom_mint", "treasury", amount, note)

    async def withdraw(self, amount: int, note: str = "Treasury withdrawal"):
        balance = await self.db.get_treasury_balance()
        if amount > balance:
            raise ValueError("The Treasury does not hold sufficient reserves.")
        await self.db.update_treasury(-amount)
        await self.db.log_transaction("treasury_withdraw", "treasury", "void", amount, note)
