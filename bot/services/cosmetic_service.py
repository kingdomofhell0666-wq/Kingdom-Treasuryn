import json
from typing import Dict, Any, List, Optional
from ..database import Database
from ..utils.skins import get_skin, get_all_skins, SKINS, TITLES, DEFAULT_TITLE, DEFAULT_SKIN_ID


class CosmeticService:
    """
    Manages card skins and titles.

    - owned_skins  / owned_titles  stored as JSON arrays in users table.
    - equipped_skin / equipped_title stored as TEXT fields.
    - All users start with the "default" skin and "Unmarked" title unlocked.
    """

    def __init__(self, db: Database):
        self.db = db

    # ─── Internal helpers ─────────────────────────────────────

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

    async def equip_skin(self, discord_id: str, skin_id: str) -> Dict[str, Any]:
        if skin_id not in SKINS:
            raise ValueError(
                f"The skin **{skin_id}** does not exist. Use `/skins` to see available options."
            )
        owned = await self.get_owned_skins(discord_id)
        if skin_id not in owned:
            raise ValueError(
                f"You do not own the **{SKINS[skin_id].name}** skin. Acquire it from the Black Market."
            )
        await self.db.set_equipped_skin(discord_id, skin_id)
        return {"skin_id": skin_id, "skin": get_skin(skin_id)}

    async def grant_skin(self, discord_id: str, skin_id: str):
        """Grant a skin to a user (called from black market or admin)."""
        if skin_id not in SKINS:
            raise ValueError(f"Unknown skin: {skin_id}")
        owned = await self.get_owned_skins(discord_id)
        if skin_id not in owned:
            owned.append(skin_id)
            await self.db.set_owned_skins(discord_id, json.dumps(owned))

    # ─── Title queries ────────────────────────────────────────

    def all_titles(self) -> List[str]:
        return TITLES

    async def get_owned_titles(self, discord_id: str) -> List[str]:
        user = await self._get_user(discord_id)
        owned = self._parse_owned(user.get("owned_titles", "[]"))
        if DEFAULT_TITLE not in owned:
            owned = [DEFAULT_TITLE] + owned
        return owned

    async def get_equipped_title(self, discord_id: str) -> str:
        user = await self._get_user(discord_id)
        return user.get("equipped_title") or DEFAULT_TITLE

    async def equip_title(self, discord_id: str, title: str) -> Dict[str, Any]:
        owned = await self.get_owned_titles(discord_id)
        if title not in owned:
            raise ValueError(
                f"You do not own the title **{title}**. Acquire it from the Black Market or through Kingdom events."
            )
        await self.db.set_equipped_title(discord_id, title)
        return {"title": title}

    async def grant_title(self, discord_id: str, title: str):
        """Grant a title to a user (called from events or admin)."""
        owned = await self.get_owned_titles(discord_id)
        if title not in owned:
            owned.append(title)
            await self.db.set_owned_titles(discord_id, json.dumps(owned))
