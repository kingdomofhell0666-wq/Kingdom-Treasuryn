import discord
from typing import Optional, Dict, Any
from .formatting import format_dc, format_tax_rate, format_cost


DARK_RED = 0x8B0000
CRIMSON = 0xB22222
GOLD = 0xFFD700
VOID_BLACK = 0x0A0A0A
BLOOD_RED = 0x6B0000


class EmbedFactory:

    @staticmethod
    def base(title: str = "", description: str = "", color: int = DARK_RED) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def identity(
        user_data: dict,
        kingdom_rank: int,
        avatar_url: Optional[str] = None,
        mention: Optional[str] = None,
    ) -> discord.Embed:
        rank = user_data.get("rank", "Forsaken")
        title = user_data.get("title", "Unmarked")
        balance = user_data.get("balance", 0)
        duels_won = user_data.get("duels_won", 0)
        duels_lost = user_data.get("duels_lost", 0)
        taxes_paid = user_data.get("taxes_paid", 0)
        username = user_data.get("username", "Unknown")

        embed = discord.Embed(
            color=BLOOD_RED,
        )

        subject = mention if mention else f"**{username}**"
        embed.description = (
            f"*The Abyss remembers your name.*\n\u200b"
        )

        embed.add_field(
            name="▸ IDENTITY",
            value=(
                f"**Name** — {subject}\n"
                f"**Rank** — {rank}\n"
                f"**Title** — *{title}*"
            ),
            inline=False,
        )
        embed.add_field(
            name="▸ WEALTH",
            value=(
                f"**Wallet** — {format_dc(balance)}\n"
                f"**Kingdom Rank** — #{kingdom_rank}"
            ),
            inline=False,
        )
        embed.add_field(
            name="▸ RECORD",
            value=(
                f"**Duels Won** — {duels_won:,}\n"
                f"**Duels Lost** — {duels_lost:,}\n"
                f"**Taxes Paid** — {format_dc(taxes_paid)}"
            ),
            inline=False,
        )

        embed.set_author(name="KINGDOM IDENTITY CARD", icon_url=avatar_url or discord.Embed.Empty)
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def wealth(user_data: dict, kingdom_rank: int) -> discord.Embed:
        balance = user_data.get("balance", 0)
        rank = user_data.get("rank", "Forsaken")
        embed = discord.Embed(color=DARK_RED)
        embed.add_field(
            name="COFFERS",
            value=f"```{format_dc(balance)}```",
            inline=False,
        )
        embed.add_field(name="RANK", value=rank, inline=True)
        embed.add_field(name="STANDING", value=f"#{kingdom_rank}", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def grind_success(result: dict) -> discord.Embed:
        gross = result["gross"]
        tax_rate = result["tax_rate"]
        tax_amount = result["tax_amount"]
        net = result["net"]
        new_balance = result["new_balance"]
        outcome_label = result.get("outcome_label", "common")

        FLAVOR = {
            "common":   "The mines yield their reward.",
            "meager":   "The veins run thin. Scant DevilCoins are recovered.",
            "rich":     "A rich vein is struck. The haul is considerable.",
            "legendary": "The abyss opens. Wealth beyond measure flows forth.",
            "failure":  "The mines are silent. Nothing stirs in the deep.",
        }

        flavor = FLAVOR.get(outcome_label, FLAVOR["common"])

        if outcome_label == "failure":
            embed = discord.Embed(
                description=f"**{flavor}**",
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        embed = discord.Embed(
            description=f"*{flavor}*",
            color=CRIMSON if outcome_label != "legendary" else GOLD,
        )
        embed.add_field(
            name="EXTRACTION",
            value=(
                f"```"
                f"Gross   {format_dc(gross):>14}\n"
                f"Tax     {format_dc(tax_amount):>14}  ({format_tax_rate(tax_rate)})\n"
                f"Net     {format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def tribute_success(result: dict) -> discord.Embed:
        gross = result["gross"]
        bonus = result["bonus"]
        tax_amount = result["tax_amount"]
        tax_rate = result["tax_rate"]
        net = result["net"]
        new_balance = result["new_balance"]

        embed = discord.Embed(
            description="*The realm renders its tribute. The Kingdom acknowledges your service.*",
            color=CRIMSON,
        )

        bonus_line = f"\nBonus   {format_dc(bonus):>14}  (grind ×5)" if bonus > 0 else ""
        embed.add_field(
            name="TRIBUTE LEDGER",
            value=(
                f"```"
                f"Gross   {format_dc(gross):>14}{bonus_line}\n"
                f"Tax     {format_dc(tax_amount):>14}  ({format_tax_rate(tax_rate)})\n"
                f"Net     {format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def transfer_success(
        sender_name: str,
        recipient_name: str,
        amount: int,
        tax: int,
        net: int,
        sender_balance: int,
    ) -> discord.Embed:
        embed = discord.Embed(
            description="*The transfer is sealed. The Treasury has taken its levy.*",
            color=DARK_RED,
        )
        embed.add_field(
            name="TRANSFER LEDGER",
            value=(
                f"```"
                f"From    {sender_name}\n"
                f"To      {recipient_name}\n"
                f"Amount  {format_dc(amount):>14}\n"
                f"Levy    {format_dc(tax):>14}  (2%)\n"
                f"Recv'd  {format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(
            name="YOUR REMAINING BALANCE",
            value=f"**{format_dc(sender_balance)}**",
            inline=False,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def ascend_success(rank_name: str, cost: int, new_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned = cost - treasury_cut

        embed = discord.Embed(
            description=f"*Your ascension is recorded in the Kingdom's ledger. The title is yours.*",
            color=GOLD,
        )
        embed.add_field(
            name="ASCENSION",
            value=f"**{rank_name}**",
            inline=False,
        )
        embed.add_field(
            name="PAYMENT",
            value=(
                f"```"
                f"Cost    {format_dc(cost):>14}\n"
                f"Treasury {format_dc(treasury_cut):>13}  (10%)\n"
                f"Burned  {format_dc(burned):>14}  (90%)"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="REMAINING BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def cooldown_error(action: str, remaining_str: str) -> discord.Embed:
        FLAVOR = {
            "grind": "The mines have not yet recovered.",
            "tribute": "The realm has not forgotten your last tribute.",
        }
        flavor = FLAVOR.get(action, "The Kingdom demands patience.")
        embed = discord.Embed(
            description=f"*{flavor}*\n\n**Return in:** {remaining_str}",
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def error(message: str) -> discord.Embed:
        embed = discord.Embed(
            description=f"*{message}*",
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def market_page(ranks: list, page: int, total_pages: int) -> discord.Embed:
        embed = discord.Embed(
            title="THE KINGDOM MARKET",
            description="*Ascend. Compete. Dominate. Each rank carries its price — and its burden.*",
            color=BLOOD_RED,
        )
        for name, cost, tax_rate in ranks:
            embed.add_field(
                name=f"⬛ {name}",
                value=(
                    f"**Cost** — {format_cost(cost)}\n"
                    f"**Tax Rate** — {format_tax_rate(tax_rate)}"
                ),
                inline=True,
            )
        embed.set_footer(
            text=f"Kingdom Treasury  ·  Page {page}/{total_pages}  ·  Use /ascend <rank>"
        )
        return embed
