import discord
from typing import List, Dict, Any, Callable, Awaitable
from ..utils.formatting import format_dc


ITEMS_PER_PAGE = 2


class BlackMarketView(discord.ui.View):
    """
    Paginated black market with per-item purchase buttons.
    buy_callback(interaction, item_id) handles the purchase and response.
    """

    def __init__(
        self,
        items: List[Dict[str, Any]],
        buy_callback: Callable[[discord.Interaction, int], Awaitable[None]],
    ):
        super().__init__(timeout=90)
        self.items        = items
        self.buy_callback = buy_callback
        self.page         = 0
        self.total_pages  = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self._rebuild_buttons()

    def _current_page_items(self) -> List[Dict[str, Any]]:
        start = self.page * ITEMS_PER_PAGE
        return self.items[start: start + ITEMS_PER_PAGE]

    def _rebuild_buttons(self):
        self.clear_items()

        page_items = self._current_page_items()
        for i, item in enumerate(page_items):
            ri = item.get("risk_increase", 0)
            rr = item.get("risk_reduce", 0)
            if ri > 0:
                risk_tag = f"  +{ri} Risk"
            elif rr > 0:
                risk_tag = f"  −{rr} Risk"
            else:
                risk_tag = ""
            label    = f"Acquire: {item['name']} — {format_dc(item['cost'])}{risk_tag}"
            item_id  = item["id"]
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.danger,
                row=i,
                custom_id=f"bm_buy_{item['id']}_{self.page}_{i}",
            )

            async def make_callback(inter: discord.Interaction, iid: int = item_id):
                await self.buy_callback(inter, iid)

            btn.callback = make_callback
            self.add_item(btn)

        # Navigation
        nav_row = min(len(page_items), 3)
        prev_label = f"◀  Page {self.page}" if self.page > 0 else "◀  Previous"
        next_label = f"Page {self.page + 2}  ▶" if self.page < self.total_pages - 1 else "Next  ▶"

        prev_btn = discord.ui.Button(
            label=prev_label,
            style=discord.ButtonStyle.secondary,
            disabled=self.page <= 0,
            row=nav_row,
            custom_id=f"bm_prev_{self.page}",
        )
        next_btn = discord.ui.Button(
            label=next_label,
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= self.total_pages - 1,
            row=nav_row,
            custom_id=f"bm_next_{self.page}",
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
