"""
MissionView — Persistent button UI for Kingdom Missions.

Buttons survive bot restarts because:
  - timeout=None
  - custom_ids encode mission_id
  - bot.add_view(MissionView(mission_id)) is called on startup for every active mission
"""

import discord
import logging

logger = logging.getLogger("kingdom_treasury")

_CRIMSON = 0x6B0000
_GOLD    = 0xFFD700
_DARK    = 0x0A0A0A


def build_mission_embed(mission: dict, participant_count: int) -> discord.Embed:
    """Build the mission announcement embed from a mission record."""
    from ..services.mission_service import format_remaining, is_expired

    status = mission.get("status", "active")

    if status == "expired" or is_expired(mission):
        embed = discord.Embed(
            title       = f"📋  {mission['title']}",
            description = "*This mission has expired.*",
            color       = 0x2C2C2C,
        )
        embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    if status == "deleted":
        embed = discord.Embed(
            title       = f"📋  {mission['title']}",
            description = "*This mission has been withdrawn by the Kingdom.*",
            color       = _DARK,
        )
        embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    embed = discord.Embed(
        title = f"📋  {mission['title']}",
        color = _CRIMSON,
    )

    # Core fields
    embed.add_field(name="💰  Reward",    value=f"**{mission['reward']:,} DC**", inline=True)
    embed.add_field(name="🆔  Mission",   value=f"**#{mission['id']}**",         inline=True)

    # Entry cost
    entry = mission.get("entry_cost", 0) or 0
    if entry > 0:
        embed.add_field(name="🎟  Entry Cost", value=f"**{entry:,} DC**", inline=True)

    # Slots
    max_p = mission.get("max_participants")
    if max_p is not None:
        embed.add_field(
            name  = "👥  Slots",
            value = f"**{participant_count}/{max_p}**",
            inline= True,
        )
    else:
        embed.add_field(name="👥  Slots", value="**Unlimited**", inline=True)

    # Required rank
    req_rank = mission.get("required_rank")
    if req_rank:
        embed.add_field(name="👑  Required Rank", value=f"**{req_rank}**", inline=True)

    # Time remaining
    remaining = format_remaining(mission)
    embed.add_field(name="⏱  Expires", value=f"**{remaining}**", inline=True)

    embed.set_footer(text=f"Mission #{mission['id']}  ·  Kingdom Treasury  ·  Kingdom of Hell")
    return embed


class MissionView(discord.ui.View):
    """Persistent button view for a single mission post."""

    def __init__(self, mission_id: int, disabled: bool = False):
        super().__init__(timeout=None)
        self.mission_id = mission_id

        accept_btn = discord.ui.Button(
            label    = "Accept Mission",
            style    = discord.ButtonStyle.success,
            emoji    = "⚔️",
            custom_id= f"mission_accept:{mission_id}",
            disabled = disabled,
        )
        accept_btn.callback = self._accept_callback
        self.add_item(accept_btn)

        decline_btn = discord.ui.Button(
            label    = "Decline",
            style    = discord.ButtonStyle.secondary,
            emoji    = "✖️",
            custom_id= f"mission_decline:{mission_id}",
            disabled = disabled,
        )
        decline_btn.callback = self._decline_callback
        self.add_item(decline_btn)

    # ──────────────────────────────────────────────────────────────────────────

    async def _accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        bot         = interaction.client
        db          = bot.db
        svc         = bot.mission_service
        guild_id    = str(interaction.guild_id)
        discord_id  = str(interaction.user.id)
        username    = interaction.user.display_name
        mission_id  = self.mission_id

        result = await svc.accept_mission(guild_id, discord_id, username, mission_id)

        if not result["ok"]:
            embed = discord.Embed(
                description = f"*{result['reason']}*",
                color       = _CRIMSON,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Success — build confirmation
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
        embed.add_field(name="Reward", value=f"**{mission['reward']:,} DC**", inline=True)
        embed.add_field(name="Mission", value=f"**#{mission_id}**",            inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Refresh the mission post to update slot count
        await self._refresh_post(interaction, mission_id)

    async def _decline_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description = "*You have declined this mission. The Kingdom does not forget cowardice.*",
            color       = _DARK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────

    async def _refresh_post(self, interaction: discord.Interaction, mission_id: int):
        """Edit the mission post message to reflect updated slot count."""
        try:
            db       = interaction.client.db
            mission  = await db.get_mission(mission_id)
            if not mission or not mission.get("message_id"):
                return
            count   = await db.count_mission_participants(mission_id)
            embed   = build_mission_embed(mission, count)
            channel = interaction.client.get_channel(int(mission["channel_id"]))
            if channel is None:
                return
            msg = await channel.fetch_message(int(mission["message_id"]))
            await msg.edit(embed=embed)
        except Exception as exc:
            logger.debug(f"[MissionView] refresh_post failed: {exc}")
