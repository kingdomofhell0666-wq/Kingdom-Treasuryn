import discord
from typing import Callable, Awaitable
from ..utils.formatting import format_dc


VOID_BLACK = 0x0A0A0A
GOLD       = 0xFFD700
BLOOD_RED  = 0x6B0000


class AscendConfirmView(discord.ui.View):
    """
    Two-button confirmation ritual for /ascend.
    Calls confirm_callback(interaction) on confirm.
    Expires after 45 seconds with a timeout message.
    """

    def __init__(
        self,
        rank_name: str,
        cost: int,
        confirm_callback: Callable[[discord.Interaction], Awaitable[None]],
    ):
        super().__init__(timeout=45)
        self.rank_name       = rank_name
        self.cost            = cost
        self.confirm_callback = confirm_callback
        self.resolved        = False

    def _disable_all(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    @discord.ui.button(
        label="⚔  Confirm Ascension",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._disable_all()
        await interaction.response.edit_message(view=self)
        await self.confirm_callback(interaction)

    @discord.ui.button(
        label="✦  Step Away",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._disable_all()
        embed = discord.Embed(
            title="👑  Ascension Abandoned",
            description=(
                f"*The ritual for **{self.rank_name}** has been abandoned.*\n"
                f"*Your wealth remains in your coffers, untouched.*"
            ),
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        self._disable_all()
