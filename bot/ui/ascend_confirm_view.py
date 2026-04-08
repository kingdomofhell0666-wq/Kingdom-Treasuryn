import discord
from typing import Callable, Awaitable


class AscendConfirmView(discord.ui.View):
    """
    Two-button confirmation for /ascend.
    Calls confirm_callback on confirm, cancels on dismiss.
    """

    def __init__(
        self,
        rank_name: str,
        cost: int,
        confirm_callback: Callable[[], Awaitable[None]],
    ):
        super().__init__(timeout=45)
        self.rank_name = rank_name
        self.cost = cost
        self.confirm_callback = confirm_callback
        self.resolved = False

    @discord.ui.button(label="⚔  Confirm Ascension", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._disable_all()
        await interaction.response.edit_message(view=self)
        await self.confirm_callback(interaction)

    @discord.ui.button(label="Withdraw", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.resolved:
            await interaction.response.defer()
            return
        self.resolved = True
        self._disable_all()
        embed = discord.Embed(
            description="*The ascension ritual is cancelled. Your wealth remains untouched.*",
            color=0x0A0A0A,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        self._disable_all()

    def _disable_all(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
