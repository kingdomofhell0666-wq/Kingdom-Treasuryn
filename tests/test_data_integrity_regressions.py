import io
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image

import bot.bot as bot_module
import bot.database.db as db_module
import bot.services.cleanup_service as cleanup_module
from bot.cogs.admin import AdminCog
from bot.cogs.missions import MissionsCog
from bot.cogs.profile import IdentityCardCreateModal, ProfileCog
from bot.utils.permissions import ROLE_LEGATES
from bot.database.db import Database
from bot.services.transaction_service import TransactionService
from bot.services.database_backup_service import DatabaseBackupService
from bot.ui.ascend_view import AscendView
from bot.ui.mission_view import MissionView, create_mission_proof_thread
from bot.services.rank_service import CANONICAL_ROLE_IDS
from bot.utils.identity_variant import resolve_identity_card_variant
from bot.utils.mine_animation import (
    ANIMATION_DURATION_SECONDS,
    FRAME_COUNT,
    generate_mine_animation,
)
from bot.utils.skins import detect_rank_from_roles
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

    async def test_postgres_disabled_mode_skips_connect_attempts(self):
        with patch.dict(os.environ, {"USE_POSTGRES": "false"}, clear=False):
            config_service = bot_module.ConfigService()
            guild_sync_service = bot_module.GuildSyncService()

            self.assertFalse(config_service.is_postgres_enabled())
            self.assertFalse(guild_sync_service.is_postgres_enabled())
            self.assertIsNone(await config_service._get_pool())
            self.assertIsNone(await guild_sync_service._get_pool())


