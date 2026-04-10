"""
Kingdom Missions — Admin command cog
Commands: /mission create | complete | delete
Background: expiry checker (every 60 s)
"""

import asyncio
import logging
from typing import Optional, List

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ..services.mission_service import MissionService, parse_duration, is_expired, format_remaining
from ..ui.mission_view import MissionView, build_mission_embed

logger = logging.getLogger("kingdom_treasury")

MISSION_CHANNEL_ID = 1488258105216209016

_VOID    = 0x0A0A0A
_CRIMSON = 0x6B0000
_GOLD    = 0xFFD700

_SEP = "━━━━━━━━━━━━━━━━━━━"

_ALL_RANKS = [
    "Forsaken","Vermin","Corrupted","Folklore","Mythology",
    "Demonology","Eschatology","Archangel","Archdemon",
    "Knight","Baron","Viscount","Count","Marquis","Duke",
]
_RANK_SET = set(_ALL_RANKS)


# ── Permission gate ───────────────────────────────────────────────────────────

from ..utils.permissions import is_kingdom_staff, denied_generic as _denied_generic


async def _is_admin(interaction: discord.Interaction) -> bool:
    """
    Mission commands are accessible to all Kingdom staff roles
    (Sovereign, Consorts, Princes, Princesses, Chancellor, Legates).
    Falls back to Discord admin check for server owners / app owners.
    """
    if is_kingdom_staff(interaction):
        return True
    if not interaction.guild:
        return False
    if interaction.user.id == interaction.guild.owner_id:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    return False


def _denied() -> discord.Embed:
    return _denied_generic()





def _err(msg: str) -> discord.Embed:
    return discord.Embed(
        title       = "⚠  Invalid Decree",
        description = f"*{msg}*",
        color       = _CRIMSON,
    )


# ── Cinematic close embeds ────────────────────────────────────────────────────

def _closing_embed(title: str) -> discord.Embed:
    lines = [_SEP, f"📜  **{title}  —  CLOSING**", _SEP, "", "*Closing...*", "", _SEP]
    return discord.Embed(description="\n".join(lines), color=0x1A0000)


def _closed_embed(title: str) -> discord.Embed:
    lines = [
        _SEP, f"📜  **{title}  —  CLOSED**", _SEP,
        "", "*This mission is no longer available.*",
        "", "*Those who hesitated… lost their chance.*",
        "", _SEP,
    ]
    return discord.Embed(description="\n".join(lines), color=_VOID)


# ── Options parser for modal ──────────────────────────────────────────────────

def _parse_options(raw: str) -> dict:
    """
    Parse the modal "Options" field into structured config.
    Format: max:5  rank:Knight  entry:500  repeats:2
    Keys are case-insensitive; rank is title-cased automatically.
    Returns a dict with keys: max_participants, required_rank, entry_cost, repeat_limit.
    """
    result = {
        "max_participants": None,
        "required_rank":    None,
        "entry_cost":       0,
        "repeat_limit":     None,
    }
    if not raw or not raw.strip():
        return result

    for token in raw.split():
        key, _, val = token.partition(":")
        if not val:
            continue
        key = key.lower().strip()
        val = val.strip()

        if key == "max":
            try:
                result["max_participants"] = max(1, int(val))
            except ValueError:
                pass
        elif key == "rank":
            candidate = val.title()
            if candidate in _RANK_SET:
                result["required_rank"] = candidate
        elif key == "entry":
            try:
                result["entry_cost"] = max(0, int(val))
            except ValueError:
                pass
        elif key in ("repeats", "repeat"):
            try:
                result["repeat_limit"] = max(1, int(val))
            except ValueError:
                pass

    return result


# ── Mission creation modal ────────────────────────────────────────────────────

