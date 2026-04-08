import discord
import random
from typing import Optional, List, Dict, Any
from .formatting import format_dc, format_tax_rate, format_cost


DARK_RED = 0x8B0000
CRIMSON = 0xB22222
GOLD = 0xFFD700
VOID_BLACK = 0x0A0A0A
BLOOD_RED = 0x6B0000
DEEP_PURPLE = 0x2C0040

SEP = "━━━━━━━━━━━━━━━━━━━━━━━━"

WEALTH_QUOTES = [
    "The Abyss grows heavier in your favor.",
    "The Kingdom acknowledges your holdings.",
    "Wealth is power. Power is survival.",
    "Your coffers speak louder than your rank.",
    "The Treasury watches. Always.",
    "Every coin forged in suffering has a price.",
    "The scales do not lie. Neither does your balance.",
]

OUTCOME_COLORS = {
    "failure": VOID_BLACK,
    "meager": DARK_RED,
    "common": CRIMSON,
    "rich": 0xCC4400,
    "jackpot": GOLD,
}

OUTCOME_FLAVOR = {
    "failure": "The rock yields nothing. Darkness consumes your effort.",
    "meager": "The veins run thin. Scant wages for the descent.",
    "common": "The mines yield their reward. Another day in the deep.",
    "rich": "A rich vein is struck. The haul is considerable.",
    "jackpot": "The abyss tears open. Wealth beyond measure flows forth.",
}