class RankEconomyRegressionTests(unittest.TestCase):
    def test_unranked_fallback_identity_is_not_eligible_for_kingdom_ranks(self):
        unranked_variant = resolve_identity_card_variant([], "Unranked")
        vermin_variant = resolve_identity_card_variant([], "Vermin")

        self.assertFalse(unranked_variant.kingdom_rank_eligible)
        self.assertTrue(vermin_variant.kingdom_rank_eligible)

    def test_rank_role_ids_match_live_detector_and_identity_card(self):
        self.assertIsNone(detect_rank_from_roles([]))

        for rank_name, role_id in CANONICAL_ROLE_IDS.items():
            role = SimpleNamespace(id=int(role_id))
            variant = resolve_identity_card_variant([role_id], rank_name)

            self.assertEqual(detect_rank_from_roles([role]), rank_name)
            self.assertEqual(variant.primary_display_role, rank_name)
            self.assertEqual(variant.kingdom_rank_eligible, rank_name != "Forsaken")
            self.assertNotIn("CONDEMNED", variant.classification)

    def test_ascension_uses_highest_public_rank_role_and_honors_overrides(self):
        import bot.services.rank_service as rank_module
        service = rank_module.RankService()
        roles = [
            SimpleNamespace(id=int(CANONICAL_ROLE_IDS["Vermin"])),
            SimpleNamespace(id=int(CANONICAL_ROLE_IDS["Corrupted"])),
        ]

        self.assertEqual(service.get_rank_from_roles(roles), "Corrupted")
        self.assertEqual(service.get_next_rank(service.get_rank_from_roles(roles)), "Folklore")
        self.assertEqual(
            service.get_rank_from_roles(
                [SimpleNamespace(id=999)],
                [{"role_id": "999", "rank_name": "Vermin"}],
            ),
            "Vermin",
        )
        self.assertIsNone(
            service.get_rank_from_roles(
                [SimpleNamespace(id=1000)],
                [{"role_id": "1000", "rank_name": "Chancellor"}],
            )
        )

    def test_new_players_must_buy_forsaken_before_vermin(self):
        service = bot_module.RankService() if hasattr(bot_module, "RankService") else None
        if service is None:
            import bot.services.rank_service as rank_module
            service = rank_module.RankService()

        self.assertTrue(service.is_purchasable("Forsaken"))
        self.assertEqual(service.get_rank_cost("Forsaken"), 750)
        self.assertEqual(service.get_rank_cost("Vermin"), 2_000)
        self.assertEqual(service.get_rank_cost("Corrupted"), 5_000)
        self.assertEqual(service.get_rank_cost("Folklore"), 20_000)
        self.assertEqual(service.get_rank_cost("Mythology"), 300_000)
        self.assertEqual(service.get_rank_cost("Demonology"), 650_000)
        self.assertEqual(service.get_rank_cost("Eschatology"), 1_400_000)
        self.assertEqual(service.get_rank_cost("Archangel"), 3_000_000)
        self.assertEqual(service.get_rank_cost("Archdemon"), 6_000_000)
        self.assertEqual(service.get_rank_cost("Knight"), 12_000_000)
        self.assertEqual(service.get_rank_cost("Baron"), 24_000_000)
        self.assertEqual(service.get_rank_cost("Viscount"), 42_000_000)
        self.assertEqual(service.get_rank_cost("Count"), 60_000_000)
        self.assertEqual(service.get_rank_cost("Marquis"), 75_000_000)
        self.assertEqual(service.get_rank_cost("Duke"), 90_000_000)
        self.assertEqual(service.get_next_rank("Unranked"), "Forsaken")
        self.assertTrue(service.can_ascend_to("Unranked", "Forsaken"))
        self.assertEqual(service.get_next_rank("Forsaken"), "Vermin")
        self.assertTrue(service.can_ascend_to("Forsaken", "Vermin"))

    def test_rank_costs_increase_strictly_without_a_forsaken_wait_timer(self):
        import bot.services.rank_service as rank_module
        service = rank_module.RankService()
        costs = [cost for _, cost, _ in service.get_purchasable_ranks()]

        self.assertTrue(all(current < following for current, following in zip(costs, costs[1:])))
        self.assertEqual(rank_module.DEFAULT_ASCENSION_COOLDOWNS["Forsaken"], 0)

    def test_ascend_view_offers_forsaken_as_the_first_purchase(self):
        import bot.services.rank_service as rank_module
        service = rank_module.RankService()
        next_rank = service.get_next_rank("Unranked")
        view = AscendView(
            ranks=service.get_purchasable_ranks(),
            owner_id=123,
            current_rank="Unranked",
            next_rank=next_rank,
            balance=750,
            ascend_cb=AsyncMock(),
        )

        buy_button = next(button for button in view.children if button.label == "⚔  Buy → Forsaken")
        self.assertFalse(buy_button.disabled)
        self.assertIn("None yet", view.build_embed().description)

    def test_ascend_button_is_disabled_when_balance_is_insufficient(self):
        import bot.services.rank_service as rank_module
        service = rank_module.RankService()
        view = AscendView(
            ranks=service.get_purchasable_ranks(),
            owner_id=123,
            current_rank="Unranked",
            next_rank="Forsaken",
            balance=749,
            ascend_cb=AsyncMock(),
        )

        buy_button = next(button for button in view.children if button.label == "🔒  Need 1 DC")
        self.assertTrue(buy_button.disabled)
        rank_fields = "\n".join(field.value for field in view.build_embed().fields)
        self.assertIn("Need **1** more DC", rank_fields)


class IdentityCardOnboardingGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_createid_opens_required_card_name_modal(self):
        database = SimpleNamespace(has_identity_card=AsyncMock(return_value=False))
        cog = ProfileCog(SimpleNamespace(db=database))
        interaction = SimpleNamespace(
            guild=SimpleNamespace(id=987),
            guild_id=987,
            channel_id=1488255553170837565,
            user=SimpleNamespace(id=123),
            response=SimpleNamespace(send_modal=AsyncMock(), send_message=AsyncMock()),
        )

        await ProfileCog.create_identity_card.callback(cog, interaction)

        interaction.response.send_modal.assert_awaited_once()
        modal = interaction.response.send_modal.await_args.args[0]
        self.assertIsInstance(modal, IdentityCardCreateModal)
        self.assertTrue(modal.card_name.required)
        self.assertEqual(modal.card_name.max_length, 32)

    async def test_new_member_must_create_card_before_using_commands(self):
        database = SimpleNamespace(has_identity_card=AsyncMock(return_value=False))
        tree = SimpleNamespace(client=SimpleNamespace(db=database))
        interaction = SimpleNamespace(
            guild=SimpleNamespace(id=987, owner_id=999),
            user=SimpleNamespace(
                id=123,
                roles=[],
                guild_permissions=SimpleNamespace(administrator=False, manage_guild=False),
            ),
            data={"name": "grind"},
            response=SimpleNamespace(send_message=AsyncMock()),
        )

        allowed = await bot_module.KingdomCommandTree.interaction_check(tree, interaction)

        self.assertFalse(allowed)
        database.has_identity_card.assert_awaited_once_with("987", "123")
        interaction.response.send_message.assert_awaited_once()
        self.assertIn("1488255553170837565", interaction.response.send_message.await_args.kwargs["embed"].description)

    async def test_identity_command_and_privileged_members_bypass_card_gate(self):
        database = SimpleNamespace(has_identity_card=AsyncMock(return_value=False))
        tree = SimpleNamespace(client=SimpleNamespace(db=database))

        async def check(user, command_name="identity"):
            interaction = SimpleNamespace(
                guild=SimpleNamespace(id=987, owner_id=999),
                user=user,
                data={"name": command_name},
                response=SimpleNamespace(send_message=AsyncMock()),
            )
            allowed = await bot_module.KingdomCommandTree.interaction_check(tree, interaction)
            return allowed, interaction

        ordinary_user = SimpleNamespace(
            id=123,
            roles=[],
            guild_permissions=SimpleNamespace(administrator=False, manage_guild=False),
        )
        admin_user = SimpleNamespace(
            id=124,
            roles=[],
            guild_permissions=SimpleNamespace(administrator=True, manage_guild=False),
        )
        moderator = SimpleNamespace(
            id=125,
            roles=[SimpleNamespace(id=ROLE_LEGATES)],
            guild_permissions=SimpleNamespace(administrator=False, manage_guild=False),
        )
        discord_moderator = SimpleNamespace(
            id=126,
            roles=[],
            guild_permissions=SimpleNamespace(
                administrator=False,
                manage_guild=False,
                manage_messages=True,
                kick_members=False,
                ban_members=False,
                moderate_members=False,
            ),
        )

        createid_allowed, _ = await check(ordinary_user, "createid")
        identity_allowed, _ = await check(ordinary_user, "identity")
        admin_allowed, _ = await check(admin_user, "grind")
        moderator_allowed, _ = await check(moderator, "grind")
        discord_moderator_allowed, _ = await check(discord_moderator, "grind")

        self.assertTrue(createid_allowed)
        self.assertFalse(identity_allowed)
        self.assertTrue(admin_allowed)
        self.assertTrue(moderator_allowed)
        self.assertTrue(discord_moderator_allowed)
        database.has_identity_card.assert_awaited_once_with("987", "123")

    async def test_own_identity_card_is_registered_after_send_in_required_channel(self):
        database = SimpleNamespace(
            upsert_user=AsyncMock(return_value={
                "rank": "Unranked",
                "balance": 0,
                "identity_display_name": "Chosen Card Name",
            }),
            get_weekly_kingdom_rank_position=AsyncMock(return_value=0),
            mark_identity_card_created=AsyncMock(),
        )
        config_service = SimpleNamespace()
        cog = ProfileCog(SimpleNamespace(db=database, config_service=config_service))
        member = SimpleNamespace(
            id=123,
            name="Member",
            display_name="Member",
            roles=[],
            mention="<@123>",
            display_avatar=SimpleNamespace(with_size=lambda size: SimpleNamespace(url=None)),
            guild_permissions=SimpleNamespace(administrator=False, manage_guild=False),
        )
        interaction = SimpleNamespace(
            guild=SimpleNamespace(id=987, owner_id=999),
            guild_id=987,
            channel_id=1488255553170837565,
            user=member,
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )

        generate_card = Mock(return_value=io.BytesIO(b"identity-card"))
        with (
            patch("bot.cogs.profile.check_routing", new=AsyncMock(return_value=True)),
            patch("bot.cogs.profile.fetch_avatar", new=AsyncMock(return_value=None)),
            patch("bot.cogs.profile.generate_card", new=generate_card),
        ):
            await ProfileCog.identity.callback(cog, interaction)

        interaction.followup.send.assert_awaited_once()
        self.assertEqual(generate_card.call_args.kwargs["display_name"], "Chosen Card Name")
        database.mark_identity_card_created.assert_awaited_once_with("987", "123")


