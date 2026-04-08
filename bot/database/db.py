import aiosqlite
import json
from typing import Optional, List
from datetime import datetime, timezone


DB_PATH = "kingdom_treasury.db"


class Database:
    def __init__(self):
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self._db = await aiosqlite.connect(DB_PATH)
        self._db.row_factory = aiosqlite.Row
        await self._init_schema()

    async def close(self):
        if self._db:
            await self._db.close()

    async def _init_schema(self):
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id      TEXT PRIMARY KEY,
                username        TEXT NOT NULL,
                balance         INTEGER NOT NULL DEFAULT 0,
                rank            TEXT NOT NULL DEFAULT 'Forsaken',
                title           TEXT NOT NULL DEFAULT 'Unmarked',
                duels_won       INTEGER NOT NULL DEFAULT 0,
                duels_lost      INTEGER NOT NULL DEFAULT 0,
                taxes_paid      INTEGER NOT NULL DEFAULT 0,
                owned_titles    TEXT NOT NULL DEFAULT '[]',
                equipped_title  TEXT,
                owned_skins     TEXT NOT NULL DEFAULT '[]',
                equipped_skin   TEXT,
                grind_count_24h INTEGER NOT NULL DEFAULT 0,
                last_grind_reset TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_type      TEXT NOT NULL,
                from_account TEXT NOT NULL,
                to_account   TEXT NOT NULL,
                amount       INTEGER NOT NULL,
                note         TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS treasury (
                id      INTEGER PRIMARY KEY CHECK (id = 1),
                balance INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS cooldowns (
                discord_id  TEXT NOT NULL,
                action      TEXT NOT NULL,
                last_used   TEXT NOT NULL,
                PRIMARY KEY (discord_id, action)
            );

            INSERT OR IGNORE INTO treasury (id, balance) VALUES (1, 0);
        """)
        await self._db.commit()

    async def get_user(self, discord_id: str) -> Optional[dict]:
        async with self._db.execute(
            "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def upsert_user(self, discord_id: str, username: str) -> dict:
        await self._db.execute(
            """
            INSERT INTO users (discord_id, username)
            VALUES (?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET username = excluded.username
            """,
            (discord_id, username),
        )
        await self._db.commit()
        return await self.get_user(discord_id)

    async def update_balance(self, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET balance = balance + ? WHERE discord_id = ?",
            (amount, discord_id),
        )
        await self._db.commit()

    async def set_balance(self, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET balance = ? WHERE discord_id = ?",
            (amount, discord_id),
        )
        await self._db.commit()

    async def set_rank(self, discord_id: str, rank: str):
        await self._db.execute(
            "UPDATE users SET rank = ? WHERE discord_id = ?",
            (rank, discord_id),
        )
        await self._db.commit()

    async def add_taxes_paid(self, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET taxes_paid = taxes_paid + ? WHERE discord_id = ?",
            (amount, discord_id),
        )
        await self._db.commit()

    async def increment_grind_count(self, discord_id: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        user = await self.get_user(discord_id)
        if not user:
            return
        last_reset = user["last_grind_reset"]
        reset_needed = True
        if last_reset:
            last_dt = datetime.fromisoformat(last_reset).replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - last_dt).total_seconds() < 86400:
                reset_needed = False
        if reset_needed:
            await self._db.execute(
                "UPDATE users SET grind_count_24h = 1, last_grind_reset = ? WHERE discord_id = ?",
                (now_str, discord_id),
            )
        else:
            await self._db.execute(
                "UPDATE users SET grind_count_24h = grind_count_24h + 1 WHERE discord_id = ?",
                (discord_id,),
            )
        await self._db.commit()

    async def get_grind_count_24h(self, discord_id: str) -> int:
        user = await self.get_user(discord_id)
        if not user:
            return 0
        last_reset = user["last_grind_reset"]
        if not last_reset:
            return 0
        last_dt = datetime.fromisoformat(last_reset).replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - last_dt).total_seconds() >= 86400:
            return 0
        return user["grind_count_24h"]

    async def get_treasury_balance(self) -> int:
        async with self._db.execute("SELECT balance FROM treasury WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row["balance"] if row else 0

    async def update_treasury(self, amount: int):
        await self._db.execute(
            "UPDATE treasury SET balance = balance + ? WHERE id = 1",
            (amount,),
        )
        await self._db.commit()

    async def log_transaction(
        self,
        tx_type: str,
        from_account: str,
        to_account: str,
        amount: int,
        note: Optional[str] = None,
    ):
        await self._db.execute(
            "INSERT INTO transactions (tx_type, from_account, to_account, amount, note) VALUES (?,?,?,?,?)",
            (tx_type, from_account, to_account, amount, note),
        )
        await self._db.commit()

    async def get_cooldown(self, discord_id: str, action: str) -> Optional[datetime]:
        async with self._db.execute(
            "SELECT last_used FROM cooldowns WHERE discord_id = ? AND action = ?",
            (discord_id, action),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return datetime.fromisoformat(row["last_used"]).replace(tzinfo=timezone.utc)
            return None

    async def set_cooldown(self, discord_id: str, action: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            """
            INSERT INTO cooldowns (discord_id, action, last_used)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id, action) DO UPDATE SET last_used = excluded.last_used
            """,
            (discord_id, action, now_str),
        )
        await self._db.commit()

    async def get_leaderboard(self, limit: int = 10) -> List[dict]:
        async with self._db.execute(
            "SELECT discord_id, username, balance, rank FROM users ORDER BY balance DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_kingdom_rank(self, discord_id: str) -> int:
        async with self._db.execute(
            """
            SELECT COUNT(*) + 1 AS kingdom_rank
            FROM users
            WHERE balance > (SELECT balance FROM users WHERE discord_id = ?)
            """,
            (discord_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row["kingdom_rank"] if row else 1

    async def get_all_transactions(self, discord_id: str, limit: int = 10) -> List[dict]:
        account = f"user:{discord_id}"
        async with self._db.execute(
            """
            SELECT * FROM transactions
            WHERE from_account = ? OR to_account = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (account, account, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
