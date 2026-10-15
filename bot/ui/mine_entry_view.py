import asyncio
import discord
from typing import Callable, Awaitable, Optional


VOID_BLACK  = 0x0A0A0A
ENTRY_COLOR = 0x1A0000


class MineEntryView(discord.ui.View):
    """
    Entry gate for the Infernal Mines grind ritual.
    Only the command owner can interact. Disables all buttons on use or timeout.
    """

    def __init__(self, owner_id: int, timeout: int = 45):
        super().__init__(timeout=timeout)
        self.owner_id   = owner_id
        self.message: Optional[discord.Message] = None
        self._used      = False
        self._on_enter:     Optional[Callable] = None
        self._on_walk_away: Optional[Callable] = None

    # ─── Callback registration ────────────────────────────────

    def set_enter_callback(self, cb: Callable):
        self._on_enter = cb

    def set_walk_callback(self, cb: Callable):
        self._on_walk_away = cb

    # ─── Interaction guard ────────────────────────────────────

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        if inter.user.id != self.owner_id:
            await inter.response.send_message(
                "*These mines are not yours to enter.*", ephemeral=True
            )
            return False
        return True

    # ─── Buttons ──────────────────────────────────────────────

    @discord.ui.button(
        label="Enter the Mine",
        style=discord.ButtonStyle.success,
        emoji="⛏",
        custom_id="mine_enter",
    )
    async def enter(self, inter: discord.Interaction, button: discord.ui.Button):
        if self._used:
            return
        self._used = True
        self._disable_all()
        if self._on_enter:
            await self._on_enter(inter)

    @discord.ui.button(
        label="Walk Away",
        style=discord.ButtonStyle.secondary,
        emoji="🚪",
        custom_id="mine_walk",
    )
    async def walk_away(self, inter: discord.Interaction, button: discord.ui.Button):
        if self._used:
            return
        self._used = True
        self._disable_all()
        if self._on_walk_away:
            await self._on_walk_away(inter)

    # ─── Helpers ──────────────────────────────────────────────

    def _disable_all(self):
        for item in self.children:
            item.disabled = True
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message and not self._used:
            try:
                embed = discord.Embed(
                    title="⛏  Infernal Mines",
                    description=(
                        "*The mine entrance stands silent.*\n\n"
                        "*You did not step forward.*\n"
                        "*The opportunity has passed.*"
                    ),
                    color=VOID_BLACK,
                )
                embed.set_footer(text="Timed out  ·  Kingdom Treasury")
                await self.message.edit(embed=embed, view=self, attachments=[])
            except Exception:
                pass
