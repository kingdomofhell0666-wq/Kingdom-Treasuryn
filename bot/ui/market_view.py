"""
Infernal Market — paginated cosmetics shop with per-item Buy buttons.
Caller-locked: only the user who opened /market can interact.
"""
import math
import discord
from dataclasses import dataclass
from typing import List, Set

VOID_BLACK = 0x0A0A0A
BLOOD_RED  = 0x6B0000
GOLD       = 0xFFD700

PAGE_SIZE  = 4

RARITY_DOT = {
    "Default":   "⬜", "Common":    "🔘", "Uncommon":  "🟢",
    "Rare":      "🔵", "Epic":      "🟣", "Legendary": "🟡", "Special":   "🔴",
}
TYPE_ICON = {"skin": "🎨", "title": "🎭"}


@dataclass
class MarketItem:
    id:          str
    name:        str
    item_type:   str   # "skin" | "title"
    price:       int
    description: str
    rarity:      str


class MarketView(discord.ui.View):
    def __init__(
        self,
        items:          List[MarketItem],
        owner_id:       int,
        bot,
        guild_id:       str,
        discord_id:     str,
        owned_skins:    List[str],
        owned_titles:   List[str],
        equipped_skin:  str,
        equipped_title: str,
    ):
        super().__init__(timeout=180)
        self.items          = items
        self.owner_id       = owner_id
        self.bot            = bot
        self.guild_id       = guild_id
        self.discord_id     = discord_id
        self.owned_skins:   Set[str] = set(owned_skins)
        self.owned_titles:  Set[str] = set(owned_titles)
        self.equipped_skin  = equipped_skin
        self.equipped_title = equipped_title
        self.page           = 0
        self.total_pages    = max(1, math.ceil(len(items) / PAGE_SIZE))
        self._rebuild()

    # ── ownership helpers ──────────────────────────────────────────────────────

    def _is_owned(self, item: MarketItem) -> bool:
        if item.item_type == "skin":
            return item.id in self.owned_skins or item.price == 0
        return item.id in self.owned_titles or item.price == 0

    def _is_equipped(self, item: MarketItem) -> bool:
        if item.item_type == "skin":
            return item.id == self.equipped_skin
        return item.id == self.equipped_title

    def _status(self, item: MarketItem) -> str:
        if self._is_equipped(item):
            return "✦ **[EQUIPPED]**"
        if self._is_owned(item):
            return "✓ Owned"
        if item.price == 0:
            return "✓ Free"
        return f"🔒 {item.price:,} <:devilcoinStack:1492184333392412692>"

    # ── embed ─────────────────────────────────────────────────────────────────

    def _current(self) -> List[MarketItem]:
        s = self.page * PAGE_SIZE
        return self.items[s: s + PAGE_SIZE]

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛒  Infernal Market — Cosmetics",
            description=(
                "*Acquire skins and titles with* <:devilcoinStack:1492184333392412692>.\n"
                "*Press **Buy** to purchase. Use `/equip-skin` or `/equip-title` to activate.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        for item in self._current():
            dot    = RARITY_DOT.get(item.rarity, "⬜")
            icon   = TYPE_ICON.get(item.item_type, "")
            status = self._status(item)
            embed.add_field(
                name=f"{dot} {icon} **{item.name}**  ·  *{item.rarity}*",
                value=f"*{item.description}*\n{status}",
                inline=False,
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

        for i, item in enumerate(current):
            owned = self._is_owned(item)
            btn   = discord.ui.Button(
                label  = f"✓ {item.name}" if owned else f"Buy {item.name}",
                style  = discord.ButtonStyle.secondary if owned else discord.ButtonStyle.danger,
                row    = i + 1,
                disabled = owned,
            )
            btn.callback = self._make_buy_cb(item)
            self.add_item(btn)

    # ── nav callbacks ─────────────────────────────────────────────────────────

    async def _prev_cb(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This infernal market session belongs to another soul.*", ephemeral=True
            )
            return
        self.page = max(0, self.page - 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next_cb(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "*This infernal market session belongs to another soul.*", ephemeral=True
            )
            return
        self.page = min(self.total_pages - 1, self.page + 1)
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ── buy callback factory ──────────────────────────────────────────────────

    def _make_buy_cb(self, item: MarketItem):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message(
                    "*This infernal market session belongs to another soul.*", ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)
            svc = self.bot.cosmetic_service

            try:
                if item.item_type == "skin":
                    result = await svc.buy_skin(self.guild_id, self.discord_id, item.id)
                    self.owned_skins.add(item.id)
                    cost        = result["cost"]
                    new_balance = result["new_balance"]
                else:
                    result = await svc.buy_title(self.guild_id, self.discord_id, item.id)
                    self.owned_titles.add(item.id)
                    cost        = result["cost"]
                    new_balance = result["new_balance"]

                ledger = getattr(self.bot, "ledger_service", None)
                if ledger and cost > 0:
                    await ledger.log(
                        action          = "market_purchase",
                        amount          = cost,
                        from_label      = f"<@{self.discord_id}>",
                        to_label        = f"Kingdom Market — {item.name}",
                        guild_id        = self.guild_id,
                        from_discord_id = self.discord_id,
                        wallet_before   = new_balance + cost,
                        wallet_after    = new_balance,
                        action_type     = "market",
                    )

                confirm = _success_embed(item, cost, new_balance)
            except ValueError as e:
                confirm = _error_embed(str(e))

            self._rebuild()
            await interaction.message.edit(embed=self.build_embed(), view=self)
            await interaction.followup.send(embed=confirm, ephemeral=True)

        return callback


# ── standalone embed helpers ───────────────────────────────────────────────────

def _success_embed(item: MarketItem, cost: int, new_balance: int) -> discord.Embed:
    icon  = TYPE_ICON.get(item.item_type, "🛒")
    embed = discord.Embed(
        title=f"{icon}  Acquired — {item.name}",
        description=f"*{item.description}*",
        color=GOLD,
    )
    embed.add_field(name="COST",    value=f"**{cost:,}** <:devilcoinStack:1492184333392412692>",        inline=True)
    embed.add_field(name="BALANCE", value=f"**{new_balance:,}** <:devilcoinStack:1492184333392412692>", inline=True)
    embed.add_field(name="RARITY",  value=item.rarity,               inline=True)
    hint = "/equip-skin" if item.item_type == "skin" else "/equip-title"
    embed.add_field(
        name="\u200b",
        value=f"*Use `{hint}` to activate it on your Identity Card.*",
        inline=False,
    )
    embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
    return embed


def _error_embed(msg: str) -> discord.Embed:
    embed = discord.Embed(description=f"*{msg}*", color=VOID_BLACK)
    embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
    return embed
