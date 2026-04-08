"""
Kingdom Treasury — Embed Factory
All embeds follow the dark-fantasy infernal aesthetic.
Palette, separators, and tone are locked to the identity card as gold standard.
"""

import discord
import random
from typing import Optional, List, Dict, Any
from .formatting import format_dc, format_tax_rate, format_cost


# ── Palette ───────────────────────────────────────────────────────────────────
VOID_BLACK   = 0x0A0A0A
IRON         = 0x1C1C1C
BLOOD_RED    = 0x6B0000
DARK_RED     = 0x8B0000
CRIMSON      = 0xB22222
DEEP_CRIMSON = 0x4A0000
GOLD         = 0xFFD700
AMBER        = 0xCC7700
DEEP_PURPLE  = 0x1A0030
VOID_PURPLE  = 0x2C0040

# ── Separators ────────────────────────────────────────────────────────────────
SEP      = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEP_THIN = "─────────────────────────────────"
SEP_GOLD = "✦ ─────────────────────────── ✦"

# ── Grind outcome data ────────────────────────────────────────────────────────
OUTCOME_COLORS = {
    "failure": VOID_BLACK,
    "meager":  DARK_RED,
    "common":  CRIMSON,
    "rich":    AMBER,
    "jackpot": GOLD,
}

OUTCOME_ICONS = {
    "failure": "🪨",
    "meager":  "⛏",
    "common":  "⛏",
    "rich":    "💰",
    "jackpot": "✦",
}

OUTCOME_TITLES = {
    "failure": "The rock gives nothing.",
    "meager":  "The veins run thin.",
    "common":  "The mines render their due.",
    "rich":    "A rich vein is struck.",
    "jackpot": "The Abyss tears open.",
}

OUTCOME_FLAVOR = {
    "failure": "Darkness consumes your effort. Return when the stone is ready.",
    "meager":  "Scant wages for the descent. The deep is not always generous.",
    "common":  "The stone yields to your hand. Another session in the dark.",
    "rich":    "The haul is considerable. The Kingdom's cut has been taken.",
    "jackpot": "Wealth beyond measure flows forth. The ledger is changed.",
}

# ── Wealth quotes ─────────────────────────────────────────────────────────────
WEALTH_QUOTES = [
    "The Abyss grows heavier in your favor.",
    "The Kingdom acknowledges your holdings.",
    "Wealth is power. Power is survival.",
    "Your coffers speak louder than your rank.",
    "The Treasury watches. Always.",
    "Every coin forged in suffering has a price.",
    "The scales do not lie. Neither does your balance.",
    "DevilCoins do not sleep. Neither should you.",
    "The kingdom is built one soul at a time.",
]


class EmbedFactory:

    # ─── Identity (embed fallback, card image is primary) ─────────────────────

    @staticmethod
    def identity(
        user_data: dict,
        kingdom_rank: int,
        avatar_url: Optional[str] = None,
        mention: Optional[str] = None,
    ) -> discord.Embed:
        from .skins import get_skin
        from ..services.rank_service import RANK_DICT

        rank       = user_data.get("rank", "Forsaken")
        balance    = user_data.get("balance", 0)
        taxes_paid = user_data.get("taxes_paid", 0)
        risk_score = user_data.get("risk_score", 0)
        username   = user_data.get("username", "Unknown")
        skin_id    = user_data.get("equipped_skin") or "default"
        title      = user_data.get("equipped_title") or "Unmarked"

        skin = get_skin(skin_id)
        rank_entry = RANK_DICT.get(rank, {})
        tax_rate   = rank_entry.get("tax_rate", 0.12)
        tax_display = f"{int(tax_rate * 100)}%" if tax_rate > 0 else "Exempt"

        display = mention if mention else f"**{username}**"
        decorated_rank = f"{skin.rank_prefix}{rank}{skin.rank_suffix}"

        embed = discord.Embed(
            title=skin.title_banner,
            description=f"{display}\n{skin.title_prefix}*{title}*",
            color=skin.color,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="\u200b", value=skin.separator, inline=False)
        embed.add_field(name="⚔  RANK",         value=f"**{decorated_rank}**", inline=True)
        embed.add_field(name="📊  TAX BRACKET", value=f"**{tax_display}**",    inline=True)
        embed.add_field(name="\u200b",           value="\u200b",               inline=True)
        embed.add_field(name="\u200b", value=skin.separator, inline=False)
        embed.add_field(name=f"{skin.wealth_prefix}  COFFERS", value=f"**{format_dc(balance)}**", inline=True)
        embed.add_field(name="🏆  KINGDOM RANK",               value=f"**#{kingdom_rank}**",       inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="\u200b", value=skin.separator, inline=False)
        risk_line = f"\nRisk Score      {risk_score:>4}/100" if risk_score > 0 else ""
        embed.add_field(
            name=f"{skin.stat_icon}  RECORD",
            value=(
                f"```"
                f"Taxes Filed     {format_dc(taxes_paid):>14}"
                f"{risk_line}\n"
                f"Card Skin       {skin.name:>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=skin.separator, inline=False)
        embed.set_footer(text=f"{skin.footer_flavor}  ·  Kingdom Treasury")
        return embed

    # ─── Wealth ───────────────────────────────────────────────────────────────

    @staticmethod
    def wealth(user_data: dict) -> discord.Embed:
        balance = user_data.get("balance", 0)
        rank    = user_data.get("rank", "Forsaken")
        quote   = random.choice(WEALTH_QUOTES)
        embed = discord.Embed(
            title="💰  Kingdom Coffers",
            description=f"*\"{quote}\"*",
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(balance)}**", inline=True)
        embed.add_field(name="RANK",    value=f"**{rank}**",               inline=True)
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Vault ────────────────────────────────────────────────────────────────

    @staticmethod
    def vault(treasury_balance: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏦  Kingdom Treasury — Central Vault",
            description=(
                "*The lifeblood of the Kingdom. All wealth flows through here.*\n"
                "*The reserves are absolute. No withdrawal is authorized.*"
            ),
            color=GOLD,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.add_field(
            name="TOTAL RESERVES",
            value=f"## {format_dc(treasury_balance)}",
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.set_footer(text='"All wealth serves the Kingdom."  ·  Kingdom Treasury')
        return embed

    # ─── Grind ────────────────────────────────────────────────────────────────

    @staticmethod
    def grind_result(result: dict) -> discord.Embed:
        outcome   = result.get("outcome_label", "common")
        gross     = result["gross"]
        eff_rate  = result["effective_tax_rate"]
        tax       = result["tax_amount"]
        net       = result["net"]
        balance   = result["new_balance"]
        flat_bonus = result.get("flat_bonus", 0)

        icon  = OUTCOME_ICONS.get(outcome, "⛏")
        color = OUTCOME_COLORS.get(outcome, CRIMSON)
        title = OUTCOME_TITLES.get(outcome, OUTCOME_TITLES["common"])
        flavor = OUTCOME_FLAVOR.get(outcome, OUTCOME_FLAVOR["common"])

        embed = discord.Embed(
            title=f"{icon}  Infernal Mines — {title}",
            description=f"*{flavor}*",
            color=color,
        )

        if outcome == "failure":
            embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
            embed.add_field(
                name="BALANCE",
                value=f"**{format_dc(balance)}**",
                inline=True,
            )
            embed.set_footer(text='"The Kingdom does not reward failure."  ·  Kingdom Treasury')
            return embed

        embed.add_field(name="\u200b", value=SEP, inline=False)

        # Ledger block
        bonus_line  = f"\nBonus    +{format_dc(flat_bonus):>14}" if flat_bonus else ""
        tax_label   = "Exempt" if eff_rate == 0 else format_tax_rate(eff_rate)
        tax_line    = f"\nTax      -{format_dc(tax):>14}  ({tax_label})" if tax > 0 else "\nTax       Exempt"

        embed.add_field(
            name="⛏  EXTRACTION LEDGER",
            value=(
                f"```"
                f"Raw      +{format_dc(gross - flat_bonus):>14}"
                f"{bonus_line}"
                f"{tax_line}\n"
                f"{'─' * 33}\n"
                f"Net      +{format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )

        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(balance)}**", inline=True)

        if outcome == "jackpot":
            embed.add_field(name="OUTCOME", value="✦  **JACKPOT**", inline=True)
            embed.set_footer(text='"The Abyss opens its veins for the worthy."  ·  Kingdom Treasury')
        elif outcome == "rich":
            embed.set_footer(text='"A good day in the deep."  ·  Kingdom Treasury')
        else:
            embed.set_footer(text='"The Kingdom takes its share."  ·  Kingdom Treasury')

        return embed

    # ─── Tribute ──────────────────────────────────────────────────────────────

    @staticmethod
    def tribute_result(result: dict) -> discord.Embed:
        gross    = result["gross"]
        bonus    = result["bonus"]
        tax      = result["tax_amount"]
        tax_rate = result["tax_rate"]
        net      = result["net"]
        balance  = result["new_balance"]
        base     = gross - bonus

        embed = discord.Embed(
            title="🩸  Royal Tribute — The Kingdom Renders Its Due",
            description=(
                "*The realm acknowledges your presence.*\n"
                "*Your loyalty is recorded in the Kingdom's eternal ledger.*"
            ),
            color=CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        bonus_line = f"\nBonus    +{format_dc(bonus):>14}  (active grind streak)" if bonus > 0 else ""
        embed.add_field(
            name="🩸  TRIBUTE LEDGER",
            value=(
                f"```"
                f"Base     +{format_dc(base):>14}"
                f"{bonus_line}\n"
                f"Tax      -{format_dc(tax):>14}  ({format_tax_rate(tax_rate)})\n"
                f"{'─' * 33}\n"
                f"Net      +{format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="BALANCE", value=f"**{format_dc(balance)}**", inline=False)
        embed.set_footer(text='"The Kingdom has taken notice."  ·  Kingdom Treasury')
        return embed

    # ─── Transfer ─────────────────────────────────────────────────────────────

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
            title="💸  Wealth Transfer — Transaction Sealed",
            description=(
                "*The exchange is complete. The Treasury has recorded its levy.*\n"
                "*Wealth moves under the Kingdom's gaze.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(
            name="📋  TRANSACTION RECORD",
            value=(
                f"```"
                f"From      {sender_name}\n"
                f"To        {recipient_name}\n"
                f"{'─' * 33}\n"
                f"Sent     +{format_dc(amount):>14}\n"
                f"Levy     -{format_dc(tax):>14}  (2% transfer tax)\n"
                f"{'─' * 33}\n"
                f"Received +{format_dc(net):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="YOUR BALANCE", value=f"**{format_dc(sender_balance)}**", inline=False)
        embed.set_footer(text='"No transaction escapes the Kingdom ledger."  ·  Kingdom Treasury')
        return embed

    # ─── Ascend ───────────────────────────────────────────────────────────────

    @staticmethod
    def ascend_confirm(rank_name: str, cost: int, current_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned       = cost - treasury_cut
        remaining    = current_balance - cost
        embed = discord.Embed(
            title="👑  Ascension Ritual — Awaiting Confirmation",
            description=(
                f"*You seek to claim the rank of **{rank_name}**.*\n"
                f"*The ritual is irreversible. The Kingdom does not grant refunds.*\n"
                f"*Confirm your will — or step away.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.add_field(
            name="👑  PAYMENT BREAKDOWN",
            value=(
                f"```"
                f"Target Rank    {rank_name}\n"
                f"{'─' * 33}\n"
                f"Total Cost     {format_dc(cost):>14}\n"
                f"Treasury Cut  +{format_dc(treasury_cut):>13}  (10%)\n"
                f"Burned         {format_dc(burned):>14}  (90%)\n"
                f"{'─' * 33}\n"
                f"After          {format_dc(remaining):>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.set_footer(text="This ritual expires in 45 seconds  ·  Kingdom Treasury")
        return embed

    @staticmethod
    def ascend_success(rank_name: str, cost: int, new_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned       = cost - treasury_cut
        embed = discord.Embed(
            title="👑  Ascension Complete",
            description=(
                f"*The rank of **{rank_name}** is now yours.*\n"
                f"*Your ascension is sealed into the Kingdom's ledger for eternity.*"
            ),
            color=GOLD,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.add_field(name="NEW RANK", value=f"## {rank_name}", inline=False)
        embed.add_field(
            name="💸  PAYMENT RECORD",
            value=(
                f"```"
                f"Total Cost     {format_dc(cost):>14}\n"
                f"Treasury Cut  +{format_dc(treasury_cut):>13}  (10%)\n"
                f"Burned         {format_dc(burned):>14}  (90%)"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="REMAINING BALANCE", value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text='"The Kingdom grows stronger with every ascension."  ·  Kingdom Treasury')
        return embed

    # ─── Market ───────────────────────────────────────────────────────────────

    @staticmethod
    def market_page(ranks: list, page: int, total_pages: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏪  Kingdom Market — Ascension Registry",
            description=(
                "*The path upward is forged in DevilCoins.*\n"
                "*Ranks must be purchased in sequence. There is no skipping the climb.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)

        RANK_DESCRIPTIONS = {
            "Vermin":      "The first step above nothing. The Kingdom has your name now.",
            "Corrupted":   "Tainted by ambition. The hierarchy takes notice.",
            "Mythology":   "Your existence becomes legend. The lower ranks defer.",
            "Folklore":    "Spoken of in the dark halls. A name with weight.",
            "Eschatology": "You study the end of things. Power through knowledge.",
            "Demonology":  "The language of demons is your native tongue now.",
            "Archangel":   "Between the sacred and the infernal. A rare position.",
            "Archdemon":   "The void bows. The Kingdom watches closely.",
            "Knight":      "Honor through force. The noble class begins here.",
            "Baron":       "Land and blood. A title that carries history.",
            "Viscount":    "The court acknowledges you by name.",
            "Count":       "Your decisions carry weight beyond your own walls.",
            "Marquis":     "Between Baron and Duke — a rank of quiet authority.",
            "Duke":        "The upper echelon. The throne is within reach.",
            "Chancellor":  "Absolute command. The Kingdom is your instrument.",
        }

        for name, cost, tax_rate in ranks:
            desc = RANK_DESCRIPTIONS.get(name, "A rank of the Kingdom hierarchy.")
            tax_str = f"{int(tax_rate * 100)}%" if tax_rate > 0 else "**Exempt**"
            embed.add_field(
                name=f"**{name}**",
                value=(
                    f"*{desc}*\n"
                    f"```"
                    f"Cost   {format_cost(cost):>18}\n"
                    f"Tax    {tax_str:>18}"
                    f"```"
                    f"Use `/ascend {name}` to claim this rank."
                ),
                inline=False,
            )

        embed.add_field(name="\u200b", value=SEP_GOLD, inline=False)
        embed.set_footer(
            text=f"Page {page} of {total_pages}  ·  Use /ascend <rank> to purchase  ·  Kingdom Treasury"
        )
        return embed

    # ─── Black Market ─────────────────────────────────────────────────────────

    @staticmethod
    def blackmarket_page(
        items: List[Dict[str, Any]], page: int, total_pages: int
    ) -> discord.Embed:
        RISK_TIERS = {
            0:  ("—",  "No risk change"),
            5:  ("🟡", "Low heat"),
            10: ("🟡", "Low heat"),
            15: ("🟠", "Moderate heat"),
            20: ("🟠", "Moderate heat"),
            25: ("🟠", "Elevated heat"),
            30: ("🔴", "High heat"),
            35: ("🔴", "High heat"),
        }

        embed = discord.Embed(
            title="🕵️  Black Market — Forbidden Acquisitions",
            description=(
                "*Items of questionable provenance. The Kingdom does not sanction these transactions.*\n"
                "*Every deal leaves a trace. Cerberus is always watching.*"
            ),
            color=DEEP_PURPLE,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        for item in items:
            ri = item.get("risk_increase", 0)
            rr = item.get("risk_reduce", 0)
            if ri > 0:
                t = RISK_TIERS.get(ri, ("🔴", f"+{ri} Risk"))
                risk_line = f"{t[0]}  **+{ri} Risk** *(exposure: {t[1]})*"
            elif rr > 0:
                risk_line = f"🟢  **−{rr} Risk** *(exposure reduced)*"
            else:
                risk_line = "⬜  **No risk change**"

            embed.add_field(
                name=f"**{item['name']}** — {format_dc(item['cost'])}",
                value=(
                    f"*{item['description']}*\n"
                    f"{risk_line}"
                ),
                inline=False,
            )
            embed.add_field(name="\u200b", value=SEP_THIN, inline=False)

        embed.set_footer(
            text=f"Page {page} of {total_pages}  ·  Inventory rotates every 6 hours  ·  Kingdom Treasury"
        )
        return embed

    @staticmethod
    def blackmarket_purchase(
        item: dict,
        cost: int,
        new_balance: int,
        old_risk: int,
        new_risk: int,
        risk_delta: int,
    ) -> discord.Embed:
        def _tier(r: int):
            if r <= 20:   return ("LOW",      "🟢", VOID_BLACK)
            elif r <= 50: return ("MEDIUM",   "🟡", 0x4A3800)
            elif r <= 80: return ("HIGH",     "🟠", 0x6B2800)
            else:         return ("CRITICAL", "🔴", DARK_RED)

        old_label, old_icon, _  = _tier(old_risk)
        new_label, new_icon, ec = _tier(new_risk)

        CERBERUS_LINES = {
            "LOW":      "*The transaction is sealed. No trace remains in the official record.*",
            "MEDIUM":   "*The market remembers every soul. Cerberus has taken notice.*",
            "HIGH":     "*The hound stirs in its kennel. Your record grows suspicious.*",
            "CRITICAL": "*Cerberus is fully awake. Every move you make is catalogued.*",
        }

        embed = discord.Embed(
            title="🕵️  Black Market — Transaction Sealed",
            description=CERBERUS_LINES[new_label],
            color=ec,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        embed.add_field(name="ITEM ACQUIRED", value=f"**{item['name']}**",   inline=True)
        embed.add_field(name="COST",          value=f"**{format_dc(cost)}**", inline=True)
        embed.add_field(name="\u200b",        value="\u200b",                 inline=True)
        embed.add_field(name="EFFECT", value=f"*{item['description']}*", inline=False)
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)

        if risk_delta > 0:
            delta_str   = f"+{risk_delta} (exposure increased)"
            tier_change = (
                f"{old_icon} {old_label}  →  {new_icon} {new_label}"
                if new_label != old_label else f"{new_icon} {new_label}"
            )
        elif risk_delta < 0:
            delta_str   = f"{risk_delta} (exposure reduced)"
            tier_change = (
                f"{old_icon} {old_label}  →  {new_icon} {new_label}"
                if new_label != old_label else f"{new_icon} {new_label}"
            )
        else:
            delta_str   = "No change"
            tier_change = f"{new_icon} {new_label}"

        embed.add_field(
            name="📋  RISK RECORD",
            value=(
                f"```"
                f"Before    {old_risk:>4} / 100\n"
                f"Delta     {delta_str}\n"
                f"After     {new_risk:>4} / 100"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name="RISK STATUS", value=f"**{tier_change}**",        inline=True)
        embed.add_field(name="BALANCE",     value=f"**{format_dc(new_balance)}**", inline=True)
        embed.add_field(name="\u200b", value=SEP, inline=False)

        FOOTER = {
            "LOW":      "No immediate threat detected.",
            "MEDIUM":   "Cerberus is aware of your presence.",
            "HIGH":     "Cerberus is watching. Check /identity for your current record.",
            "CRITICAL": "Immediate audit risk. The Kingdom is closing in.",
        }
        embed.set_footer(text=f"{FOOTER[new_label]}  ·  Kingdom Treasury")
        return embed

    # ─── Cerberus Audit ───────────────────────────────────────────────────────

    @staticmethod
    def cerberus_cleared(risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Record Cleared",
            description=(
                "*The hound circles. It sniffs. It finds nothing of value.*\n"
                "*You are cleared. Your record is updated. This time.*"
            ),
            color=VOID_BLACK,
        )
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="OUTCOME",    value="✅  **Cleared**",        inline=True)
        embed.add_field(name="RISK DELTA", value=f"`{risk_delta:+d}`",     inline=True)
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.set_footer(text='"The hound remembers even when it does not act."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def cerberus_penalty(penalty: int, penalty_pct: float, risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Penalty Exacted",
            description=(
                "*The hound has found its quarry. The Kingdom collects what is owed.*\n"
                "*Resistance is not an option. Compliance is the only path forward.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="OUTCOME",    value="⚠️  **Penalized**",                              inline=True)
        embed.add_field(name="SEIZED",     value=f"**−{format_dc(penalty)}** `({int(penalty_pct * 100)}%)`", inline=True)
        embed.add_field(name="RISK DELTA", value=f"`{risk_delta:+d}`",                            inline=True)
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.set_footer(text='"Cerberus does not forget. Neither does the ledger."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def cerberus_immune() -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Shadow Cloak Active",
            description=(
                "*The hound circles. Your cloak absorbs the scent.*\n"
                "*Cerberus finds nothing to pursue. The Shadow Cloak is consumed.*"
            ),
            color=VOID_PURPLE,
        )
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="OUTCOME", value="🌑  **Immune** *(Shadow Cloak consumed)*", inline=False)
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.set_footer(text='"The void protects — but only once."  ·  Kingdom Treasury')
        return embed

    # ─── Investments ──────────────────────────────────────────────────────────

    @staticmethod
    def investment_opened(result: dict) -> discord.Embed:
        matures_at = result["matures_at"]
        unix_ts    = int(matures_at.timestamp())
        embed = discord.Embed(
            title="📈  Investment Position Opened",
            description=(
                "*Your DevilCoins are deployed. The infernal markets will render judgment.*\n"
                "*Patience is the only strategy that works in the dark.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)
        embed.add_field(name="TYPE",      value=f"**{result['label']}**",        inline=True)
        embed.add_field(name="PRINCIPAL", value=format_dc(result["amount"]),     inline=True)
        embed.add_field(name="MATURES",   value=f"<t:{unix_ts}:R>",             inline=True)
        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="REMAINING BALANCE", value=f"**{format_dc(result['new_balance'])}**", inline=False)
        embed.set_footer(text='"Capital deployed. The Kingdom watches it grow."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def portfolio(investments: list) -> discord.Embed:
        if not investments:
            embed = discord.Embed(
                title="📊  Investment Portfolio — No Active Positions",
                description=(
                    "*Your portfolio is empty. No capital is at work.*\n"
                    "*Use `/invest` to open a position in the infernal markets.*"
                ),
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        any_ready = any(inv["matured"] for inv in investments)
        embed = discord.Embed(
            title="📊  Investment Portfolio — Active Positions",
            description=(
                "*Capital deployed across the infernal markets.*\n"
                + ("*Some positions are ready for collection.*" if any_ready else
                   "*All positions are still maturing.*")
            ),
            color=GOLD if any_ready else DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        for inv in investments:
            dt      = inv["matures_at_dt"]
            unix_ts = int(dt.timestamp())
            matured = inv["matured"]
            status  = "✅  **READY TO COLLECT**" if matured else f"⏳  Matures <t:{unix_ts}:R>"
            embed.add_field(
                name=f"**#{inv['id']}** — {inv['inv_type'].replace('_', ' ').title()}",
                value=(
                    f"Principal: **{format_dc(inv['principal'])}**\n"
                    f"{status}"
                ),
                inline=True,
            )

        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.set_footer(text="Use /collect to claim matured positions  ·  Kingdom Treasury")
        return embed

    @staticmethod
    def investment_collected(result: dict) -> discord.Embed:
        results       = result["results"]
        total_payout  = result["total_payout"]
        new_balance   = result["new_balance"]
        all_profit    = all(r["success"] for r in results)

        embed = discord.Embed(
            title="📈  Investments Settled — The Kingdom Renders Its Verdict",
            description=(
                "*Your positions have been closed. The ledger is updated.*"
            ),
            color=GOLD if all_profit else CRIMSON,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        for r in results:
            profit_sign = "+" if r["profit"] >= 0 else "−"
            profit_abs  = abs(r["profit"])
            outcome_str = "✅  Profit" if r["success"] else "📉  Loss"
            embed.add_field(
                name=f"**#{r['id']}** — {r['inv_type'].replace('_', ' ').title()}  ·  {outcome_str}",
                value=(
                    f"```"
                    f"Principal  {format_dc(r['principal']):>16}\n"
                    f"Payout     {format_dc(r['payout']):>16}\n"
                    f"P&L        {profit_sign}{format_dc(profit_abs):>15}"
                    f"```"
                ),
                inline=False,
            )

        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="TOTAL RECEIVED", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="BALANCE",        value=f"**{format_dc(new_balance)}**",  inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def investment_withdrawn(result: dict) -> discord.Embed:
        new_balance  = result["new_balance"]
        total_payout = result["total_payout"]
        embed = discord.Embed(
            title="📉  Early Withdrawal — Penalty Exacted",
            description=(
                "*The Kingdom does not reward impatience.*\n"
                "*A 20% penalty has been levied on all withdrawn positions.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name="\u200b", value=SEP, inline=False)

        for r in result["results"]:
            embed.add_field(
                name=f"**#{r['id']}** — {r['inv_type'].replace('_', ' ').title()}",
                value=(
                    f"```"
                    f"Principal  {format_dc(r['principal']):>16}\n"
                    f"Penalty   -{format_dc(r['penalty']):>15}\n"
                    f"Received   {format_dc(r['payout']):>16}"
                    f"```"
                ),
                inline=False,
            )

        embed.add_field(name="\u200b", value=SEP_THIN, inline=False)
        embed.add_field(name="TOTAL RECEIVED", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="BALANCE",        value=f"**{format_dc(new_balance)}**",  inline=True)
        embed.set_footer(text='"The Kingdom does not forget the impatient."  ·  Kingdom Treasury')
        return embed

    # ─── Error / Cooldown ─────────────────────────────────────────────────────

    @staticmethod
    def cooldown_error(action: str, remaining_str: str) -> discord.Embed:
        FLAVOR = {
            "grind":   "The mines have not recovered. The rock demands rest.",
            "tribute": "The realm has not forgotten your last offering. Wait.",
        }
        flavor = FLAVOR.get(action, "The Kingdom demands patience. Act when the time is right.")
        embed = discord.Embed(
            title="⏳  Not Yet",
            description=f"*{flavor}*",
            color=IRON,
        )
        embed.add_field(name="RETURN IN", value=f"```{remaining_str}```", inline=False)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def error(message: str) -> discord.Embed:
        embed = discord.Embed(
            title="⚠️  Kingdom System",
            description=f"*{message}*",
            color=VOID_BLACK,
        )
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed
