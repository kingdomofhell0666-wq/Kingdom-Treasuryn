import json
from typing import Dict, Any, List, Optional
from ..database import Database
from ..utils.skins import (
    get_skin, get_all_skins, SKINS, TITLES_CATALOG,
    DEFAULT_TITLE, DEFAULT_SKIN_ID, Title,
)


class CosmeticService:
    """
    Manages card skins and titles.

    - Skins and titles are purchased with DevilCoins from the main wallet.
    - owned_skins / owned_titles stored as JSON arrays in users table.
    - equipped_skin / equipped_title stored as TEXT fields.
    - The "default" skin and "Unmarked" title are always free.
    """

    def __init__(self, db: Database):
        self.db = db

    # ─── Helpers ──────────────────────────────────────────────

    def _parse_owned(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    async def _get_user(self, discord_id: str) -> dict:
        user = await self.db.get_user(discord_id)
        if not user:
            raise ValueError("User not found. Use any economy command first.")
        return user

    # ─── Skin queries ─────────────────────────────────────────

    def all_skins(self) -> Dict[str, Any]:
        return {sid: s for sid, s in get_all_skins().items()}

    async def get_owned_skins(self, discord_id: str) -> List[str]:
        user = await self._get_user(discord_id)
        owned = self._parse_owned(user.get("owned_skins", "[]"))
        if DEFAULT_SKIN_ID not in owned:
            owned = [DEFAULT_SKIN_ID] + owned
        return owned

    async def get_equipped_skin_id(self, discord_id: str) -> str:
        user = await self._get_user(discord_id)
        return user.get("equipped_skin") or DEFAULT_SKIN_ID

    async def buy_skin(self, discord_id: str, skin_id: str) -> Dict[str, Any]:
        """Purchase a skin with DC. Raises ValueError on any failure."""
        if skin_id not in SKINS:
            raise ValueError(
                f"The skin **{skin_id}** does not exist. Use `/skins` to see available options."
            )
        skin = SKINS[skin_id]
        if skin.price_dc == 0:
            raise ValueError(
                f"**{skin.name}** is free and already in your possession."
            )

        user = await self._get_user(discord_id)
        owned = self._parse_owned(user.get("owned_skins", "[]"))
        if DEFAULT_SKIN_ID not in owned:
            owned = [DEFAULT_SKIN_ID] + owned

        if skin_id in owned:
            raise ValueError(
                f"You already own the **{skin.name}** skin. Use `/equip-skin` to activate it."
            )
        if user["balance"] < skin.price_dc:
            needed = skin.price_dc - user["balance"]
            raise ValueError(
                f"Insufficient funds. You need **{needed:,} DC** more to acquire **{skin.name}**."
            )

        # Deduct DC and grant skin
        await self.db.update_balance(discord_id, -skin.price_dc)
        owned.append(skin_id)
        await self.db.set_owned_skins(discord_id, json.dumps(owned))
        await self.db.log_transaction(
            tx_type="skin_purchase",
            from_account=f"user:{discord_id}",
            to_account="kingdom_mint",
            amount=skin.price_dc,
            note=f"Skin purchase: {skin.name}",
        )

        updated = await self.db.get_user(discord_id)
        return {
            "skin": skin,
            "cost": skin.price_dc,
            "new_balance": updated["balance"] if updated else 0,
        }

    async def equip_skin(self, discord_id: str, skin_id: str) -> Dict[str, Any]:
        if skin_id not in SKINS:
            raise ValueError(
                f"The skin **{skin_id}** does not exist. Use `/skins` to see available options."
            )
        owned = await self.get_owned_skins(discord_id)
        if skin_id not in owned:
            raise ValueError(
                f"You do not own the **{SKINS[skin_id].name}** skin. Use `/buy-skin` to purchase it."
            )
        await self.db.set_equipped_skin(discord_id, skin_id)
        return {"skin_id": skin_id, "skin": get_skin(skin_id)}

    async def grant_skin(self, discord_id: str, skin_id: str):
        """Grant a skin to a user without cost (admin / events)."""
        if skin_id not in SKINS:
            raise ValueError(f"Unknown skin: {skin_id}")
        owned = await self.get_owned_skins(discord_id)
        if skin_id not in owned:
            owned.append(skin_id)
            await self.db.set_owned_skins(discord_id, json.dumps(owned))

    # ─── Title queries ────────────────────────────────────────

    def all_titles(self) -> Dict[str, Title]:
        return TITLES_CATALOG

    async def get_owned_titles(self, discord_id: str) -> List[str]:
        user = await self._get_user(discord_id)
        owned = self._parse_owned(user.get("owned_titles", "[]"))
        if DEFAULT_TITLE not in owned:
            owned = [DEFAULT_TITLE] + owned
        return owned

    async def get_equipped_title(self, discord_id: str) -> str:
        user = await self._get_user(discord_id)
        return user.get("equipped_title") or DEFAULT_TITLE

    async def buy_title(self, discord_id: str, title_name: str) -> Dict[str, Any]:
        """Purchase a title with DC. Raises ValueError on any failure."""
        if title_name not in TITLES_CATALOG:
            raise ValueError(
                f"The title **{title_name}** does not exist. Use `/titles` to browse available titles."
            )
        title = TITLES_CATALOG[title_name]
        if title.price_dc == 0:
            raise ValueError(
                f"**{title.name}** is free and already in your possession."
            )

        user = await self._get_user(discord_id)
        owned = self._parse_owned(user.get("owned_titles", "[]"))
        if DEFAULT_TITLE not in owned:
            owned = [DEFAULT_TITLE] + owned

        if title_name in owned:
            raise ValueError(
                f"You already own the title **{title.name}**. Use `/equip-title` to activate it."
            )
        if user["balance"] < title.price_dc:
            needed = title.price_dc - user["balance"]
            raise ValueError(
                f"Insufficient funds. You need **{needed:,} DC** more to acquire **{title.name}**."
            )

        # Deduct DC and grant title
        await self.db.update_balance(discord_id, -title.price_dc)
        owned.append(title_name)
        await self.db.set_owned_titles(discord_id, json.dumps(owned))
        await self.db.log_transaction(
            tx_type="title_purchase",
            from_account=f"user:{discord_id}",
            to_account="kingdom_mint",
            amount=title.price_dc,
            note=f"Title purchase: {title.name}",
        )

        updated = await self.db.get_user(discord_id)
        return {
            "title": title,
            "cost": title.price_dc,
            "new_balance": updated["balance"] if updated else 0,
        }

    async def equip_title(self, discord_id: str, title_name: str) -> Dict[str, Any]:
        if title_name not in TITLES_CATALOG:
            raise ValueError(
                f"The title **{title_name}** does not exist. Use `/titles` to browse available titles."
            )
        owned = await self.get_owned_titles(discord_id)
        if title_name not in owned:
            raise ValueError(
                f"You do not own the title **{title_name}**. Use `/buy-title` to purchase it."
            )
        await self.db.set_equipped_title(discord_id, title_name)
        return {"title": TITLES_CATALOG[title_name]}

    async def grant_title(self, discord_id: str, title_name: str):
        """Grant a title to a user without cost (admin / events)."""
        if title_name not in TITLES_CATALOG:
            raise ValueError(f"Unknown title: {title_name}")
        owned = await self.get_owned_titles(discord_id)
        if title_name not in owned:
            owned.append(title_name)
            await self.db.set_owned_titles(discord_id, json.dumps(owned))
