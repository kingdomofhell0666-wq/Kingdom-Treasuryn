"""
MissionView — Persistent button UI for Kingdom Missions.

Buttons survive bot restarts because:
  - timeout=None
  - custom_ids encode mission_id
  - bot.add_view(MissionView(mission_id)) is called on startup for every active mission
"""

import discord
import logging
from typing import List

from ..utils.permissions import KINGDOM_ROLES

logger = logging.getLogger("kingdom_treasury")

_CRIMSON = 0x6B0000
_GOLD    = 0xFFD700
_DARK    = 0x0A0A0A

_SEP = "━━━━━━━━━━━━━━━━━━━"
_DC  = "<:devilcoinStack:1492184333392412692>"

# Discord embed description hard limit
_EMBED_MAX = 4000


def _can_review_missions(member: discord.Member, guild: discord.Guild) -> bool:
    permissions = member.guild_permissions
    role_ids = {role.id for role in member.roles}
    return (
        member.id == guild.owner_id
        or permissions.administrator
        or permissions.manage_guild
        or permissions.manage_threads
        or bool(role_ids & KINGDOM_ROLES)
    )


async def create_mission_proof_thread(
    guild: discord.Guild,
    channel,
    participant: discord.Member,
    mission: dict,
) -> discord.Thread:
    """Create a private proof thread for only the member and mission reviewers."""
    if not hasattr(channel, "create_thread"):
        raise RuntimeError("The mission channel does not support private threads.")

    owner = guild.get_member(guild.owner_id)
    if owner is None:
        owner = await guild.fetch_member(guild.owner_id)

    reviewers = {
        member.id: member
        for member in guild.members
        if _can_review_missions(member, guild)
    }
    reviewers[owner.id] = owner

    safe_title = " ".join(mission["title"].split())
    thread_name = f"mission-{mission['id']}-{safe_title}"[:100]
    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.private_thread,
        invitable=False,
        auto_archive_duration=10080,
        reason=f"Private proof thread for mission #{mission['id']}",
    )

    try:
        invited = {participant.id: participant, **reviewers}
        for member in invited.values():
            await thread.add_user(member)
        await thread.send(
            content=(
                f"{participant.mention} accepted **{mission['title']}**.\n"
                "Post your proof for the mission here. This private thread is visible only to you and the mission reviewers."
            ),
            allowed_mentions=discord.AllowedMentions(
                users=[participant], roles=False, everyone=False
            ),
        )
    except Exception:
        try:
            await thread.delete(reason="Mission acceptance setup failed")
        except Exception:
            logger.exception("Failed to remove incomplete proof thread for mission #%s", mission["id"])
        raise

    return thread


