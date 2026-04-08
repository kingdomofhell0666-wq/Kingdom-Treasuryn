import discord
from typing import Optional
from .formatting import format_dc, format_tax_rate, format_cost


DARK_RED = 0x8B0000
CRIMSON = 0xB22222
GOLD = 0xFFD700
VOID_BLACK = 0x0A0A0A
BLOOD_RED = 0x6B0000

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━"

WEALTH_QUOTES = [
    "The Abyss grows heavier in your favor.",
    "The Kingdom acknowledges your holdings.",
    "Wealth is power. Power is survival.",
    "Your coffers speak louder than your rank.",
    "The Treasury watches. Always.",
]

import random


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
        taxes_paid = user_data.get("taxes_paid", 0)
        username = user_data.get("username", "Unknown")

        display_name = mention if mention else f"**{username}**"

        embed = discord.Embed(
            title="👑  Kingdom Identity Card",
            description=display_name,
            color=BLOOD_RED,
        )

        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="\u200b", value=SEP, inline=False)

        embed.add_field(
            name="Rank",
            value=rank,
            inline=True,
        )
        embed.add_field(
            name="Title",
            value=f"*{title}*",
            inline=True,
        )

        embed.add_field(name="\u200b", value=SEP, inline=False)

        embed.add_field(
            name="💰  Wealth",
            value=f"{format_dc(balance)}\nKingdom Rank: **#{kingdom_rank}**",
            inline=False,
        )

        embed.add_field(name="\u200b", value=SEP, inline=False)

        embed.add_field(
            name="📊  Stats",
            value=f"Taxes Paid: **{format_dc(taxes_paid)}**",
            inline=False,
        )

        embed.add_field(name="\u200b", value=SEP, inline=False)

        embed.set_footer(text='"The Abyss remembers your name."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def wealth(user_data: dict) -> discord.Embed:
        balance = user_data.get("balance", 0)
        quote = random.choice(WEALTH_QUOTES)

        embed = discord.Embed(
            description=(
                f"💰  You possess **{format_dc(balance)}**\n"
                f'*"{quote}"*'
            ),
            color=DARK_RED,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def vault(treasury_balance: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏦  Kingdom Treasury",
            description="*The central reserve of the Kingdom of Hell. Untouchable. Absolute.*",
            color=GOLD,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="TOTAL RESERVES",
            value=f"**{format_dc(treasury_balance)}**",
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def grind_result(result: dict) -> discord.Embed:
        gross = result["gross"]
        tax_rate = result["tax_rate"]
        tax_amount = result["tax_amount"]
        net = result["net"]
        new_balance = result["new_balance"]
        success = result["success"]

        if not success:
            embed = discord.Embed(
                title="⛏️  Infernal Mines",
                description=(
                    "*The rock yields nothing.\n"
                    "The darkness consumes your effort.*"
                ),
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        embed = discord.Embed(
            title="⛏️  Infernal Mines",
            description="*You descended into the deep. The mines yield their reward.*",
            color=CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="EXTRACTION",
            value=(
                f"```"
                f"Raw   {format_dc(gross):>16}\n"
                f"Tax   -{format_dc(tax_amount):>15}  ({format_tax_rate(tax_rate)})\n"
                f"Net   +{format_dc(net):>15}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="BALANCE",
            value=f"**{format_dc(new_balance)}**",
            inline=False,
        )
        embed.set_footer(text='"The Kingdom takes its share."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def tribute_result(result: dict) -> discord.Embed:
        gross = result["gross"]
        bonus = result["bonus"]
        tax_amount = result["tax_amount"]
        tax_rate = result["tax_rate"]
        net = result["net"]
        new_balance = result["new_balance"]

        embed = discord.Embed(
            title="🩸  Royal Tribute",
            description="*The realm renders its offering. Your loyalty is recorded.*",
            color=CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        bonus_line = f"\nBonus +{format_dc(bonus):>14}  (grind ×5)" if bonus > 0 else ""
        embed.add_field(
            name="TRIBUTE LEDGER",
            value=(
                f"```"
                f"Base  +{format_dc(gross - bonus):>14}{bonus_line}\n"
                f"Tax    -{format_dc(tax_amount):>14}  ({format_tax_rate(tax_rate)})\n"
                f"Net   +{format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="BALANCE",
            value=f"**{format_dc(new_balance)}**",
            inline=False,
        )
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
            title="💸  Wealth Transfer",
            description="*The transaction is sealed. The Treasury has taken its levy.*",
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="LEDGER",
            value=(
                f"```"
                f"From      {sender_name}\n"
                f"To        {recipient_name}\n"
                f"Amount    {format_dc(amount):>12}\n"
                f"Levy      -{format_dc(tax):>11}  (2%)\n"
                f"Received  +{format_dc(net):>11}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="YOUR BALANCE",
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
            title="👑  Ascension",
            description=f"*Your ascension is recorded in the Kingdom's ledger. The title is yours.*",
            color=GOLD,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="NEW RANK",
            value=f"**{rank_name}**",
            inline=False,
        )
        embed.add_field(
            name="PAYMENT BREAKDOWN",
            value=(
                f"```"
                f"Cost       {format_dc(cost):>12}\n"
                f"Treasury   +{format_dc(treasury_cut):>11}  (10%)\n"
                f"Burned     {format_dc(burned):>12}  (90%)"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="REMAINING BALANCE",
            value=f"**{format_dc(new_balance)}**",
            inline=False,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def cooldown_error(action: str, remaining_str: str) -> discord.Embed:
        FLAVOR = {
            "grind": "The mines have not yet recovered. The rock demands rest.",
            "tribute": "The realm has not forgotten your last tribute.",
        }
        flavor = FLAVOR.get(action, "The Kingdom demands patience.")
        embed = discord.Embed(
            description=f"*{flavor}*\n\n**Return in:** `{remaining_str}`",
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
            title="🏪  Kingdom Market",
            description=(
                "*Ascend. Compete. Dominate.*\n"
                "*Each rank carries its price — and its burden.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for name, cost, tax_rate in ranks:
            embed.add_field(
                name=f"**{name}**",
                value=(
                    f"Cost: **{format_cost(cost)}**\n"
                    f"Tax: {format_tax_rate(tax_rate)}"
                ),
                inline=True,
            )
        embed.set_footer(
            text=f"Page {page} of {total_pages}  ·  Use /ascend <rank>  ·  Kingdom Treasury"
        )
        return embed
