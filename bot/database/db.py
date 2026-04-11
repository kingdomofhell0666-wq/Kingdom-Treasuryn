"""
Kingdom Treasury — Database Layer
All live-economy tables are guild-scoped (guild_id + discord_id).
The `meta` table is global and is NEVER reset.
"""

import aiosqlite
import hashlib
import logging
from typing import Optional, List
from datetime import datetime, timezone

logger = logging.getLogger("kingdom_treasury")

DB_PATH       = "kingdom_treasury.db"
SCHEMA_VERSION = 2   # bumped when schema changes require a migration


class Database:
    def __init__(self):
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self._db = await aiosqlite.connect(DB_PATH)
        self._db.row_factory = aiosqlite.Row
        await self._ensure_meta_table()
        await self._migrate_if_needed()

    async def close(self):
        if self._db:
            await self._db.close()

    # ─── Meta (global, never reset) ───────────────────────────────────────────

    async def _ensure_meta_table(self):
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await self._db.commit()

    async def get_meta(self, key: str) -> Optional[str]:
        async with self._db.execute(
            "SELECT value FROM meta WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row["value"] if row else None

    async def set_meta(self, key: str, value: str):
        await self._db.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await self._db.commit()

    # ─── Schema migration ─────────────────────────────────────────────────────

    async def _migrate_if_needed(self):
        stored = await self.get_meta("schema_version")
        current = int(stored) if stored else 0

        if current < SCHEMA_VERSION:
            logger.info(
                f"Schema version {current} → {SCHEMA_VERSION}: rebuilding all economy tables."
            )
            await self._drop_economy_tables()
            await self._create_economy_tables()
            await self.set_meta("schema_version", str(SCHEMA_VERSION))
            logger.info("Schema migration complete.")
        else:
            # Tables already exist at correct version — just ensure they exist
            await self._create_economy_tables()

        # Additive migrations — safe to run every startup (errors ignored)
        await self._additive_migrations()

    async def _additive_migrations(self):
        """Add new columns to existing tables without wiping any data."""
        additive = [
            "ALTER TABLE missions ADD COLUMN description TEXT",
            "ALTER TABLE missions ADD COLUMN repeat_limit INTEGER",
            "ALTER TABLE users ADD COLUMN is_frozen INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN freeze_reason TEXT",
            "ALTER TABLE users ADD COLUMN frozen_by TEXT",
            "ALTER TABLE users ADD COLUMN frozen_at TEXT",
            # Economy pressure system
            "ALTER TABLE users ADD COLUMN sacrifice_active INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_downgrade_at TEXT",
            # Infernal Market — relics + badge equipping
            "ALTER TABLE users ADD COLUMN owned_relics TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN equipped_relic TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN equipped_badges TEXT NOT NULL DEFAULT '[]'",
        ]
        for stmt in additive:
            try:
                await self._db.execute(stmt)
                await self._db.commit()
            except Exception:
                pass  # column already exists — safe to ignore

    async def _drop_economy_tables(self):
        """Drop all live-economy tables so they can be recreated with guild_id."""
        for tbl in ("users", "transactions", "treasury", "cooldowns", "investments", "user_perks"):
            await self._db.execute(f"DROP TABLE IF EXISTS {tbl}")
        await self._db.commit()

    async def _create_economy_tables(self):
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id         TEXT NOT NULL,
                discord_id       TEXT NOT NULL,
                username         TEXT NOT NULL,
                balance          INTEGER NOT NULL DEFAULT 0,
                rank             TEXT NOT NULL DEFAULT 'Forsaken',
                taxes_paid       INTEGER NOT NULL DEFAULT 0,
                risk_score       INTEGER NOT NULL DEFAULT 0,
                owned_titles     TEXT NOT NULL DEFAULT '[]',
                equipped_title   TEXT,
                owned_skins      TEXT NOT NULL DEFAULT '[]',
                equipped_skin    TEXT,
                owned_badges     TEXT NOT NULL DEFAULT '[]',
                grind_count      INTEGER NOT NULL DEFAULT 0,
                grind_count_24h  INTEGER NOT NULL DEFAULT 0,
                last_grind_reset TEXT,
                tribute_count    INTEGER NOT NULL DEFAULT 0,
                created_at       TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (guild_id, discord_id)
            );

            CREATE TABLE IF NOT EXISTS treasury (
                guild_id TEXT PRIMARY KEY,
                balance  INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id     TEXT NOT NULL,
                tx_type      TEXT NOT NULL,
                from_account TEXT NOT NULL,
                to_account   TEXT NOT NULL,
                amount       INTEGER NOT NULL,
                note         TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cooldowns (
                guild_id   TEXT NOT NULL,
                discord_id TEXT NOT NULL,
                action     TEXT NOT NULL,
                last_used  TEXT NOT NULL,
                PRIMARY KEY (guild_id, discord_id, action)
            );

            CREATE TABLE IF NOT EXISTS investments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    TEXT NOT NULL,
                discord_id  TEXT NOT NULL,
                inv_type    TEXT NOT NULL,
                principal   INTEGER NOT NULL,
                matures_at  TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'active',
                payout      INTEGER,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS user_perks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id       TEXT NOT NULL,
                discord_id     TEXT NOT NULL,
                perk_type      TEXT NOT NULL,
                perk_value     REAL NOT NULL DEFAULT 0,
                uses_remaining INTEGER NOT NULL DEFAULT 1,
                created_at     TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS ascension_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id     TEXT NOT NULL,
                discord_id   TEXT NOT NULL,
                username     TEXT NOT NULL,
                rank         TEXT NOT NULL,
                ascended_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS missions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id         TEXT NOT NULL,
                title            TEXT NOT NULL,
                description      TEXT,
                reward           INTEGER NOT NULL,
                expires_at       TEXT,
                max_participants INTEGER,
                repeat_limit     INTEGER,
                required_rank    TEXT,
                entry_cost       INTEGER NOT NULL DEFAULT 0,
                status           TEXT NOT NULL DEFAULT 'active',
                message_id       TEXT,
                channel_id       TEXT NOT NULL DEFAULT '1488258105216209016',
                created_at       TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS mission_participants (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id   INTEGER NOT NULL,
                guild_id     TEXT NOT NULL,
                discord_id   TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'accepted',
                accepted_at  TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT,
                UNIQUE(mission_id, discord_id)
            );
        """)
        await self._db.commit()

    # ─── Reset ────────────────────────────────────────────────────────────────

    async def reset_guild_data(self, guild_id: str):
        """Hard-delete ALL economy data for a specific guild."""
        tables = [
            "users", "transactions", "treasury", "cooldowns", "investments",
            "user_perks", "ascension_history", "missions", "mission_participants",
        ]
        for tbl in tables:
            await self._db.execute(f"DELETE FROM {tbl} WHERE guild_id = ?", (guild_id,))
        await self._db.commit()
        logger.info(f"Guild {guild_id} — all economy data purged.")

    async def reset_all_data(self):
        """Hard-delete ALL economy data across every guild."""
        tables = [
            "users", "transactions", "treasury", "cooldowns", "investments",
            "user_perks", "ascension_history", "missions", "mission_participants",
        ]
        for tbl in tables:
            await self._db.execute(f"DELETE FROM {tbl}")
        await self._db.commit()
        logger.info("Global reset complete — all economy data purged.")

    # ─── Token fingerprint ────────────────────────────────────────────────────

    @staticmethod
    def compute_token_fingerprint(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:24]

    # ─── Users ────────────────────────────────────────────────────────────────

    async def get_user(self, guild_id: str, discord_id: str) -> Optional[dict]:
        async with self._db.execute(
            "SELECT * FROM users WHERE guild_id = ? AND discord_id = ?",
            (guild_id, discord_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def upsert_user(self, guild_id: str, discord_id: str, username: str) -> dict:
        await self._db.execute(
            """
            INSERT INTO users (guild_id, discord_id, username)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, discord_id) DO UPDATE SET username = excluded.username
            """,
            (guild_id, discord_id, username),
        )
        await self._db.commit()
        return await self.get_user(guild_id, discord_id)

    async def update_balance(self, guild_id: str, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET balance = balance + ? WHERE guild_id = ? AND discord_id = ?",
            (amount, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_balance(self, guild_id: str, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET balance = ? WHERE guild_id = ? AND discord_id = ?",
            (amount, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_rank(self, guild_id: str, discord_id: str, rank: str):
        await self._db.execute(
            "UPDATE users SET rank = ? WHERE guild_id = ? AND discord_id = ?",
            (rank, guild_id, discord_id),
        )
        await self._db.commit()

    async def add_taxes_paid(self, guild_id: str, discord_id: str, amount: int):
        await self._db.execute(
            "UPDATE users SET taxes_paid = taxes_paid + ? WHERE guild_id = ? AND discord_id = ?",
            (amount, guild_id, discord_id),
        )
        await self._db.commit()

    async def adjust_risk_score(self, guild_id: str, discord_id: str, delta: int):
        await self._db.execute(
            """
            UPDATE users
            SET risk_score = MAX(0, MIN(100, risk_score + ?))
            WHERE guild_id = ? AND discord_id = ?
            """,
            (delta, guild_id, discord_id),
        )
        await self._db.commit()

    async def increment_grind_count(self, guild_id: str, discord_id: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        user = await self.get_user(guild_id, discord_id)
        if not user:
            return
        last_reset = user.get("last_grind_reset")
        reset_needed = True
        if last_reset:
            last_dt = datetime.fromisoformat(last_reset).replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - last_dt).total_seconds() < 86400:
                reset_needed = False
        if reset_needed:
            await self._db.execute(
                """UPDATE users
                   SET grind_count_24h = 1,
                       last_grind_reset = ?,
                       grind_count = grind_count + 1
                   WHERE guild_id = ? AND discord_id = ?""",
                (now_str, guild_id, discord_id),
            )
        else:
            await self._db.execute(
                """UPDATE users
                   SET grind_count_24h = grind_count_24h + 1,
                       grind_count = grind_count + 1
                   WHERE guild_id = ? AND discord_id = ?""",
                (guild_id, discord_id),
            )
        await self._db.commit()

    async def increment_tribute_count(self, guild_id: str, discord_id: str):
        await self._db.execute(
            "UPDATE users SET tribute_count = tribute_count + 1 WHERE guild_id = ? AND discord_id = ?",
            (guild_id, discord_id),
        )
        await self._db.commit()

    async def get_grind_count_24h(self, guild_id: str, discord_id: str) -> int:
        user = await self.get_user(guild_id, discord_id)
        if not user:
            return 0
        last_reset = user.get("last_grind_reset")
        if not last_reset:
            return 0
        last_dt = datetime.fromisoformat(last_reset).replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - last_dt).total_seconds() >= 86400:
            return 0
        return user["grind_count_24h"]

    # Kingdom rank ordering: rank hierarchy (index) DESC, then balance DESC.
    # Mirrors PUBLIC_KINGDOM_RANKS in rank_service.py.
    # Chancellor is a staff role and is NOT part of the public rank hierarchy —
    # it does not appear here. Duke (14) is the highest public economy rank.
    _RANK_CASE = """
        CASE rank
            WHEN 'Forsaken'    THEN 0
            WHEN 'Vermin'      THEN 1
            WHEN 'Corrupted'   THEN 2
            WHEN 'Folklore'    THEN 3
            WHEN 'Mythology'   THEN 4
            WHEN 'Demonology'  THEN 5
            WHEN 'Eschatology' THEN 6
            WHEN 'Archangel'   THEN 7
            WHEN 'Archdemon'   THEN 8
            WHEN 'Knight'      THEN 9
            WHEN 'Baron'       THEN 10
            WHEN 'Viscount'    THEN 11
            WHEN 'Count'       THEN 12
            WHEN 'Marquis'     THEN 13
            WHEN 'Duke'        THEN 14
            ELSE 0
        END
    """

    async def get_leaderboard(self, guild_id: str, limit: int = 10) -> List[dict]:
        """
        Return top users sorted by public rank hierarchy first (Duke > … > Forsaken),
        then by balance descending for ties within the same rank.
        Matches /identity ordering exactly.  Chancellor is not part of the public hierarchy.
        """
        async with self._db.execute(
            f"""SELECT discord_id, username, balance, rank,
                       {self._RANK_CASE} AS rank_idx
               FROM users WHERE guild_id = ?
               ORDER BY rank_idx DESC, balance DESC LIMIT ?""",
            (guild_id, limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_kingdom_rank(self, guild_id: str, discord_id: str) -> int:
        """
        Return the user's 1-based kingdom rank position using rank hierarchy first,
        then balance for ties. Matches get_leaderboard ordering exactly.
        """
        async with self._db.execute(
            f"""
            SELECT COUNT(*) + 1 AS kingdom_rank
            FROM users
            WHERE guild_id = ?
              AND (
                {self._RANK_CASE} > (
                    SELECT {self._RANK_CASE}
                    FROM users WHERE guild_id = ? AND discord_id = ?
                )
                OR (
                    {self._RANK_CASE} = (
                        SELECT {self._RANK_CASE}
                        FROM users WHERE guild_id = ? AND discord_id = ?
                    )
                    AND balance > (
                        SELECT balance FROM users WHERE guild_id = ? AND discord_id = ?
                    )
                )
              )
            """,
            (guild_id, guild_id, discord_id, guild_id, discord_id, guild_id, discord_id),
        ) as cur:
            row = await cur.fetchone()
            return row["kingdom_rank"] if row else 1

    # ─── Treasury ─────────────────────────────────────────────────────────────

    async def get_treasury_balance(self, guild_id: str) -> int:
        async with self._db.execute(
            "SELECT balance FROM treasury WHERE guild_id = ?", (guild_id,)
        ) as cur:
            row = await cur.fetchone()
            return row["balance"] if row else 0

    async def update_treasury(self, guild_id: str, amount: int):
        await self._db.execute(
            """
            INSERT INTO treasury (guild_id, balance) VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET balance = balance + excluded.balance
            """,
            (guild_id, amount),
        )
        await self._db.commit()

    # ─── Transactions ─────────────────────────────────────────────────────────

    async def log_transaction(
        self,
        guild_id: str,
        tx_type: str,
        from_account: str,
        to_account: str,
        amount: int,
        note: Optional[str] = None,
    ):
        await self._db.execute(
            """INSERT INTO transactions
               (guild_id, tx_type, from_account, to_account, amount, note)
               VALUES (?,?,?,?,?,?)""",
            (guild_id, tx_type, from_account, to_account, amount, note),
        )
        await self._db.commit()

    async def get_user_transactions(
        self, guild_id: str, discord_id: str, limit: int = 10
    ) -> List[dict]:
        account = f"user:{discord_id}"
        async with self._db.execute(
            """
            SELECT * FROM transactions
            WHERE guild_id = ? AND (from_account = ? OR to_account = ?)
            ORDER BY created_at DESC LIMIT ?
            """,
            (guild_id, account, account, limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # alias used by audit_service
    async def get_all_transactions(
        self, guild_id: str, discord_id: str, limit: int = 10
    ) -> List[dict]:
        return await self.get_user_transactions(guild_id, discord_id, limit)

    # ─── Cooldowns ────────────────────────────────────────────────────────────

    async def get_cooldown(
        self, guild_id: str, discord_id: str, action: str
    ) -> Optional[datetime]:
        async with self._db.execute(
            "SELECT last_used FROM cooldowns WHERE guild_id = ? AND discord_id = ? AND action = ?",
            (guild_id, discord_id, action),
        ) as cur:
            row = await cur.fetchone()
            if row:
                return datetime.fromisoformat(row["last_used"]).replace(tzinfo=timezone.utc)
            return None

    async def set_cooldown(self, guild_id: str, discord_id: str, action: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            """
            INSERT INTO cooldowns (guild_id, discord_id, action, last_used)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, discord_id, action)
            DO UPDATE SET last_used = excluded.last_used
            """,
            (guild_id, discord_id, action, now_str),
        )
        await self._db.commit()

    # ─── Investments ──────────────────────────────────────────────────────────

    async def create_investment(
        self,
        guild_id: str,
        discord_id: str,
        inv_type: str,
        principal: int,
        matures_at: str,
    ) -> int:
        cur = await self._db.execute(
            """INSERT INTO investments (guild_id, discord_id, inv_type, principal, matures_at)
               VALUES (?, ?, ?, ?, ?)""",
            (guild_id, discord_id, inv_type, principal, matures_at),
        )
        await self._db.commit()
        return cur.lastrowid

    async def get_active_investments(self, guild_id: str, discord_id: str) -> List[dict]:
        async with self._db.execute(
            """SELECT * FROM investments
               WHERE guild_id = ? AND discord_id = ? AND status = 'active'
               ORDER BY created_at ASC""",
            (guild_id, discord_id),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_matured_investments(self, guild_id: str, discord_id: str) -> List[dict]:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        async with self._db.execute(
            """SELECT * FROM investments
               WHERE guild_id = ? AND discord_id = ? AND status = 'active' AND matures_at <= ?
               ORDER BY matures_at ASC""",
            (guild_id, discord_id, now_str),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def settle_investment(self, investment_id: int, payout: int, status: str = "collected"):
        await self._db.execute(
            "UPDATE investments SET status = ?, payout = ? WHERE id = ?",
            (status, payout, investment_id),
        )
        await self._db.commit()

    # ─── User Perks ───────────────────────────────────────────────────────────

    async def add_perk(
        self,
        guild_id: str,
        discord_id: str,
        perk_type: str,
        perk_value: float,
        uses: int,
    ):
        await self._db.execute(
            """INSERT INTO user_perks (guild_id, discord_id, perk_type, perk_value, uses_remaining)
               VALUES (?,?,?,?,?)""",
            (guild_id, discord_id, perk_type, perk_value, uses),
        )
        await self._db.commit()

    async def get_active_perks(self, guild_id: str, discord_id: str) -> List[dict]:
        async with self._db.execute(
            """SELECT * FROM user_perks
               WHERE guild_id = ? AND discord_id = ? AND uses_remaining > 0
               ORDER BY created_at ASC""",
            (guild_id, discord_id),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def consume_perk(self, perk_id: int):
        await self._db.execute(
            "UPDATE user_perks SET uses_remaining = uses_remaining - 1 WHERE id = ?",
            (perk_id,),
        )
        await self._db.commit()

    async def delete_perk(self, perk_id: int):
        await self._db.execute("DELETE FROM user_perks WHERE id = ?", (perk_id,))
        await self._db.commit()

    # ─── Cosmetics ────────────────────────────────────────────────────────────

    async def set_equipped_skin(self, guild_id: str, discord_id: str, skin_id: str):
        await self._db.execute(
            "UPDATE users SET equipped_skin = ? WHERE guild_id = ? AND discord_id = ?",
            (skin_id, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_owned_skins(self, guild_id: str, discord_id: str, skins_json: str):
        await self._db.execute(
            "UPDATE users SET owned_skins = ? WHERE guild_id = ? AND discord_id = ?",
            (skins_json, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_equipped_title(self, guild_id: str, discord_id: str, title: str):
        await self._db.execute(
            "UPDATE users SET equipped_title = ? WHERE guild_id = ? AND discord_id = ?",
            (title, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_owned_titles(self, guild_id: str, discord_id: str, titles_json: str):
        await self._db.execute(
            "UPDATE users SET owned_titles = ? WHERE guild_id = ? AND discord_id = ?",
            (titles_json, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_owned_badges(self, guild_id: str, discord_id: str, badges_json: str):
        await self._db.execute(
            "UPDATE users SET owned_badges = ? WHERE guild_id = ? AND discord_id = ?",
            (badges_json, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_owned_relics(self, guild_id: str, discord_id: str, relics_json: str):
        await self._db.execute(
            "UPDATE users SET owned_relics = ? WHERE guild_id = ? AND discord_id = ?",
            (relics_json, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_equipped_relic(self, guild_id: str, discord_id: str, relic_id: str):
        await self._db.execute(
            "UPDATE users SET equipped_relic = ? WHERE guild_id = ? AND discord_id = ?",
            (relic_id, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_equipped_badges(self, guild_id: str, discord_id: str, badges_json: str):
        await self._db.execute(
            "UPDATE users SET equipped_badges = ? WHERE guild_id = ? AND discord_id = ?",
            (badges_json, guild_id, discord_id),
        )
        await self._db.commit()

    async def admin_reset_user(self, guild_id: str, discord_id: str):
        """Fully reset a user's economy within a guild (admin action)."""
        # Reset all user stats to default
        await self._db.execute(
            """UPDATE users
               SET balance = 0, rank = 'Forsaken', risk_score = 0,
                   taxes_paid = 0, grind_count = 0, grind_count_24h = 0,
                   tribute_count = 0
               WHERE guild_id = ? AND discord_id = ?""",
            (guild_id, discord_id),
        )
        # Delete all cooldown records
        await self._db.execute(
            "DELETE FROM cooldowns WHERE guild_id = ? AND discord_id = ?",
            (guild_id, discord_id),
        )
        # Void all active investments (return nothing)
        await self._db.execute(
            """UPDATE investments SET status = 'voided', payout = 0
               WHERE guild_id = ? AND discord_id = ? AND status = 'active'""",
            (guild_id, discord_id),
        )
        # Remove all perks
        await self._db.execute(
            "DELETE FROM user_perks WHERE guild_id = ? AND discord_id = ?",
            (guild_id, discord_id),
        )
        await self._db.commit()
        logger.info(f"Guild {guild_id} — user {discord_id} economy reset by admin.")

    # ─── Ascension History ────────────────────────────────────────────────────

    async def record_ascension(self, guild_id: str, discord_id: str, username: str, rank_name: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            """INSERT INTO ascension_history (guild_id, discord_id, username, rank, ascended_at)
               VALUES (?, ?, ?, ?, ?)""",
            (guild_id, discord_id, username, rank_name, now_str),
        )
        await self._db.commit()

    async def get_last_ascension_time(self, guild_id: str, discord_id: str, rank_name: str) -> Optional[datetime]:
        """Return the datetime of the user's most recent ascension to rank_name, or None."""
        async with self._db.execute(
            """SELECT ascended_at FROM ascension_history
               WHERE guild_id = ? AND discord_id = ? AND rank = ?
               ORDER BY ascended_at DESC LIMIT 1""",
            (guild_id, discord_id, rank_name),
        ) as cur:
            row = await cur.fetchone()
            if row is None:
                return None
            try:
                return datetime.fromisoformat(row["ascended_at"]).replace(tzinfo=timezone.utc)
            except Exception:
                return None

    # ─── Missions ─────────────────────────────────────────────────────────────

    async def create_mission(
        self,
        guild_id:        str,
        title:           str,
        reward:          int,
        expires_at:      Optional[str],
        max_participants: Optional[int],
        required_rank:   Optional[str],
        entry_cost:      int,
        channel_id:      str            = "1488258105216209016",
        description:     Optional[str]  = None,
        repeat_limit:    Optional[int]  = None,
    ) -> dict:
        cur = await self._db.execute(
            """INSERT INTO missions
               (guild_id, title, description, reward, expires_at, max_participants,
                repeat_limit, required_rank, entry_cost, channel_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (guild_id, title, description, reward, expires_at, max_participants,
             repeat_limit, required_rank, entry_cost, channel_id),
        )
        await self._db.commit()
        return await self.get_mission(cur.lastrowid)

    async def get_mission(self, mission_id: int) -> Optional[dict]:
        async with self._db.execute(
            "SELECT * FROM missions WHERE id = ?", (mission_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_active_missions(self, guild_id: str) -> List[dict]:
        async with self._db.execute(
            "SELECT * FROM missions WHERE guild_id = ? AND status = 'active' ORDER BY created_at DESC",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_all_missions(self, guild_id: str) -> List[dict]:
        async with self._db.execute(
            "SELECT * FROM missions WHERE guild_id = ? ORDER BY created_at DESC",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def set_mission_message(self, mission_id: int, message_id: str):
        await self._db.execute(
            "UPDATE missions SET message_id = ? WHERE id = ?", (message_id, mission_id)
        )
        await self._db.commit()

    async def set_mission_status(self, mission_id: int, status: str):
        await self._db.execute(
            "UPDATE missions SET status = ? WHERE id = ?", (status, mission_id)
        )
        await self._db.commit()

    async def get_mission_participant(self, mission_id: int, discord_id: str) -> Optional[dict]:
        async with self._db.execute(
            "SELECT * FROM mission_participants WHERE mission_id = ? AND discord_id = ?",
            (mission_id, discord_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_mission_participants(self, mission_id: int) -> List[dict]:
        async with self._db.execute(
            "SELECT * FROM mission_participants WHERE mission_id = ? ORDER BY accepted_at ASC",
            (mission_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def count_mission_participants(self, mission_id: int) -> int:
        async with self._db.execute(
            "SELECT COUNT(*) AS cnt FROM mission_participants WHERE mission_id = ?",
            (mission_id,),
        ) as cur:
            row = await cur.fetchone()
            return row["cnt"] if row else 0

    async def add_mission_participant(self, mission_id: int, guild_id: str, discord_id: str):
        await self._db.execute(
            """INSERT OR IGNORE INTO mission_participants (mission_id, guild_id, discord_id)
               VALUES (?,?,?)""",
            (mission_id, guild_id, discord_id),
        )
        await self._db.commit()

    async def complete_mission_participant(self, mission_id: int, discord_id: str):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            """UPDATE mission_participants
               SET status = 'completed', completed_at = ?
               WHERE mission_id = ? AND discord_id = ?""",
            (now_str, mission_id, discord_id),
        )
        await self._db.commit()

    async def hard_delete_mission(self, mission_id: int):
        """Permanently erase a mission and all its participant records from the database."""
        await self._db.execute(
            "DELETE FROM mission_participants WHERE mission_id = ?", (mission_id,)
        )
        await self._db.execute(
            "DELETE FROM missions WHERE id = ?", (mission_id,)
        )
        await self._db.commit()
        logger.info(f"[DB] Mission #{mission_id} hard-deleted (participants + mission row removed).")

    # ── Freeze / Unfreeze ──────────────────────────────────────────────────────

    async def freeze_user(
        self, guild_id: str, discord_id: str, reason: str, frozen_by: str
    ):
        """Mark a user's ledger as frozen."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            """UPDATE users
               SET is_frozen = 1, freeze_reason = ?, frozen_by = ?, frozen_at = ?
               WHERE guild_id = ? AND discord_id = ?""",
            (reason, frozen_by, now_str, guild_id, discord_id),
        )
        await self._db.commit()
        logger.info(f"[DB] User {discord_id} frozen in guild {guild_id}: {reason}")

    async def unfreeze_user(self, guild_id: str, discord_id: str):
        """Lift the freeze on a user's ledger."""
        await self._db.execute(
            """UPDATE users
               SET is_frozen = 0, freeze_reason = NULL, frozen_by = NULL, frozen_at = NULL
               WHERE guild_id = ? AND discord_id = ?""",
            (guild_id, discord_id),
        )
        await self._db.commit()
        logger.info(f"[DB] User {discord_id} unfrozen in guild {guild_id}")

    # ── Pressure System ────────────────────────────────────────────────────────

    async def get_all_users_for_guild(self, guild_id: str) -> List[dict]:
        """Return every user row for the given guild (for tax collection)."""
        async with self._db.execute(
            "SELECT discord_id, username, balance, rank, sacrifice_active, last_downgrade_at "
            "FROM users WHERE guild_id = ?",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_sacrifice_users(self, guild_id: str) -> List[dict]:
        """Return all users in the guild currently flagged as sacrifice_active=1."""
        async with self._db.execute(
            "SELECT discord_id, username, balance, rank, sacrifice_active, last_downgrade_at "
            "FROM users WHERE guild_id = ? AND sacrifice_active = 1",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def set_sacrifice_active(self, guild_id: str, discord_id: str, active: bool):
        """Enable or disable sacrifice penalty for a user."""
        val = 1 if active else 0
        await self._db.execute(
            "UPDATE users SET sacrifice_active = ? WHERE guild_id = ? AND discord_id = ?",
            (val, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_last_downgrade_at(self, guild_id: str, discord_id: str, ts: str):
        """Record the ISO-format UTC timestamp of the most recent rank downgrade."""
        await self._db.execute(
            "UPDATE users SET last_downgrade_at = ? WHERE guild_id = ? AND discord_id = ?",
            (ts, guild_id, discord_id),
        )
        await self._db.commit()

    async def set_rank(self, guild_id: str, discord_id: str, rank: str):
        """Directly set a user's rank (used by the downgrade system)."""
        await self._db.execute(
            "UPDATE users SET rank = ? WHERE guild_id = ? AND discord_id = ?",
            (rank, guild_id, discord_id),
        )
        await self._db.commit()
        logger.info(f"[DB] Rank set for user {discord_id} in guild {guild_id}: {rank}")
