import json
from typing import Dict, Any, List, Optional
from ..database import Database
from ..utils.skins import (
    get_skin, get_all_skins, SKINS, TITLES_CATALOG,
    DEFAULT_TITLE, DEFAULT_SKIN_ID,
)


class CosmeticService:
    def __init__(self, db: Database):
        self.db = db

    def _parse_owned(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    async def _get_user(self, guild_id: str, discord_id: str) -> dict:
        user = await self.db.get_user(guild_id, discord_id)
        if not user:
            raise ValueError("User not found. Use any economy command first.")
        return user

    def all_skins(self) -> Dict[str, Any]:
        return {sid: s for sid, s in get_all_skins().items()}

    async def get_owned_skins(self, guild_id: str, discord_id: str) -> List[str]:
        user  = await self._get_user(guild_id, discord_id)
        owned = self._parse_owned(user.get("owned_skins", "[]"))
        if DEFAULT_SKIN_ID not in owned:
            owned = [DEFAULT_SKIN_ID] + owned
        return owned

    async def get_equipped_skin_id(self, guild_id: str, discord_id: str) -> str:
        user = await self._get_user(guild_id, discord_id)
        return user.get("equipped_skin") or DEFAULT_SKIN_ID

    async def buy_skin(self, guild_id: str, discord_id: str, skin_id: str) -> Dict[str, Any]:
        if skin_id not in SKINS:
            raise ValueError(f"The skin **{skin_id}** does not exist.")
        skin = SKINS[skin_id]
        if skin.price_dc == 0:
            raise ValueError(f"**{skin.name}** is free and already yours.")
        user  = await self._get_user(guild_id, discord_id)
        owned = self._parse_owned(user.get("owned_skins", "[]"))
        if skin_id in owned:
            raise ValueError(f"You already own **{skin.name}**.")
        if user["balance"] < skin.price_dc:
            needed = skin.price_dc - user["balance"]
            raise ValueError(f"Insufficient funds. You need **{needed:,}** <:devilcoinStack:1492184333392412692> more.")
        owned.append(skin_id)
        await self.db.update_balance(guild_id, discord_id, -skin.price_dc)
        await self.db.set_owned_skins(guild_id, discord_id, json.dumps(owned))
        await self.db.log_transaction(guild_id, "skin_purchase", f"user:{discord_id}", "void", skin.price_dc, f"Skin purchased: {skin_id}")
        updated = await self.db.get_user(guild_id, discord_id)
        return {"skin": skin, "cost": skin.price_dc, "new_balance": updated["balance"] if updated else 0}

    async def equip_skin(self, guild_id: str, discord_id: str, skin_id: str) -> Dict[str, Any]:
        if skin_id not in SKINS:
            raise ValueError(f"Unknown skin: **{skin_id}**.")
        user  = await self._get_user(guild_id, discord_id)
        owned = self._parse_owned(user.get("owned_skins", "[]"))
        if skin_id != DEFAULT_SKIN_ID and skin_id not in owned:
            raise ValueError(f"You do not own **{SKINS[skin_id].name}**. Purchase it first.")
        await self.db.set_equipped_skin(guild_id, discord_id, skin_id)
        return {"skin": SKINS[skin_id]}

    async def get_owned_titles(self, guild_id: str, discord_id: str) -> List[str]:
        user = await self._get_user(guild_id, discord_id)
        return self._parse_owned(user.get("owned_titles", "[]"))

    async def get_equipped_title(self, guild_id: str, discord_id: str) -> str:
        user = await self._get_user(guild_id, discord_id)
        return user.get("equipped_title") or DEFAULT_TITLE

    async def buy_title(self, guild_id: str, discord_id: str, title_name: str) -> Dict[str, Any]:
        if title_name not in TITLES_CATALOG:
            raise ValueError(f"Unknown title: **{title_name}**.")
        title = TITLES_CATALOG[title_name]
        if title.price_dc == 0:
            raise ValueError(f"**{title.name}** is free.")
        user  = await self._get_user(guild_id, discord_id)
        owned = self._parse_owned(user.get("owned_titles", "[]"))
        if title_name in owned:
            raise ValueError(f"You already own **{title.name}**.")
        if user["balance"] < title.price_dc:
            needed = title.price_dc - user["balance"]
            raise ValueError(f"Insufficient funds. You need **{needed:,}** <:devilcoinStack:1492184333392412692> more.")
        owned.append(title_name)
        await self.db.update_balance(guild_id, discord_id, -title.price_dc)
        await self.db.set_owned_titles(guild_id, discord_id, json.dumps(owned))
        await self.db.log_transaction(guild_id, "title_purchase", f"user:{discord_id}", "void", title.price_dc, f"Title purchased: {title_name}")
        updated = await self.db.get_user(guild_id, discord_id)
        return {"title": title, "cost": title.price_dc, "new_balance": updated["balance"] if updated else 0}

    async def equip_title(self, guild_id: str, discord_id: str, title_name: str):
        if title_name not in TITLES_CATALOG:
            raise ValueError(f"Unknown title: **{title_name}**.")
        user  = await self._get_user(guild_id, discord_id)
        owned = self._parse_owned(user.get("owned_titles", "[]"))
        title = TITLES_CATALOG[title_name]
        if title.price_dc > 0 and title_name not in owned:
            raise ValueError(f"You do not own **{title_name}**. Purchase it first.")
        await self.db.set_equipped_title(guild_id, discord_id, title_name)
