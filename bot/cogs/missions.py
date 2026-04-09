"""
Kingdom Missions — Admin command cog
Commands: /mission create | complete | delete | list
Background: expiry checker (every 60 s)
"""

import asyncio
import logging
from datetime import datetime, timezone
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

# All public kingdom ranks (for autocomplete / choices)
_ALL_RANKS = [
    "Forsaken","Vermin","Corrupted","Folklore","Mythology",
    "Demonology","Eschatology","Archangel","Archdemon",
    "Knight","Baron","Viscount","Count","Marquis","Duke",
]


# ── Permission gate (reuse admin.py pattern) ──────────────────────────────────

async def _is_admin(interaction: discord.Interaction) -> bool:
    try:
        app_info = await interaction.client.application_info()
        if interaction.user.id == app_info.owner.id:
            return True
    except Exception:
        pass
    if not interaction.guild:
        return False
    if interaction.user.id == interaction.guild.owner_id:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    return False


def _denied() -> discord.Embed:
    return discord.Embed(
        title       = "🔒  Access Denied",
        description = "*You do not hold authority to issue Kingdom missions.*",
        color       = _VOID,
    )


def _err(msg: str) -> discord.Embed:
    return discord.Embed(
        title       = "⚠  Invalid Decree",
        description = f"*{msg}*",
        color       = _CRIMSON,
    )


# ─────────────────────────────────────────────────────────────────────────────

class MissionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):          return self.bot.db
    @property
    def svc(self) -> MissionService: return self.bot.mission_service

    async def cog_load(self):
        """Re-register persistent views for all active missions on startup."""
        try:
            # We need to iterate over every guild the bot is in
            # (missions table is guild-scoped; query all unique guild IDs)
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
                guild_id = str(guild.id)
                missions = await self.db.get_active_missions(guild_id)
                for m in missions:
                    if is_expired(m):
                        await self.db.set_mission_status(m["id"], "expired")
                        await self._update_mission_post(m, expired=True)
                        logger.info(f"[Missions] Mission #{m['id']} expired.")
        except Exception as exc:
            logger.warning(f"[Missions] expiry loop error: {exc}")

    @_expiry_loop.before_loop
    async def _before_expiry(self):
        await self.bot.wait_until_ready()

    async def _update_mission_post(self, mission: dict, expired: bool = False):
        """Edit the Discord message to reflect expired / updated state."""
        try:
            if not mission.get("message_id"):
                return
            channel = self.bot.get_channel(int(mission["channel_id"]))
            if channel is None:
                return
            msg = await channel.fetch_message(int(mission["message_id"]))
            count = await self.db.count_mission_participants(mission["id"])
            embed = build_mission_embed(mission, count)
            view  = MissionView(mission_id=mission["id"], disabled=expired)
            await msg.edit(embed=embed, view=view)
        except Exception as exc:
            logger.debug(f"[Missions] update_post failed: {exc}")

    # ── /mission group ────────────────────────────────────────────────────────

    mission = app_commands.Group(name="mission", description="Kingdom Mission management.")

    # ── /mission create ───────────────────────────────────────────────────────

    @mission.command(name="create", description="Create a new Kingdom Mission.")
    @app_commands.describe(
        title            = "Mission title.",
        reward           = "DC reward paid to each completer (from Treasury).",
        duration         = "Time limit: 10m · 1h · 24h · 3d (leave blank = no expiry).",
        max_participants = "Max number of participants (leave blank = unlimited).",
        required_rank    = "Minimum rank required to accept.",
        entry_cost       = "DC entry fee (deducted on accept, sent to Treasury).",
    )
    @app_commands.choices(required_rank=[
        app_commands.Choice(name=r, value=r) for r in _ALL_RANKS
    ])
    async def mission_create(
        self,
        interaction:     discord.Interaction,
        title:           str,
        reward:          int,
        duration:        Optional[str] = None,
        max_participants: Optional[int] = None,
        required_rank:   Optional[str] = None,
        entry_cost:      int           = 0,
    ):
        await interaction.response.defer(ephemeral=True)
        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        if reward <= 0:
            await interaction.followup.send(embed=_err("Reward must be greater than 0."), ephemeral=True)
            return
        if entry_cost < 0:
            await interaction.followup.send(embed=_err("Entry cost cannot be negative."), ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        try:
            mission = await self.svc.create_mission(
                guild_id         = guild_id,
                title            = title,
                reward           = reward,
                duration_str     = duration,
                max_participants = max_participants,
                required_rank    = required_rank,
                entry_cost       = entry_cost,
            )
        except ValueError as exc:
            await interaction.followup.send(embed=_err(str(exc)), ephemeral=True)
            return

        # Post to missions channel
        channel = self.bot.get_channel(MISSION_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(MISSION_CHANNEL_ID)
            except Exception:
                pass

        if channel is None:
            await interaction.followup.send(
                embed=_err("Could not find the missions channel. Mission was created but not posted."),
                ephemeral=True,
            )
            return

        count = 0
        embed = build_mission_embed(mission, count)
        view  = MissionView(mission_id=mission["id"])
        self.bot.add_view(view)

        try:
            msg = await channel.send(embed=embed, view=view)
            await self.db.set_mission_message(mission["id"], str(msg.id))
        except Exception as exc:
            logger.error(f"[Missions] failed to post mission: {exc}")
            await interaction.followup.send(
                embed=_err(f"Mission created (#{mission['id']}) but failed to post: {exc}"),
                ephemeral=True,
            )
            return

        confirm = discord.Embed(
            title       = "✅  Mission Posted",
            description = f"*Mission **{title}** has been decreed.*",
            color       = _GOLD,
        )
        confirm.add_field(name="ID",     value=f"**#{mission['id']}**",      inline=True)
        confirm.add_field(name="Reward", value=f"**{reward:,} DC**",         inline=True)
        if entry_cost:
            confirm.add_field(name="Entry", value=f"**{entry_cost:,} DC**",  inline=True)
        if max_participants:
            confirm.add_field(name="Slots", value=f"**{max_participants}**",  inline=True)
        if required_rank:
            confirm.add_field(name="VIP",   value=f"**{required_rank}+**",   inline=True)
        if duration:
            confirm.add_field(name="Duration", value=f"**{duration}**",      inline=True)
        confirm.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=confirm, ephemeral=True)

    # ── /mission complete ─────────────────────────────────────────────────────

    @mission.command(name="complete", description="Mark a mission participant as complete and pay their reward.")
    @app_commands.describe(
        user       = "The user to pay.",
        mission_id = "Mission ID (use autocomplete).",
    )
    async def mission_complete(
        self,
        interaction: discord.Interaction,
        user:        discord.Member,
        mission_id:  int,
    ):
        await interaction.response.defer(ephemeral=True)
        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        guild_id   = str(interaction.guild_id)
        discord_id = str(user.id)

        result = await self.svc.complete_mission(guild_id, discord_id, mission_id)

        if not result["ok"]:
            await interaction.followup.send(embed=_err(result["reason"]), ephemeral=True)
            return

        embed = discord.Embed(
            title       = "✅  Mission Complete",
            description = (
                f"*{user.display_name} has been paid for Mission **#{mission_id}**.*\n"
                f"*The Treasury has released the reward.*"
            ),
            color       = _GOLD,
        )
        embed.add_field(name="Reward Paid", value=f"**{result['reward']:,} DC**", inline=True)
        embed.add_field(name="Recipient",   value=user.mention,                   inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @mission_complete.autocomplete("mission_id")
    async def complete_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[int]]:
        guild_id = str(interaction.guild_id)
        try:
            missions = await self.db.get_active_missions(guild_id)
        except Exception:
            return []
        q = current.lower()
        choices = []
        for m in missions:
            label = f"#{m['id']} — {m['title']}"
            if q in str(m["id"]) or q in m["title"].lower():
                choices.append(app_commands.Choice(name=label[:100], value=m["id"]))
            if len(choices) >= 25:
                break
        return choices

    # ── /mission delete ───────────────────────────────────────────────────────

    @mission.command(name="delete", description="Withdraw and remove a mission.")
    @app_commands.describe(mission_id="Mission ID to delete.")
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
        await self._update_mission_post(await self.db.get_mission(mission_id))

        embed = discord.Embed(
            title       = "🗑  Mission Withdrawn",
            description = f"*Mission **#{mission_id} — {mission['title']}** has been withdrawn.*",
            color       = _VOID,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /mission list ─────────────────────────────────────────────────────────

    @mission.command(name="list", description="List all missions for this server.")
    async def mission_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not await _is_admin(interaction):
            await interaction.followup.send(embed=_denied(), ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        missions = await self.db.get_all_missions(guild_id)

        if not missions:
            embed = discord.Embed(
                description = "*No missions have been created yet.*",
                color       = _VOID,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title = "📋  Kingdom Missions",
            color = _CRIMSON,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")

        for m in missions[:20]:   # Discord embed field limit
            status  = m["status"].upper()
            expired = is_expired(m) and m["status"] == "active"
            if expired:
                status = "EXPIRED"

            parts = [f"**Reward:** {m['reward']:,} DC", f"**Status:** {status}"]
            if m.get("entry_cost"):
                parts.append(f"**Entry:** {m['entry_cost']:,} DC")
            max_p = m.get("max_participants")
            if max_p:
                count = await self.db.count_mission_participants(m["id"])
                parts.append(f"**Slots:** {count}/{max_p}")
            if m.get("required_rank"):
                parts.append(f"**VIP:** {m['required_rank']}+")
            if m.get("expires_at") and not expired:
                parts.append(f"**Expires:** {format_remaining(m)}")

            embed.add_field(
                name  = f"#{m['id']} — {m['title']}",
                value = "  ·  ".join(parts),
                inline= False,
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── Duration autocomplete ─────────────────────────────────────────────────

    @mission_create.autocomplete("duration")
    async def duration_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        options = [
            ("10 minutes",  "10m"),
            ("30 minutes",  "30m"),
            ("1 hour",      "1h"),
            ("6 hours",     "6h"),
            ("12 hours",    "12h"),
            ("24 hours",    "24h"),
            ("2 days",      "2d"),
            ("3 days",      "3d"),
        ]
        q = current.lower()
        return [
            app_commands.Choice(name=label, value=val)
            for label, val in options
            if q in label.lower() or q in val.lower()
        ]