class MissionCreateModal(discord.ui.Modal, title="📜  Kingdom Mission Decree"):
    """
    5-field interactive form for creating a mission.

    Field layout:
      1. Title       — short, required
      2. Description — paragraph, optional (immersive flavour text)
      3. Reward      — DC amount, required
      4. Duration    — e.g. 1h / 24h / 3d; optional
      5. Options     — "max:5 rank:Knight entry:500 repeats:2"; optional
    """

    mission_title = discord.ui.TextInput(
        label       = "Mission Title",
        placeholder = "e.g. Gather 5 Demon Avatars",
        required    = True,
        max_length  = 100,
    )
    description = discord.ui.TextInput(
        label       = "Description  (optional)",
        style       = discord.TextStyle.paragraph,
        placeholder = "Dark, mysterious flavour text for the mission...",
        required    = False,
        max_length  = 500,
    )
    reward = discord.ui.TextInput(
        label       = "Reward  (DC amount)",
        placeholder = "e.g. 5000",
        required    = True,
        max_length  = 20,
    )
    duration = discord.ui.TextInput(
        label       = "Duration  (optional: 10m · 1h · 24h · 3d)",
        placeholder = "e.g. 24h    (leave blank = no expiry)",
        required    = False,
        max_length  = 10,
    )
    options = discord.ui.TextInput(
        label       = "Options  (optional)",
        placeholder = "max:5  rank:Knight  entry:500  repeats:2",
        required    = False,
        max_length  = 200,
    )

    def __init__(self, cog: "MissionsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # ── Parse inputs ─────────────────────────────────────────────────────
        title_val = self.mission_title.value.strip()
        desc_val  = self.description.value.strip() or None
        dur_val   = self.duration.value.strip() or None
        opts      = _parse_options(self.options.value)

        try:
            reward_val = int(self.reward.value.strip().replace(",", ""))
        except ValueError:
            await interaction.followup.send(embed=_err("Reward must be a whole number."), ephemeral=True)
            return

        if reward_val <= 0:
            await interaction.followup.send(embed=_err("Reward must be greater than 0."), ephemeral=True)
            return

        # ── Validate rank ────────────────────────────────────────────────────
        req_rank = opts["required_rank"]
        if req_rank and req_rank not in _RANK_SET:
            await interaction.followup.send(
                embed=_err(
                    f"Unknown rank **{req_rank}**. Valid ranks:\n"
                    + ", ".join(_ALL_RANKS)
                ),
                ephemeral=True,
            )
            return

        # ── Create mission in DB ─────────────────────────────────────────────
        guild_id = str(interaction.guild_id)
        try:
            mission = await self.cog.svc.create_mission(
                guild_id         = guild_id,
                title            = title_val,
                reward           = reward_val,
                duration_str     = dur_val,
                max_participants = opts["max_participants"],
                required_rank    = req_rank,
                entry_cost       = opts["entry_cost"],
                description      = desc_val,
                repeat_limit     = opts["repeat_limit"],
            )
        except ValueError as exc:
            await interaction.followup.send(embed=_err(str(exc)), ephemeral=True)
            return

        # ── Post to missions channel ─────────────────────────────────────────
        channel = self.cog.bot.get_channel(MISSION_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.cog.bot.fetch_channel(MISSION_CHANNEL_ID)
            except Exception:
                channel = None

        if channel is None:
            await interaction.followup.send(
                embed=_err("Could not find the missions channel. Mission created but not posted."),
                ephemeral=True,
            )
            return

        embed = build_mission_embed(mission, participants=[])
        view  = MissionView(mission_id=mission["id"])
        self.cog.bot.add_view(view)

        try:
            msg = await channel.send(embed=embed, view=view)
            await self.cog.db.set_mission_message(mission["id"], str(msg.id))
        except Exception as exc:
            logger.error(f"[Missions] failed to post mission: {exc}")
            await interaction.followup.send(
                embed=_err(f"Mission created (#{mission['id']}) but failed to post: {exc}"),
                ephemeral=True,
            )
            return

        # ── Confirmation ─────────────────────────────────────────────────────
        confirm = discord.Embed(
            title       = "✅  Mission Posted",
            description = f"*Mission **{title_val}** has been decreed in <#{MISSION_CHANNEL_ID}>.*",
            color       = _GOLD,
        )
        confirm.add_field(name="ID",     value=f"**#{mission['id']}**",           inline=True)
        confirm.add_field(name="Reward", value=f"**{reward_val:,} DC**",          inline=True)
        entry = opts["entry_cost"]
        if entry:
            confirm.add_field(name="Entry",   value=f"**{entry:,} DC**",          inline=True)
        if opts["max_participants"]:
            confirm.add_field(name="Slots",   value=f"**{opts['max_participants']}**", inline=True)
        if opts["repeat_limit"]:
            confirm.add_field(name="Repeats", value=f"**{opts['repeat_limit']}**",    inline=True)
        if req_rank:
            confirm.add_field(name="Rank",    value=f"**{req_rank}+**",           inline=True)
        if dur_val:
            confirm.add_field(name="Expires", value=f"**{dur_val}**",             inline=True)
        confirm.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=confirm, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"[MissionCreateModal] on_error: {error}")
        try:
            await interaction.followup.send(embed=_err(f"An error occurred: {error}"), ephemeral=True)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────

class MissionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):                    return self.bot.db
    @property
    def svc(self) -> MissionService: return self.bot.mission_service

    async def cog_load(self):
        try:
            for guild in self.bot.guilds:
                missions = await self.db.get_active_missions(str(guild.id))
                for m in missions:
                    self.bot.add_view(MissionView(mission_id=m["id"]))
            logger.info("[Missions] Persistent views re-registered.")
        except Exception as exc:
            logger.warning(f"[Missions] cog_load view re-register failed: {exc}")
        self._expiry_loop.start()

    async def cog_unload(self):
        self._expiry_loop.cancel()

    # ── Background expiry checker ─────────────────────────────────────────────

    @tasks.loop(seconds=60)
    async def _expiry_loop(self):
        try:
            for guild in self.bot.guilds:
                missions = await self.db.get_active_missions(str(guild.id))
                for m in missions:
                    if is_expired(m):
                        await self.db.set_mission_status(m["id"], "expired")
                        asyncio.create_task(
                            self._cinematic_close(m),
                            name=f"mission_close_{m['id']}",
                        )
                        logger.info(f"[Missions] Mission #{m['id']} expired — cinematic close queued.")
        except Exception as exc:
            logger.warning(f"[Missions] expiry loop error: {exc}")

    @_expiry_loop.before_loop
    async def _before_expiry(self):
        await self.bot.wait_until_ready()

    # ── Cinematic close sequence ──────────────────────────────────────────────

    async def _cinematic_close(self, mission: dict):
        """
        ACTIVE → CLOSING → CLOSED → (message deleted from channel)
        Step 1: Fetch Discord message
        Step 2: Edit → CLOSING, strip all buttons
        Step 3: Wait 2 s
        Step 4: Edit → CLOSED
        Step 5: Wait 3 s
        Step 6: Delete message
        """
        mission_id = mission.get("id", "?")
        title      = mission.get("title", "KINGDOM MISSION")

        if not mission.get("message_id"):
            logger.warning(f"[Missions] cinematic_close #{mission_id}: no message_id stored.")
            return

        channel = self.bot.get_channel(int(mission["channel_id"]))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(mission["channel_id"]))
            except Exception as exc:
                logger.warning(f"[Missions] cinematic_close #{mission_id}: channel not found — {exc}")
                return

        try:
            msg = await channel.fetch_message(int(mission["message_id"]))
        except discord.NotFound:
            logger.warning(f"[Missions] cinematic_close #{mission_id}: message already gone.")
            return
        except Exception as exc:
            logger.warning(f"[Missions] cinematic_close #{mission_id}: fetch failed — {exc}")
            return

        try:
            await msg.edit(embed=_closing_embed(title), view=None)
        except Exception as exc:
            logger.debug(f"[Missions] cinematic_close #{mission_id}: step 2 failed — {exc}")

        await asyncio.sleep(2)

        try:
            await msg.edit(embed=_closed_embed(title))
        except Exception as exc:
            logger.debug(f"[Missions] cinematic_close #{mission_id}: step 4 failed — {exc}")

        await asyncio.sleep(3)

        try:
            await msg.delete()
            logger.info(f"[Missions] cinematic_close #{mission_id}: message deleted.")
        except Exception as exc:
            logger.error(f"[Missions] cinematic_close #{mission_id}: delete failed — {exc}")

    # ── /mission group ────────────────────────────────────────────────────────

    mission = app_commands.Group(name="mission", description="Kingdom Mission management.")

    # ── /mission create — opens interactive modal ─────────────────────────────

    @mission.command(name="create", description="Open the Kingdom Mission creation form.")
    async def mission_create(self, interaction: discord.Interaction):
        if not await _is_admin(interaction):
            await interaction.response.send_message(embed=_denied(), ephemeral=True)
            return
        await interaction.response.send_modal(MissionCreateModal(cog=self))

    # ── /mission complete — participant autocomplete ───────────────────────────

    @mission.command(name="complete", description="Mark a participant complete and pay their reward.")
    @app_commands.describe(
        mission_id = "Mission (autocomplete: search by title).",
        user       = "Accepted participant (autocomplete — select mission first).",
    )
    async def mission_complete(
        self,
        interaction: discord.Interaction,
        mission_id:  int,
        user:        str,
    ):
        await interaction.response.defer(ephemeral=True)
        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        # Resolve discord_id from autocomplete value
        discord_id = user.strip()
        if not discord_id.isdigit():
            await interaction.followup.send(
                embed=_err("Invalid user selection. Please use autocomplete to choose a participant."),
                ephemeral=True,
            )
            return

        # Resolve display name for the confirmation embed
        member  = interaction.guild.get_member(int(discord_id)) if interaction.guild else None
        display = member.display_name if member else f"User {discord_id}"
        mention = f"<@{discord_id}>"

        result = await self.svc.complete_mission(
            guild_id   = str(interaction.guild_id),
            discord_id = discord_id,
            mission_id = mission_id,
        )

        if not result["ok"]:
            await interaction.followup.send(embed=_err(result["reason"]), ephemeral=True)
            return

        embed = discord.Embed(
            title       = "✅  Mission Complete",
            description = (
                f"*{display} has been paid for Mission **#{mission_id}**.*\n"
                f"*The Treasury has released the reward.*"
            ),
            color = _GOLD,
        )
        embed.add_field(name="Reward Paid", value=f"**{result['reward']:,} DC**", inline=True)
        embed.add_field(name="Recipient",   value=mention,                         inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Infernal Ledger — log mission reward payout
        ledger = getattr(self.bot, "ledger_service", None)
        if ledger and result.get("reward", 0) > 0:
            asyncio.create_task(ledger.log(
                action          = "mission_reward",
                amount          = result["reward"],
                from_label      = "Kingdom Treasury",
                to_label        = mention,
                guild_id        = str(interaction.guild_id),
                from_discord_id = discord_id,
                action_type     = "mission",
            ))

        # Fetch the mission dict *before* hard-deleting it
        # (cinematic close uses stored channel_id + message_id, not DB queries)
        mission = await self.db.get_mission(mission_id)
        if mission:
            await self.db.hard_delete_mission(mission_id)
            asyncio.create_task(
                self._cinematic_close(mission),
                name=f"mission_close_{mission_id}",
            )

    @mission_complete.autocomplete("mission_id")
    async def complete_mission_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[int]]:
        try:
            missions = await self.db.get_active_missions(str(interaction.guild_id))
        except Exception:
            return []
        q = current.lower()
        choices = []
        for m in missions:
            label = f"#{m['id']} — {m['title']}"
            if not q or q in str(m["id"]) or q in m["title"].lower():
                choices.append(app_commands.Choice(name=label[:100], value=m["id"]))
            if len(choices) >= 25:
                break
        return choices

    @mission_complete.autocomplete("user")
    async def complete_user_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Show only accepted participants for the currently selected mission."""
        # Read the mission_id the admin has already typed/chosen
        namespace  = interaction.namespace
        mission_id = getattr(namespace, "mission_id", None)
        if not mission_id:
            return [app_commands.Choice(name="Select a mission first", value="0")]

        try:
            rows = await self.db.get_mission_participants(int(mission_id))
        except Exception:
            return []

        # Only show participants who haven't been marked complete yet
        pending = [r for r in rows if r.get("status") != "completed"]
        if not pending:
            return [app_commands.Choice(name="No pending participants", value="0")]

        q = current.lower()
        choices = []
        for p in pending:
            discord_id = p["discord_id"]
            member     = interaction.guild.get_member(int(discord_id)) if interaction.guild else None
            display    = member.display_name if member else f"User {discord_id}"
            if not q or q in display.lower() or q in discord_id:
                choices.append(app_commands.Choice(name=display[:100], value=discord_id))
            if len(choices) >= 25:
                break
        return choices

    # ── /mission delete ───────────────────────────────────────────────────────

    @mission.command(name="delete", description="Withdraw and remove a mission.")
    @app_commands.describe(mission_id="Mission to withdraw (use autocomplete to search by title).")
    async def mission_delete(self, interaction: discord.Interaction, mission_id: int):
        await interaction.response.defer(ephemeral=True)
        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        mission = await self.db.get_mission(mission_id)
        if not mission or str(mission["guild_id"]) != str(interaction.guild_id):
            await interaction.followup.send(embed=_err("Mission not found."), ephemeral=True)
            return

        await self.svc.delete_mission(mission_id)

        embed = discord.Embed(
            title       = "🗑  Mission Withdrawn",
            description = f"*Mission **#{mission_id} — {mission['title']}** has been rescinded.*",
            color       = _VOID,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        asyncio.create_task(
            self._cinematic_close(mission),
            name=f"mission_close_{mission_id}",
        )

    @mission_delete.autocomplete("mission_id")
    async def delete_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[int]]:
        try:
            missions = await self.db.get_active_missions(str(interaction.guild_id))
        except Exception:
            return []
        q = current.lower()
        choices = []
        for m in missions:
            label = f"#{m['id']} — {m['title']}"
            if not q or q in str(m["id"]) or q in m["title"].lower():
                choices.append(app_commands.Choice(name=label[:100], value=m["id"]))
            if len(choices) >= 25:
                break
        return choices