class EmbedFactory:

    # ─── Identity ────────────────────────────────────────────

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
        risk_score = user_data.get("risk_score", 0)
        username = user_data.get("username", "Unknown")
        display = mention if mention else f"**{username}**"

        embed = discord.Embed(
            title="👑  Kingdom Identity Card",
            description=display,
            color=BLOOD_RED,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="Rank", value=f"**{rank}**", inline=True)
        embed.add_field(name="Title", value=f"*{title}*", inline=True)
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="💰  Wealth",
            value=f"**{format_dc(balance)}**\nKingdom Rank: **#{kingdom_rank}**",
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="📊  Stats",
            value=f"Taxes Paid: **{format_dc(taxes_paid)}**",
            inline=True,
        )
        if risk_score > 0:
            embed.add_field(
                name="⚠  Risk",
                value=f"**{risk_score}/100**",
                inline=True,
            )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.set_footer(text='"The Abyss remembers your name."  ·  Kingdom Treasury')
        return embed

    # ─── Wealth ──────────────────────────────────────────────

    @staticmethod
    def wealth(user_data: dict) -> discord.Embed:
        balance = user_data.get("balance", 0)
        quote = random.choice(WEALTH_QUOTES)
        embed = discord.Embed(
            description=f"💰  You possess **{format_dc(balance)}**\n*\"{quote}\"*",
            color=DARK_RED,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Vault ───────────────────────────────────────────────

    @staticmethod
    def vault(treasury_balance: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏦  Kingdom Treasury",
            description="*The central reserve. Absolute. Untouchable.*",
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

    # ─── Grind ───────────────────────────────────────────────

    @staticmethod
    def grind_result(result: dict) -> discord.Embed:
        outcome_label = result.get("outcome_label", "common")
        gross = result["gross"]
        effective_tax_rate = result["effective_tax_rate"]
        tax_amount = result["tax_amount"]
        net = result["net"]
        new_balance = result["new_balance"]
        flat_bonus = result.get("flat_bonus", 0)

        flavor = OUTCOME_FLAVOR.get(outcome_label, OUTCOME_FLAVOR["common"])
        color = OUTCOME_COLORS.get(outcome_label, CRIMSON)

        if outcome_label == "failure":
            embed = discord.Embed(
                title="⛏️  Infernal Mines",
                description=f"*{flavor}*",
                color=color,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        embed = discord.Embed(
            title="⛏️  Infernal Mines",
            description=f"*{flavor}*",
            color=color,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        bonus_line = f"\nBonus  +{format_dc(flat_bonus):>15}" if flat_bonus else ""
        tax_label = f"Tax-Free" if effective_tax_rate == 0 else f"{format_tax_rate(effective_tax_rate)}"
        tax_line = f"\nTax    -{format_dc(tax_amount):>15}  ({tax_label})" if tax_amount > 0 else "\nTax     Exempt"

        embed.add_field(
            name="EXTRACTION",
            value=(
                f"```"
                f"Raw    +{format_dc(gross - flat_bonus):>15}{bonus_line}{tax_line}\n"
                f"Net    +{format_dc(net):>15}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text='"The Kingdom takes its share."  ·  Kingdom Treasury')
        return embed

    # ─── Tribute ─────────────────────────────────────────────

    @staticmethod
    def tribute_result(result: dict) -> discord.Embed:
        gross = result["gross"]
        bonus = result["bonus"]
        tax_amount = result["tax_amount"]
        tax_rate = result["tax_rate"]
        net = result["net"]
        new_balance = result["new_balance"]
        base = gross - bonus

        embed = discord.Embed(
            title="🩸  Royal Tribute",
            description="*The realm renders its offering. Your loyalty is recorded in the Kingdom's ledger.*",
            color=CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        bonus_line = f"\nBonus  +{format_dc(bonus):>15}  (grind ×5)" if bonus > 0 else ""
        embed.add_field(
            name="TRIBUTE LEDGER",
            value=(
                f"```"
                f"Base   +{format_dc(base):>15}{bonus_line}\n"
                f"Tax    -{format_dc(tax_amount):>15}  ({format_tax_rate(tax_rate)})\n"
                f"Net    +{format_dc(net):>15}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Transfer ────────────────────────────────────────────

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
                f"Levy     -{format_dc(tax):>12}  (2%)\n"
                f"Received +{format_dc(net):>12}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="YOUR BALANCE", value=f"**{format_dc(sender_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Ascend ──────────────────────────────────────────────

    @staticmethod
    def ascend_confirm(rank_name: str, cost: int, current_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned = cost - treasury_cut
        remaining = current_balance - cost
        embed = discord.Embed(
            title="👑  Ascension Ritual",
            description=(
                f"*You seek to claim the rank of **{rank_name}**.*\n"
                f"*This transaction is irreversible. The Kingdom does not offer refunds.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="PAYMENT BREAKDOWN",
            value=(
                f"```"
                f"Cost       {format_dc(cost):>12}\n"
                f"Treasury  +{format_dc(treasury_cut):>11}  (10%)\n"
                f"Burned     {format_dc(burned):>12}  (90%)\n"
                f"Remaining  {format_dc(remaining):>12}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.set_footer(text="This action expires in 45 seconds  ·  Kingdom Treasury")
        return embed

    @staticmethod
    def ascend_success(rank_name: str, cost: int, new_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned = cost - treasury_cut
        embed = discord.Embed(
            title="👑  Ascension",
            description="*Your ascension is recorded. The title is sealed into the Kingdom's ledger.*",
            color=GOLD,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="NEW RANK", value=f"**{rank_name}**", inline=False)
        embed.add_field(
            name="PAYMENT",
            value=(
                f"```"
                f"Cost       {format_dc(cost):>12}\n"
                f"Treasury  +{format_dc(treasury_cut):>11}  (10%)\n"
                f"Burned     {format_dc(burned):>12}  (90%)"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="REMAINING BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Market ──────────────────────────────────────────────

    @staticmethod
    def market_page(ranks: list, page: int, total_pages: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏪  Kingdom Market",
            description=(
                "*Ascend. Compete. Dominate.*\n"
                "*Each rank must be purchased in sequence — no skipping.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for name, cost, tax_rate in ranks:
            embed.add_field(
                name=f"**{name}**",
                value=f"Cost: **{format_cost(cost)}**\nTax: {format_tax_rate(tax_rate)}",
                inline=True,
            )
        embed.set_footer(
            text=f"Page {page}/{total_pages}  ·  /ascend <rank>  ·  Kingdom Treasury"
        )
        return embed

    # ─── Black Market ────────────────────────────────────────

    @staticmethod
    def blackmarket_page(
        items: List[Dict[str, Any]], page: int, total_pages: int
    ) -> discord.Embed:
        embed = discord.Embed(
            title="🕵️  Black Market",
            description=(
                "*Items of forbidden provenance. The Kingdom does not sanction these transactions.*\n"
                "*Each purchase may increase your risk score. Cerberus watches.*"
            ),
            color=DEEP_PURPLE,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for item in items:
            risk_str = f"+{item['risk_increase']} Risk" if item["risk_increase"] > 0 else "No Risk"
            embed.add_field(
                name=f"**{item['name']}** — {format_dc(item['cost'])}",
                value=f"{item['description']}\n*{risk_str}*",
                inline=False,
            )
        embed.set_footer(
            text=f"Page {page}/{total_pages}  ·  Rotates every 6 hours  ·  Kingdom Treasury"
        )
        return embed

    @staticmethod
    def blackmarket_purchase(item: dict, cost: int, new_balance: int, new_risk: int) -> discord.Embed:
        embed = discord.Embed(
            title="🕵️  Transaction Complete",
            description=f"*The item is yours. No record will be found... in the official ledger.*",
            color=DEEP_PURPLE,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="ITEM", value=f"**{item['name']}**", inline=True)
        embed.add_field(name="COST", value=format_dc(cost), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="EFFECT", value=item["description"], inline=False)
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=True)
        embed.add_field(name="RISK SCORE", value=f"**{new_risk}/100**", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Cerberus Audit ──────────────────────────────────────

    @staticmethod
    def cerberus_cleared(risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐺  Cerberus Audit",
            description=(
                "*The hound circles. It sniffs. It finds nothing.*\n"
                "*You are cleared. This time.*"
            ),
            color=VOID_BLACK,
        )
        embed.add_field(name="OUTCOME", value="**Cleared**", inline=True)
        embed.add_field(name="RISK DELTA", value=f"{risk_delta:+d}", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def cerberus_penalty(penalty: int, penalty_pct: float, risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐺  Cerberus Audit",
            description=(
                "*The hound finds guilt. The Kingdom collects what is owed.*\n"
                "*Resistance is futile.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="OUTCOME", value="**Penalized**", inline=True)
        embed.add_field(
            name="PENALTY",
            value=f"**-{format_dc(penalty)}** ({int(penalty_pct * 100)}%)",
            inline=True,
        )
        embed.add_field(name="RISK DELTA", value=f"{risk_delta:+d}", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def cerberus_immune() -> discord.Embed:
        embed = discord.Embed(
            title="🐺  Cerberus Audit",
            description=(
                "*The hound circles. Your cloak holds.*\n"
                "*Cerberus finds nothing to pursue. For now.*"
            ),
            color=DEEP_PURPLE,
        )
        embed.add_field(name="OUTCOME", value="**Immune** *(Shadow Cloak consumed)*", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Investments ─────────────────────────────────────────

    @staticmethod
    def investment_opened(result: dict) -> discord.Embed:
        from datetime import timezone
        matures_at = result["matures_at"]
        unix_ts = int(matures_at.timestamp())
        embed = discord.Embed(
            title="📈  Investment Opened",
            description="*Your DevilCoins are committed. The Kingdom will render its judgment in time.*",
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="TYPE", value=f"**{result['label']}**", inline=True)
        embed.add_field(name="PRINCIPAL", value=format_dc(result["amount"]), inline=True)
        embed.add_field(name="MATURES", value=f"<t:{unix_ts}:R>", inline=True)
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="REMAINING BALANCE", value=f"**{format_dc(result['new_balance'])}**", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def portfolio(investments: list) -> discord.Embed:
        if not investments:
            embed = discord.Embed(
                description="*Your portfolio is empty. No capital at work.*",
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        embed = discord.Embed(
            title="📊  Investment Portfolio",
            description="*Active positions in the infernal markets.*",
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for inv in investments:
            matures_at_dt = inv["matures_at_dt"]
            unix_ts = int(matures_at_dt.timestamp())
            status = "✅ **Ready to collect**" if inv["matured"] else f"<t:{unix_ts}:R>"
            embed.add_field(
                name=f"#{inv['id']} — {inv['inv_type'].title()}",
                value=f"Principal: **{format_dc(inv['principal'])}**\nMatures: {status}",
                inline=True,
            )
        embed.set_footer(
            text="Use /collect to claim matured investments  ·  Kingdom Treasury"
        )
        return embed

    @staticmethod
    def investment_collected(result: dict) -> discord.Embed:
        results = result["results"]
        total_payout = result["total_payout"]
        new_balance = result["new_balance"]

        embed = discord.Embed(
            title="📈  Investments Settled",
            description="*The Kingdom renders its verdict.*",
            color=GOLD if all(r["success"] for r in results) else CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for r in results:
            profit_str = f"+{format_dc(r['profit'])}" if r["profit"] >= 0 else f"-{format_dc(abs(r['profit']))}"
            outcome = "**Profit**" if r["success"] else "**Loss**"
            embed.add_field(
                name=f"#{r['id']} — {r['inv_type'].title()}  {outcome}",
                value=(
                    f"Principal: {format_dc(r['principal'])}\n"
                    f"Payout: **{format_dc(r['payout'])}** ({profit_str})"
                ),
                inline=True,
            )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="TOTAL RECEIVED", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def investment_withdrawn(result: dict) -> discord.Embed:
        new_balance = result["new_balance"]
        total_payout = result["total_payout"]
        embed = discord.Embed(
            title="📉  Early Withdrawal",
            description=(
                "*The Kingdom does not reward impatience.*\n"
                "*A 20% penalty has been exacted on all withdrawn positions.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        for r in result["results"]:
            embed.add_field(
                name=f"#{r['id']} — {r['inv_type'].title()}",
                value=(
                    f"Principal: {format_dc(r['principal'])}\n"
                    f"Received: **{format_dc(r['payout'])}**  (Penalty: -{format_dc(r['penalty'])})"
                ),
                inline=True,
            )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="TOTAL RECEIVED", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="BALANCE", value=f"**{format_dc(new_balance)}**", inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Shared error / cooldown ──────────────────────────────

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
        embed = discord.Embed(description=f"*{message}*", color=VOID_BLACK)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed
