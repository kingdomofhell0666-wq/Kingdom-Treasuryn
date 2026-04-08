import random
import time
from typing import List, Dict, Any, Optional
from ..database import Database


# Full pool of black market items
BLACKMARKET_POOL: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Shadow Tax Seal",
        "description": "Your next 3 grinds are exempt from Kingdom tax.",
        "cost": 1_500,
        "risk_increase": 20,
        "effect_type": "tax_exempt",
        "effect_value": 0.0,
        "effect_uses": 3,
    },
    {
        "id": 2,
        "name": "Corrupt Ledger",
        "description": "Reduces your effective tax rate by 3% for your next 5 grinds.",
        "cost": 800,
        "risk_increase": 15,
        "effect_type": "tax_reduction",
        "effect_value": 0.03,
        "effect_uses": 5,
    },
    {
        "id": 3,
        "name": "Infernal Stimulant",
        "description": "Forces a rich vein or jackpot outcome on your next grind.",
        "cost": 2_000,
        "risk_increase": 10,
        "effect_type": "grind_boost",
        "effect_value": 1.0,
        "effect_uses": 1,
    },
    {
        "id": 4,
        "name": "Cerberus Bribe",
        "description": "Immediately reduces your risk score by 25 points.",
        "cost": 3_000,
        "risk_increase": 0,
        "effect_type": "risk_reduce",
        "effect_value": 25.0,
        "effect_uses": 1,
    },
    {
        "id": 5,
        "name": "Shadow Cloak",
        "description": "Grants immunity from the next Cerberus audit triggered against you.",
        "cost": 2_500,
        "risk_increase": 35,
        "effect_type": "audit_immunity",
        "effect_value": 1.0,
        "effect_uses": 1,
    },
    {
        "id": 6,
        "name": "Miner's Charm",
        "description": "Adds +100 DC to your next 5 grind earnings.",
        "cost": 600,
        "risk_increase": 5,
        "effect_type": "grind_bonus",
        "effect_value": 100.0,
        "effect_uses": 5,
    },
    {
        "id": 7,
        "name": "Void Laundry",
        "description": "Erases 30 points of risk score. Leaves no trace in the ledger.",
        "cost": 4_000,
        "risk_increase": 0,
        "effect_type": "risk_reduce",
        "effect_value": 30.0,
        "effect_uses": 1,
    },
    {
        "id": 8,
        "name": "Fortune Seal",
        "description": "Raises your grind reward ceiling by +200 DC for the next 3 grinds.",
        "cost": 1_200,
        "risk_increase": 10,
        "effect_type": "grind_ceiling",
        "effect_value": 200.0,
        "effect_uses": 3,
    },
]

ROTATION_WINDOW = 6 * 3600  # 6 hours in seconds
ITEMS_PER_ROTATION = 4


def get_active_items() -> List[Dict[str, Any]]:
    """
    Returns the 4 currently active black market items.
    Rotates deterministically every 6 hours using time-based seed.
    """
    slot = int(time.time() // ROTATION_WINDOW)
    rng = random.Random(slot)
    return rng.sample(BLACKMARKET_POOL, min(ITEMS_PER_ROTATION, len(BLACKMARKET_POOL)))


def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    for item in BLACKMARKET_POOL:
        if item["id"] == item_id:
            return item
    return None


class BlackMarketService:
    def __init__(self, db: Database):
        self.db = db

    def get_active_items(self) -> List[Dict[str, Any]]:
        return get_active_items()

    async def purchase(self, discord_id: str, username: str, item_id: int) -> Dict[str, Any]:
        active = get_active_items()
        active_ids = {i["id"] for i in active}

        if item_id not in active_ids:
            raise ValueError("This item is no longer available. The market has shifted.")

        item = get_item_by_id(item_id)
        if not item:
            raise ValueError("Unknown item.")

        user = await self.db.upsert_user(discord_id, username)
        cost = item["cost"]
        old_risk = user.get("risk_score", 0)

        if user["balance"] < cost:
            needed = cost - user["balance"]
            raise ValueError(
                f"Insufficient funds. You need {needed:,} more DC to acquire this item."
            )

        # Deduct cost (all burns to void — no treasury cut for black market)
        await self.db.update_balance(discord_id, -cost)
        await self.db.log_transaction(
            "blackmarket_purchase",
            f"user:{discord_id}",
            "void",
            cost,
            f"Black Market: {item['name']}",
        )

        # Apply instant effects (risk_reduce)
        risk_delta = item["risk_increase"]
        if item["effect_type"] == "risk_reduce":
            await self.db.adjust_risk_score(discord_id, -int(item["effect_value"]))
        else:
            # Grant perk
            await self.db.add_perk(
                discord_id,
                item["effect_type"],
                item["effect_value"],
                item["effect_uses"],
            )

        # Apply risk increase
        if risk_delta > 0:
            await self.db.adjust_risk_score(discord_id, risk_delta)

        updated_user = await self.db.get_user(discord_id)
        new_risk = updated_user.get("risk_score", 0) if updated_user else 0
        return {
            "item": item,
            "cost": cost,
            "new_balance": updated_user["balance"] if updated_user else 0,
            "old_risk": old_risk,
            "new_risk": new_risk,
            "risk_delta": new_risk - old_risk,
        }
