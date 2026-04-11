"""
Ascension Ritual — paginated rank-shop with per-rank Ascend buttons.
Caller-locked: only the user who opened /ascend can interact.
Strict progression: only the immediate next rank button is enabled.
"""
import math
import discord
from typing import List, Tuple, Callable, Awaitable, Optional

VOID_BLACK = 0x0A0A0A
DARK_RED   = 0x8B0000
GOLD       = 0xFFD700

PAGE_SIZE  = 4


class AscendView(discord.ui.View):
    def __init__(
        self,
        ranks:        List[Tuple[str, int, float]],   # (name, cost, tax_rate)
        owner_id:     int,
        current_rank: str,
        next_rank:    Optional[str],
        ascend_cb:    Callable[[discord.Interaction, str, int], Awaitable[None]],
    ):
        super().__init__(timeout=180)
        self.ranks        = ranks
        self.owner_id     = owner_id
        self.current_rank = current_rank
        self.next_rank    = next_rank
        self.ascend_cb    = ascend_cb
        self.page         = 0
        self.total_pages  = max(1, math.ceil(len(ranks) / PAGE_SIZE))
        self._jump_to_next()
        self._rebuild()

    def _jump_to_next(self):
        """Open the page that contains the next ascendable rank."""
        if not self.next_rank:
            return
        for i, (name, _, _) in enumerate(self.ranks):
            if name == self.next_rank:
                self.page = i // PAGE_SIZE
                return

    def _current(self) -> List[Tuple[str, int, float]]:
        s = self.page * PAGE_SIZE
        return self.ranks[s: s + PAGE_SIZE]

    # ── embed ─────────────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        next_label = (
            f"**{self.next_rank}**" if self.next_rank
            else "*You stand at the Apex of the Kingdom.*"
        )
        embed = discord.Embed(
            title="👑  Ascension Ritual — Rank Hierarchy",
            description=(
                f"*Current Rank:* **{self.current_rank}**\n"
                f"*Next Ascension:* {next_label}\n\n"
                "*The ritual is strict. Ascend one step at a time. No skipping.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)

        for name, cost, tax_rate in self._current():
            is_next = name == self.next_rank
            marker  = "⚔ **AVAILABLE**" if is_next else "🔒 Locked"
            tax_pct = f"{int(tax_rate * 100)}%"
            embed.add_field(
                name=f"{'⚔' if is_next else '🔒'}  **{name}**",
                value=f"Cost: **{cost:,}** <:devilcoinStack:1492184333392412692>\nTax Rate: **{tax_pct}**\n{marker}",
                inline=True,
            )

        embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        embed.set_footer(
            text=f"Page {self.page + 1} / {self.total_pages}  ·  Kingdom Treasury  ·  Kingdom of Hell"
        )
        return embed

    # ── view rebuild ──────────────────────────────────────────────────────────

    def _rebuild(self):
        self.clear_items()
        current = self._current()

        prev = discord.ui.Button(
            label="◀  Previous", style=discord.ButtonStyle.secondary,
            row=0, disabled=self.page == 0,
        )
        nxt = discord.ui.Button(
            label="Next  ▶", style=discord.ButtonStyle.secondary,
            row=0, disabled=self.page >= self.total_pages - 1,
        )
        prev.callback = self._prev_cb
        nxt.callback  = self._next_cb
        self.add_item(prev)
        self.add_item(nxt)

        for i, (name, cost, _) in enumerate(current):
            is_next = name == self.next_rank
            btn = discord.ui.Button(
                label    = f"⚔  Ascend → {name}" if is_next else f"🔒  {name}",
                style    = discord.ButtonStyle.danger if is_next else discord.ButtonStyle.secondary,
                row      = i + 1,
                disabled = not is_next,
            )
            if is_next:
                btn.callback = self._make_ascend_cb(name, cost)
            else:
                btn.callback = self._locked_cb
            self.add_item(btn)

    # ── nav callbacks ─────────────────────────────────────────────────────────

    async def _prev_cb(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This ascension ritual belongs to another soul.*", ephemeral=True
            )
            return
        self.page = max(0, self.page - 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next_cb(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This ascension ritual belongs to another soul.*", ephemeral=True
            )
            return
        self.page = min(self.total_pages - 1, self.page + 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _locked_cb(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "*You must ascend in order. The ritual demands strict progression.*",
            ephemeral=True,
        )

    # ── ascend callback factory ───────────────────────────────────────────────

    def _make_ascend_cb(self, rank_name: str, cost: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message(
                    "*This ascension ritual belongs to another soul.*", ephemeral=True
                )
                return

            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            await interaction.response.edit_message(view=self)
            await self.ascend_cb(interaction, rank_name, cost)

        return callback
