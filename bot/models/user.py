from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    discord_id: str
    username: str
    balance: int = 0
    rank: str = "Forsaken"
    title: str = "Unmarked"
    duels_won: int = 0
    duels_lost: int = 0
    taxes_paid: int = 0
    owned_titles: str = "[]"
    equipped_title: Optional[str] = None
    owned_skins: str = "[]"
    equipped_skin: Optional[str] = None
    grind_count_24h: int = 0
    last_grind_reset: Optional[str] = None