def build_mission_embed(mission: dict, participants: List[str]) -> discord.Embed:
    """
    Build the premium mission card embed.

    participants — list of discord_id strings (accepted + not yet completed).
    Slot count is derived from len(participants).
    """
    from ..services.mission_service import format_remaining, is_expired

    status = mission.get("status", "active")

    # ── Expired state ──────────────────────────────────────────────────────────
    if status == "expired" or (status == "active" and is_expired(mission)):
        lines = [
            _SEP,
            "📜  **KINGDOM MISSION**",
            _SEP,
            "",
            "🩸  **Task:**",
            f"{mission['title']}",
            "",
            _SEP,
            "⏳  **STATUS**",
            _SEP,
            "",
            "*This mission has elapsed. The window has closed.*",
            "*The Kingdom no longer accepts submissions.*",
            "",
            _SEP,
        ]
        embed = discord.Embed(description="\n".join(lines), color=0x2C2C2C)
        embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ── Withdrawn/deleted state ────────────────────────────────────────────────
    if status == "deleted":
        lines = [
            _SEP,
            "📜  **KINGDOM MISSION**",
            _SEP,
            "",
            "🩸  **Task:**",
            f"{mission['title']}",
            "",
            _SEP,
            "🚫  **STATUS**",
            _SEP,
            "",
            "*This decree has been rescinded by the Kingdom.*",
            "*It will not be spoken of again.*",
            "",
            _SEP,
        ]
        embed = discord.Embed(description="\n".join(lines), color=_DARK)
        embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ── Active mission card ────────────────────────────────────────────────────
    description  = mission.get("description") or ""
    req_rank     = mission.get("required_rank") or "None"
    max_p        = mission.get("max_participants")
    repeat_limit = mission.get("repeat_limit")
    entry_cost   = mission.get("entry_cost", 0) or 0
    reward       = mission.get("reward", 0)
    remaining    = format_remaining(mission)

    count      = len(participants)
    is_full    = (max_p is not None and count >= max_p)
    slots_val  = f"{count}/{max_p}  {'⛔ FULL' if is_full else ''}" if max_p is not None else "Unlimited"
    repeat_val = str(repeat_limit) if repeat_limit is not None else "Unlimited"
    entry_val  = f"{entry_cost:,} {_DC}" if entry_cost > 0 else "Free"

    lines = [
        _SEP,
        "📜  **KINGDOM MISSION**",
        _SEP,
        "",
        "🩸  **Task:**",
        f"{mission['title']}",
    ]

    if description:
        lines += [
            "",
            "📖  **Description:**",
            f"{description}",
        ]

    lines += [
        "",
        _SEP,
        "⚔️  **CONDITIONS**",
        _SEP,
        "",
        f"👑  Required Rank:  **{req_rank}**",
        f"👥  Slots:  **{slots_val}**",
        f"🔁  Repeat Limit:  **{repeat_val}**",
        "",
        _SEP,
        "⏳  **TIME**",
        _SEP,
        "",
        f"Expires in:  **{remaining}**",
        "",
        _SEP,
        "💰  **REWARD**",
        _SEP,
        "",
        "Reward:",
        f"**{reward:,}** {_DC}",
        "",
        "Entry Cost:",
        entry_val,
        "",
        _SEP,
        "👥  **PARTICIPANTS**",
        _SEP,
        "",
    ]

    if participants:
        # Cap at 20 to avoid embed overflow
        shown  = participants[:20]
        plines = [f"{i + 1}. <@{uid}>" for i, uid in enumerate(shown)]
        if len(participants) > 20:
            plines.append(f"*... and {len(participants) - 20} more.*")
        lines += plines
    else:
        lines.append("*No participants yet.*")

    lines += ["", _SEP]

    description_text = "\n".join(lines)
    # Hard safety trim — Discord rejects >4096 chars
    if len(description_text) > _EMBED_MAX:
        description_text = description_text[:_EMBED_MAX - 3] + "..."

    embed = discord.Embed(description=description_text, color=_CRIMSON)
    embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
    return embed