class MineAnimationTests(unittest.TestCase):
    def test_animation_is_animated_and_depends_on_actual_net_reward(self):
        reward_animation = generate_mine_animation(327)
        other_reward_animation = generate_mine_animation(328)
        reward_gif = Image.open(reward_animation)

        self.assertEqual(reward_gif.format, "GIF")
        self.assertEqual(reward_gif.size, (384, 216))
        self.assertEqual(reward_gif.n_frames, FRAME_COUNT)
        self.assertGreaterEqual(ANIMATION_DURATION_SECONDS, 6.5)
        self.assertNotEqual(reward_animation.getvalue(), other_reward_animation.getvalue())


class RankDatabaseRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_mission_proof_thread_id_persists_for_participant(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "mission-thread.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    await database.add_mission_participant(42, "guild", "member")
                    await database.set_mission_participant_thread(42, "member", "987654321")
                    participant = await database.get_mission_participant(42, "member")
                    self.assertEqual(participant["thread_id"], "987654321")
                finally:
                    await database.close()

    async def test_identity_card_registry_is_persistent_per_guild_and_user(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "identity-registry.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    self.assertFalse(await database.has_identity_card("guild-a", "member"))
                    await database.mark_identity_card_created("guild-a", "member")
                    self.assertTrue(await database.has_identity_card("guild-a", "member"))
                    self.assertFalse(await database.has_identity_card("guild-b", "member"))
                finally:
                    await database.close()

    async def test_forsaken_is_excluded_from_weekly_server_leaderboard(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "forsaken-leaderboard.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    await database.upsert_user("guild", "forsaken-player", "Forsaken Player")
                    await database.set_rank("guild", "forsaken-player", "Forsaken")
                    await database.add_weekly_active_seconds("guild", "forsaken-player", 60)
                    await database.update_balance("guild", "forsaken-player", 200)
                    await database.upsert_user("guild", "unranked-player", "Unranked Player")
                    await database.add_weekly_active_seconds("guild", "unranked-player", 120)
                    await database.update_balance("guild", "unranked-player", 500)
                    await database.upsert_user("guild", "vermin-player", "Vermin Player")
                    await database.set_rank("guild", "vermin-player", "Vermin")
                    await database.add_weekly_active_seconds("guild", "vermin-player", 30)

                    leaderboard = await database.get_weekly_kingdom_leaderboard("guild")
                    forsaken_position = await database.get_weekly_kingdom_rank_position(
                        "guild", "forsaken-player"
                    )
                    unranked_position = await database.get_weekly_kingdom_rank_position(
                        "guild", "unranked-player"
                    )
                    vermin_position = await database.get_weekly_kingdom_rank_position(
                        "guild", "vermin-player"
                    )

                    self.assertEqual([row["discord_id"] for row in leaderboard], ["vermin-player"])
                    self.assertEqual(forsaken_position, 0)
                    self.assertEqual(unranked_position, 0)
                    self.assertEqual(vermin_position, 1)
                finally:
                    await database.close()

    async def test_new_users_start_unranked_and_existing_progress_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "rank-progression.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    new_user = await database.upsert_user("guild", "new-user", "New")
                    self.assertEqual(new_user["rank"], "Unranked")

                    await database.set_rank("guild", "new-user", "Vermin")
                    await database.set_balance("guild", "new-user", 1234)
                    updated_user = await database.upsert_user("guild", "new-user", "Renamed")

                    self.assertEqual(updated_user["rank"], "Vermin")
                    self.assertEqual(updated_user["balance"], 1234)
                    await database.set_identity_display_name("guild", "new-user", "Chosen Card Name")
                    updated_user = await database.get_user("guild", "new-user")
                    self.assertEqual(updated_user["identity_display_name"], "Chosen Card Name")
                finally:
                    await database.close()

    async def test_global_reset_clears_only_bot_data_and_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "reset-scope.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    await database.set_meta("preserved_marker", "keep")
                    await database.upsert_user("guild", "player", "Player")
                    await database.set_balance("guild", "player", 1234)
                    await database.update_treasury("guild", 4321)
                    await database.log_transaction("guild", "test", "mint", "user:player", 1234)

                    deleted = await database.reset_kingdom_treasury_data()

                    self.assertEqual(deleted["users"], 1)
                    self.assertEqual(deleted["treasury"], 1)
                    self.assertEqual(deleted["transactions"], 1)
                    self.assertEqual(await database.get_meta("preserved_marker"), "keep")
                    self.assertEqual(await database.get_user("guild", "player"), None)
                    self.assertEqual(await database.get_treasury_balance("guild"), 0)
                    async with database._db.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
                    ) as cursor:
                        self.assertIsNotNone(await cursor.fetchone())
                    async with database._db.execute(
                        "SELECT COUNT(*) FROM sqlite_sequence WHERE name IN (?, ?, ?)",
                        ("transactions", "investments", "missions"),
                    ) as cursor:
                        self.assertEqual((await cursor.fetchone())[0], 0)

                    recreated_user = await database.upsert_user("guild", "new-player", "New Player")
                    self.assertEqual(recreated_user["rank"], "Unranked")
                finally:
                    await database.close()

    async def test_ascension_debit_rejects_short_balance_and_accepts_exact_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "ascension-payment.db"
            with patch.object(db_module, "DB_PATH", str(database_path)):
                database = Database()
                await database.connect()
                try:
                    await database.upsert_user("guild", "player", "Player")
                    await database.set_balance("guild", "player", 749)
                    transactions = TransactionService(database)

                    with self.assertRaisesRegex(ValueError, "Insufficient DC"):
                        await transactions.ascension_payment("guild", "player", "Forsaken", 750)

                    user = await database.get_user("guild", "player")
                    self.assertEqual(user["balance"], 749)
                    self.assertEqual(user["rank"], "Unranked")

                    await database.set_balance("guild", "player", 750)
                    await transactions.ascension_payment("guild", "player", "Forsaken", 750)

                    user = await database.get_user("guild", "player")
                    self.assertEqual(user["balance"], 0)
                    self.assertEqual(user["rank"], "Forsaken")

                    await transactions.rollback_ascension(
                        "guild", "player", "Unranked", "Forsaken", 750
                    )
                    user = await database.get_user("guild", "player")
                    self.assertEqual(user["balance"], 750)
                    self.assertEqual(user["rank"], "Unranked")
                    self.assertEqual(await database.get_treasury_balance("guild"), 0)
                finally:
                    await database.close()


class GlobalResetSafetyRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_database_backup_is_integrity_checked_and_contains_source_data(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "kingdom_treasury.db"
            backup_root = Path(directory) / "backups"
            with sqlite3.connect(source_path) as connection:
                connection.execute("CREATE TABLE users (discord_id TEXT PRIMARY KEY)")
                connection.execute("INSERT INTO users VALUES ('saved-user')")

            backup_path = await DatabaseBackupService(source_path, backup_root).create_verified_backup()

            self.assertTrue(backup_path.is_file())
            self.assertEqual(backup_path.parent.parent, backup_root)
            with sqlite3.connect(backup_path) as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("SELECT discord_id FROM users").fetchone()[0], "saved-user")

    async def test_global_reset_requires_founder_and_exact_confirmation(self):
        command = AdminCog.reset_kingdom_treasury
        self.assertEqual(command.name, "reset")
        reset = AsyncMock()
        cog = AdminCog(SimpleNamespace(db=SimpleNamespace(reset_kingdom_treasury_data=reset)))

        for founder_id, actor_id, confirmation in (
            ("999", 123, "RESET"),
            ("123", 123, "reset"),
            ("123", 123, None),
        ):
            interaction = SimpleNamespace(
                user=SimpleNamespace(id=actor_id),
                response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock()),
                followup=SimpleNamespace(send=AsyncMock()),
            )
            with patch.dict(os.environ, {"FOUNDER_ID": founder_id}):
                await command.callback(cog, interaction, confirmation)
            interaction.response.send_message.assert_awaited_once()

        reset.assert_not_awaited()

    async def test_reset_aborts_without_touching_database_if_backup_fails(self):
        command = AdminCog.reset_kingdom_treasury
        reset = AsyncMock()
        cog = AdminCog(SimpleNamespace(db=SimpleNamespace(reset_kingdom_treasury_data=reset)))
        interaction = SimpleNamespace(
            user=SimpleNamespace(id=123),
            response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        backup_service = SimpleNamespace(
            create_verified_backup=AsyncMock(side_effect=OSError("backup unavailable"))
        )

        with (
            patch.dict(os.environ, {"FOUNDER_ID": "123"}),
            patch("bot.cogs.admin.DatabaseBackupService", return_value=backup_service),
        ):
            await command.callback(cog, interaction, "RESET")

        reset.assert_not_awaited()
        interaction.followup.send.assert_awaited_once()


class MissionPrivacyRegressionTests(unittest.IsolatedAsyncioTestCase):
    def test_mission_slash_commands_are_admin_only(self):
        self.assertTrue(MissionsCog.mission.default_permissions.administrator)
        self.assertEqual(
            {command.name for command in MissionsCog.mission.commands},
            {"create", "complete", "delete"},
        )
        self.assertTrue(
            all(command.default_permissions.administrator for command in MissionsCog.mission.commands)
        )

    async def test_private_proof_thread_invites_member_and_reviewers_only(self):
        def member(member_id, *, administrator=False, role_ids=()):
            return SimpleNamespace(
                id=member_id,
                mention=f"<@{member_id}>",
                roles=[SimpleNamespace(id=role_id) for role_id in role_ids],
                guild_permissions=SimpleNamespace(
                    administrator=administrator,
                    manage_guild=False,
                    manage_threads=False,
                ),
            )

        owner = member(1)
        admin = member(2, administrator=True)
        moderator = member(3, role_ids=[ROLE_LEGATES])
        outsider = member(4)
        participant = member(5)
        guild_members = [owner, admin, moderator, outsider, participant]
        guild = SimpleNamespace(
            owner_id=owner.id,
            members=guild_members,
            get_member=lambda member_id: next(
                (item for item in guild_members if item.id == member_id), None
            ),
            fetch_member=AsyncMock(),
        )
        thread = SimpleNamespace(
            id=99,
            mention="<#99>",
            add_user=AsyncMock(),
            send=AsyncMock(),
            delete=AsyncMock(),
        )
        channel = SimpleNamespace(create_thread=AsyncMock(return_value=thread))
        mission = {"id": 7, "title": "Collect infernal ore"}

        created_thread = await create_mission_proof_thread(guild, channel, participant, mission)

        self.assertIs(created_thread, thread)
        self.assertEqual(
            {call.args[0].id for call in thread.add_user.await_args_list},
            {owner.id, admin.id, moderator.id, participant.id},
        )
        self.assertNotIn(outsider.id, {call.args[0].id for call in thread.add_user.await_args_list})
        self.assertEqual(
            channel.create_thread.await_args.kwargs["type"],
            discord.ChannelType.private_thread,
        )
        self.assertFalse(channel.create_thread.await_args.kwargs["invitable"])

    async def test_thread_failure_prevents_mission_acceptance(self):
        mission_service = SimpleNamespace(accept_mission=AsyncMock())
        mission = {"id": 7, "guild_id": "guild", "channel_id": "55"}
        database = SimpleNamespace(get_mission=AsyncMock(return_value=mission))
        bot = SimpleNamespace(
            db=database,
            mission_service=mission_service,
            get_channel=Mock(return_value=SimpleNamespace()),
            fetch_channel=AsyncMock(),
        )
        participant = SimpleNamespace(id=123, display_name="Member")
        interaction = SimpleNamespace(
            client=bot,
            guild_id="guild",
            guild=SimpleNamespace(id=1),
            user=participant,
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        view = MissionView(mission_id=7)

        with patch(
            "bot.ui.mission_view.create_mission_proof_thread",
            new=AsyncMock(side_effect=RuntimeError("private threads unavailable")),
        ):
            await view._accept_callback(interaction)

        mission_service.accept_mission.assert_not_awaited()
        interaction.followup.send.assert_awaited_once()


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