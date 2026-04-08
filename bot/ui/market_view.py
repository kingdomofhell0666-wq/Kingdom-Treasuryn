import discord
from typing import List, Tuple
from ..utils.embeds import EmbedFactory


ITEMS_PER_PAGE = 6


class MarketView(discord.ui.View):
    def __init__(self, ranks: List[Tuple[str, int, float]]):
        super().__init__(timeout=120)
        self.ranks = ranks
        self.page = 1
        self.total_pages = max(1, (len(ranks) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= self.total_pages

    def _get_current_page_ranks(self) -> List[Tuple[str, int, float]]:
        start = (self.page - 1) * ITEMS_PER_PAGE
        return self.ranks[start: start + ITEMS_PER_PAGE]

    def build_embed(self) -> discord.Embed:
        return EmbedFactory.market_page(
            self._get_current_page_ranks(), self.page, self.total_pages
        )

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.total_pages, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