class MissionView(discord.ui.View):
    """Persistent button view for a single mission post."""

    def __init__(self, mission_id: int, disabled: bool = False):
        super().__init__(timeout=None)
        self.mission_id = mission_id

        accept_btn = discord.ui.Button(
            label     = "Accept Mission",
            style     = discord.ButtonStyle.success,
            emoji     = "⚔️",
            custom_id = f"mission_accept:{mission_id}",
            disabled  = disabled,
        )
        accept_btn.callback = self._accept_callback
        self.add_item(accept_btn)

        decline_btn = discord.ui.Button(
            label     = "Decline Mission",
            style     = discord.ButtonStyle.secondary,
            emoji     = "✖️",
            custom_id = f"mission_decline:{mission_id}",
            disabled  = disabled,
        )
        decline_btn.callback = self._decline_callback
        self.add_item(decline_btn)

    # ──────────────────────────────────────────────────────────────────────────

    async def _accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        bot        = interaction.client
        db         = bot.db
        svc        = bot.mission_service
        guild_id   = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        username   = interaction.user.display_name
        mission_id = self.mission_id

        guild = interaction.guild
        mission = await db.get_mission(mission_id)
        if guild is None or mission is None or str(mission["guild_id"]) != guild_id:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="*This mission is not available in this server.*",
                    color=_CRIMSON,
                ),
                ephemeral=True,
            )
            return

        channel = bot.get_channel(int(mission["channel_id"]))
        if channel is None:
            try:
                channel = await bot.fetch_channel(int(mission["channel_id"]))
            except Exception:
                channel = None
        if channel is None:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="*The private proof channel is unavailable. Your mission was not accepted and no entry fee was charged.*",
                    color=_CRIMSON,
                ),
                ephemeral=True,
            )
            return

        try:
            proof_thread = await create_mission_proof_thread(
                guild, channel, interaction.user, mission
            )
        except Exception as exc:
            logger.warning(
                "[MissionView] private proof thread setup failed for mission=%s member=%s: %s",
                mission_id,
                discord_id,
                exc,
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    description=(
                        "*A private proof thread could not be created. "
                        "Your mission was not accepted and no entry fee was charged.* "
                        "Ask an administrator to check Create Private Threads and Manage Threads permissions."
                    ),
                    color=_CRIMSON,
                ),
                ephemeral=True,
            )
            return

        try:
            result = await svc.accept_mission(guild_id, discord_id, username, mission_id)
        except Exception:
            try:
                await proof_thread.delete(reason="Mission acceptance failed")
            except Exception:
                logger.exception("[MissionView] failed to remove unused proof thread for mission=%s", mission_id)
            raise

        if not result["ok"]:
            try:
                await proof_thread.delete(reason="Mission acceptance was rejected")
            except Exception:
                logger.exception("[MissionView] failed to remove rejected proof thread for mission=%s", mission_id)
            embed = discord.Embed(
                description = f"*{result['reason']}*",
                color       = _CRIMSON,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            await db.set_mission_participant_thread(
                mission_id, discord_id, str(proof_thread.id)
            )
        except Exception:
            logger.exception(
                "[MissionView] accepted mission but could not persist proof thread ID: mission=%s member=%s",
                mission_id,
                discord_id,
            )

        entry_cost = result.get("entry_cost", 0)

        if entry_cost > 0:
            desc = (
                f"*You have accepted the mission **{mission['title']}**.*\n"
                f"*Entry fee of **{entry_cost:,}** {_DC} has been collected.*\n\n"
                f"*Complete your task. The Kingdom is watching.*"
            )
        else:
            desc = (
                f"*You have accepted the mission **{mission['title']}**.*\n\n"
                f"*Complete your task. The Kingdom is watching.*"
            )

        embed = discord.Embed(
            title       = "⚔️  Mission Accepted",
            description = desc,
            color       = _GOLD,
        )
        embed.add_field(name="Reward",  value=f"**{mission['reward']:,}** {_DC}", inline=True)
        embed.add_field(name="Mission", value=f"**#{mission_id}**",             inline=True)
        embed.add_field(name="Private proof thread", value=proof_thread.mention, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Refresh the live mission card (participants + slot count)
        await self._refresh_post(interaction, mission_id)

    async def _decline_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description = (
                "*You have declined this mission.*\n"
                "*The Kingdom does not forget cowardice.*"
            ),
            color = _DARK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────

    async def _refresh_post(self, interaction: discord.Interaction, mission_id: int):
        """Edit the mission post with updated participants list and slot count."""
        try:
            db      = interaction.client.db
            mission = await db.get_mission(mission_id)
            if not mission or not mission.get("message_id"):
                return

            rows        = await db.get_mission_participants(mission_id)
            discord_ids = [r["discord_id"] for r in rows]

            embed   = build_mission_embed(mission, discord_ids)
            channel = interaction.client.get_channel(int(mission["channel_id"]))
            if channel is None:
                channel = await interaction.client.fetch_channel(int(mission["channel_id"]))
            msg = await channel.fetch_message(int(mission["message_id"]))
            await msg.edit(embed=embed)
        except Exception as exc:
            logger.debug(f"[MissionView] refresh_post failed: {exc}")
