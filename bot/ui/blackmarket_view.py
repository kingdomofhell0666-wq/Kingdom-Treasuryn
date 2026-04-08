import discord
from typing import List, Dict, Any, Callable, Awaitable
from ..utils.formatting import format_dc


ITEMS_PER_PAGE = 2


class BlackMarketView(discord.ui.View):
    """
    Paginated black market with per-item Buy buttons.
    buy_callback(interaction, item_id) handles the purchase logic.
    """

    def __init__(
        self,
        items: List[Dict[str, Any]],
        buy_callback: Callable[[discord.Interaction, int], Awaitable[None]],
    ):
        super().__init__(timeout=60)
        self.items = items
        self.buy_callback = buy_callback
        self.page = 0
        self.total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self._rebuild_buttons()

    def _current_page_items(self) -> List[Dict[str, Any]]:
        start = self.page * ITEMS_PER_PAGE
        return self.items[start: start + ITEMS_PER_PAGE]

    def _rebuild_buttons(self):
        self.clear_items()

        page_items = self._current_page_items()
        for i, item in enumerate(page_items):
            label = f"Buy: {item['name']} — {format_dc(item['cost'])}"
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.danger,
                row=i,
                custom_id=f"bm_buy_{item['id']}",
            )
            item_id = item["id"]

            async def make_callback(inter: discord.Interaction, iid: int = item_id):
                await self.buy_callback(inter, iid)

            btn.callback = make_callback
            self.add_item(btn)

        # Navigation row
        prev_btn = discord.ui.Button(
            label="◀ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=self.page <= 0,
            row=3,
            custom_id="bm_prev",
        )
        next_btn = discord.ui.Button(
            label="Next ▶",
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= self.total_pages - 1,
            row=3,
            custom_id="bm_next",
        )

        async def prev_callback(inter: discord.Interaction):
            self.page = max(0, self.page - 1)
            self._rebuild_buttons()
            await inter.response.edit_message(embed=self._build_embed(), view=self)

        async def next_callback(inter: discord.Interaction):
            self.page = min(self.total_pages - 1, self.page + 1)
            self._rebuild_buttons()
            await inter.response.edit_message(embed=self._build_embed(), view=self)

        prev_btn.callback = prev_callback
        next_btn.callback = next_callback
        self.add_item(prev_btn)
        self.add_item(next_btn)

    def _build_embed(self) -> discord.Embed:
        from ..utils.embeds import EmbedFactory
        return EmbedFactory.blackmarket_page(
            self._current_page_items(), self.page + 1, self.total_pages
        )

    def build_embed(self) -> discord.Embed:
        return self._build_embed()
