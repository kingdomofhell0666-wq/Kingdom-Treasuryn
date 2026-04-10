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

logger = logging.getLogger("kingdom_treasury")

_CRIMSON = 0x6B0000
_GOLD    = 0xFFD700
_DARK    = 0x0A0A0A

_SEP = "━━━━━━━━━━━━━━━━━━━"
_DC  = "<:devilcoins:1491713762217168916>"

# Discord embed description hard limit
_EMBED_MAX = 4000


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

        result = await svc.accept_mission(guild_id, discord_id, username, mission_id)

        if not result["ok"]:
            embed = discord.Embed(
                description = f"*{result['reason']}*",
                color       = _CRIMSON,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        mission    = await db.get_mission(mission_id)
        entry_cost = result.get("entry_cost", 0)

        if entry_cost > 0:
            desc = (
                f"*You have accepted the mission **{mission['title']}**.*\n"
                f"*Entry fee of **{entry_cost:,} DC** has been collected.*\n\n"
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
        embed.add_field(name="Reward",  value=f"**{mission['reward']:,} DC**", inline=True)
        embed.add_field(name="Mission", value=f"**#{mission_id}**",             inline=True)
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
