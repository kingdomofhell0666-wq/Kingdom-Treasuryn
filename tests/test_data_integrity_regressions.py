import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bot.bot as bot_module
import bot.database.db as db_module
import bot.services.cleanup_service as cleanup_module
from bot.cogs.admin import AdminCog
from bot.database.db import Database
from bot.utils.permissions import is_strict_discord_admin


class _Permissions:
    def __init__(self, *, administrator=False, manage_guild=False):
        self.administrator = administrator
        self.manage_guild = manage_guild


def _interaction(*, guild, administrator=False, manage_guild=False):
    return SimpleNamespace(
        guild=guild,
        user=SimpleNamespace(
            id=123,
            display_name="Test Admin",
            guild_permissions=_Permissions(
                administrator=administrator,
                manage_guild=manage_guild,
            ),
        ),
    )


class PermissionRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_condemned_rejects_dm_and_manage_guild_only_members(self):
        for interaction in (
            _interaction(guild=None, administrator=True),
            _interaction(guild=object(), manage_guild=True),
        ):
            with self.subTest(interaction=interaction):
                self.assertFalse(is_strict_discord_admin(interaction))

                interaction.response = SimpleNamespace(defer=AsyncMock())
                interaction.followup = SimpleNamespace(send=AsyncMock())
                cog = AdminCog(SimpleNamespace())

                with patch("bot.cogs.admin.run_cleanup") as run_cleanup:
                    await AdminCog.condemned.callback(cog, interaction, True)

                run_cleanup.assert_not_called()
                interaction.followup.send.assert_awaited_once()

    async def test_condemned_confirmation_is_available_only_to_discord_admins(self):
        interaction = _interaction(guild=object(), administrator=True)
        self.assertTrue(is_strict_discord_admin(interaction))

        interaction.response = SimpleNamespace(defer=AsyncMock())
        interaction.followup = SimpleNamespace(send=AsyncMock())
        cog = AdminCog(SimpleNamespace())

        fake_result = SimpleNamespace(
            report_after=SimpleNamespace(
                cog_count=0,
                command_count=0,
                candidates=(),
                report_id="test",
            ),
            report_before=SimpleNamespace(),
            removed=(),
            backup_status="test",
            error=None,
            text=lambda: "test",
        )
        with patch("bot.cogs.admin.run_cleanup", return_value=fake_result) as run_cleanup:
            await AdminCog.condemned.callback(cog, interaction, True)

        run_cleanup.assert_called_once_with(True)
        interaction.followup.send.assert_awaited_once()


class StartupPersistenceRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_change_and_forced_reset_flag_preserve_user_data(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "treasury.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                seeded = Database()
                await seeded.connect()
                await seeded.upsert_user("guild-1", "user-1", "Keeper")
                await seeded.update_balance("guild-1", "user-1", 9876)
                await seeded.set_meta(
                    "token_fingerprint",
                    Database.compute_token_fingerprint("old-token"),
                )
                await seeded.close()

                with patch.dict(
                    os.environ,
                    {
                        "DISCORD_BOT_TOKEN": "new-token",
                        "FULL_RESET_ON_START": "true",
                    },
                    clear=False,
                ), patch.object(Database, "reset_all_data", new=AsyncMock()) as reset:
                    with patch("discord.ext.tasks.Loop.start"):
                        bot = bot_module.KingdomTreasuryBot()
                        bot.tree.sync = AsyncMock()
                        try:
                            with patch.object(
                                bot_module.KingdomTreasuryBot,
                                "add_cog",
                                new=AsyncMock(),
                            ):
                                await bot.setup_hook()

                            user = await bot.db.get_user("guild-1", "user-1")
                            self.assertEqual(user["balance"], 9876)
                            self.assertEqual(
                                await bot.db.get_meta("token_fingerprint"),
                                Database.compute_token_fingerprint("new-token"),
                            )
                            reset.assert_not_awaited()
                        finally:
                            await bot.db.close()
                            await bot.config_service.close()
                            await bot.guild_sync_service.close()
                            await bot.close()


class MigrationPersistenceRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_incompatible_schema_fails_without_deleting_legacy_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "legacy.db"
            with sqlite3.connect(database_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    INSERT INTO meta (key, value) VALUES ('schema_version', '0');
                    CREATE TABLE users (
                        guild_id TEXT NOT NULL,
                        discord_id TEXT NOT NULL,
                        username TEXT NOT NULL
                    );
                    INSERT INTO users VALUES ('guild-legacy', 'user-legacy', 'Legacy Keeper');
                    """
                )

            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                with self.assertRaisesRegex(RuntimeError, "no data was deleted"):
                    await database.connect()
                if database._db is not None:
                    await database.close()

            with sqlite3.connect(database_path) as connection:
                row = connection.execute(
                    "SELECT guild_id, discord_id, username FROM users"
                ).fetchone()
                schema_version = connection.execute(
                    "SELECT value FROM meta WHERE key = 'schema_version'"
                ).fetchone()[0]

            self.assertEqual(
                row,
                ("guild-legacy", "user-legacy", "Legacy Keeper"),
            )
            self.assertEqual(schema_version, "0")


class CleanupPersistenceRegressionTests(unittest.TestCase):
    def _project_fixture(self, root):
        (root / "bot" / "cogs").mkdir(parents=True)
        (root / "bot" / "cogs" / "example.py").write_text("# source\n")
        (root / "bot" / "bot.py").write_text("# runtime\n")
        cache = root / "bot" / "__pycache__"
        cache.mkdir()
        (cache / "sentinel.pyc").write_bytes(b"cache")
        source = root / "important-data.txt"
        source.write_text("must remain")
        return cache, source

    def test_report_mode_does_not_delete_files_or_create_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, source = self._project_fixture(Path(directory))
            with patch.object(cleanup_module, "PROJECT_ROOT", Path(directory)):
                with patch.object(cleanup_module, "_create_backup") as create_backup:
                    result = cleanup_module.run_cleanup(confirm=False)

            create_backup.assert_not_called()
            self.assertFalse(result.removed)
            self.assertTrue(cache.exists())
            self.assertTrue(source.exists())
            self.assertEqual(source.read_text(), "must remain")

    def test_confirmed_cleanup_backs_up_before_removing_allowlisted_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, source = self._project_fixture(Path(directory))
            events = []

            def backup():
                self.assertTrue(cache.exists())
                events.append("backup")
                return "backup complete"

            original_rmtree = cleanup_module.shutil.rmtree

            def remove(path):
                self.assertEqual(events, ["backup"])
                events.append("remove")
                original_rmtree(path)

            with patch.object(cleanup_module, "PROJECT_ROOT", Path(directory)):
                with patch.object(cleanup_module, "_create_backup", side_effect=backup):
                    with patch.object(cleanup_module.shutil, "rmtree", side_effect=remove):
                        result = cleanup_module.run_cleanup(confirm=True)

            self.assertEqual(events, ["backup", "remove"])
            self.assertEqual(result.removed, ("bot/__pycache__",))
            self.assertFalse(cache.exists())
            self.assertTrue(source.exists())

    def test_cleanup_aborts_without_deleting_when_backup_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            cache, source = self._project_fixture(Path(directory))
            with patch.object(cleanup_module, "PROJECT_ROOT", Path(directory)):
                with patch.object(
                    cleanup_module,
                    "_create_backup",
                    side_effect=RuntimeError("backup unavailable"),
                ), patch.object(cleanup_module.logger, "exception"):
                    result = cleanup_module.run_cleanup(confirm=True)

            self.assertFalse(result.removed)
            self.assertIsNotNone(result.error)
            self.assertTrue(cache.exists())
            self.assertTrue(source.exists())


class BackupRestoreRegressionTests(unittest.IsolatedAsyncioTestCase):
    _EXPECTED_BUSINESS_TABLES = frozenset(
        {"meta", "users", "treasury", "transactions"}
    )

    @staticmethod
    def _snapshot_database(path: Path) -> dict[str, tuple[tuple[object, ...], ...]]:
        with sqlite3.connect(path) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                    """
                )
            }
            return {
                table: tuple(
                    tuple(row)
                    for row in connection.execute(
                        f'SELECT * FROM "{table}" ORDER BY rowid'
                    )
                )
                for table in sorted(tables)
            }

    def _assert_database_restored(
        self, source_path: Path, restored_path: Path
    ) -> None:
        source = self._snapshot_database(source_path)
        restored = self._snapshot_database(restored_path)

        self.assertTrue(
            self._EXPECTED_BUSINESS_TABLES <= source.keys(),
            "La base source ne contient pas toutes les tables métier attendues.",
        )
        self.assertEqual(
            set(source),
            set(restored),
            "La restauration a perdu une table SQLite.",
        )
        for table in sorted(source):
            self.assertEqual(
                source[table],
                restored[table],
                f"La restauration a perdu ou modifié une ligne dans « {table} ».",
            )

    async def test_backup_restores_users_balances_transactions_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / cleanup_module.DATABASE_FILENAME
            backup_directory = root / "backup"
            restored_path = root / "restored.db"

            with patch.object(db_module, "DB_PATH", str(source_path)), patch.object(
                cleanup_module, "PROJECT_ROOT", root
            ):
                database = Database()
                await database.connect()
                await database.upsert_user("guild-1", "user-1", "Keeper")
                await database.upsert_user("guild-1", "user-2", "Treasurer")
                await database.set_balance("guild-1", "user-1", 9876)
                await database.set_balance("guild-1", "user-2", 4321)
                await database.update_treasury("guild-1", 2468)
                await database.log_transaction(
                    "guild-1",
                    "tribute",
                    "user:user-1",
                    "treasury:guild-1",
                    2468,
                    "restoration fixture",
                )
                await database.set_meta("backup_marker", "restore-check-2026-09-22")
                await database.close()

                backup_directory.mkdir()
                status = cleanup_module._backup_database(backup_directory)

            self.assertIn("copie SQLite vérifiée", status)
            backup_path = backup_directory / cleanup_module.DATABASE_FILENAME

            # Simulate restoring the verified backup into a fresh database file.
            with sqlite3.connect(backup_path) as backup, sqlite3.connect(
                restored_path
            ) as restored:
                backup.backup(restored)

            self._assert_database_restored(source_path, restored_path)


if __name__ == "__main__":
    unittest.main()