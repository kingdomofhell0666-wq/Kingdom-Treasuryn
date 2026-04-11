"""
Kingdom Treasury — Embed Factory
Dark fantasy system interface. Every command feels like
an action inside a living kingdom, not a Discord bot response.
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
GOLD         = 0xFFD700
AMBER        = 0xCC7700
DEEP_PURPLE  = 0x1A0030
VOID_PURPLE  = 0x2C0040

# ── Separators ────────────────────────────────────────────────────────────────
SEP      = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEP_THIN = "─────────────────────────────────"
SEP_GOLD = "✦ ─────────────────────────── ✦"
BLANK    = "\u200b"

# ── Outcome metadata ──────────────────────────────────────────────────────────
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

OUTCOME_FLAVOR = {
    "failure": "*The seam yields nothing. No reward is recorded.*",
    "meager":  "*The haul is thin. The veins ran sparse today.*",
    "common":  "*Standard extraction complete. The Kingdom takes its share.*",
    "rich":    "*A strong vein struck. The haul is well above standard.*",
    "jackpot": "*The Abyss tears open. Wealth beyond measure flows forth.*",
}

WEALTH_QUOTES = [
    "The ledger never lies.",
    "All wealth is recorded. Always.",
    "The Kingdom acknowledges your holdings.",
    "Power is measured in DevilCoins here.",
    "The Treasury watches every transaction.",
    "Wealth is the only language the Kingdom speaks.",
    "Every coin has a history. Yours is no exception.",
]


class EmbedFactory:

    # ─── Identity (embed fallback, image card is primary) ─────────────────────

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
        rank_entry  = RANK_DICT.get(rank, {})
        tax_rate    = rank_entry.get("tax_rate", 0.12)
        tax_display = f"{int(tax_rate * 100)}%" if tax_rate > 0 else "Exempt"
        display     = mention if mention else f"**{username}**"

        embed = discord.Embed(
            title=skin.title_banner,
            description=f"{display}\n{skin.title_prefix}*{title}*",
            color=skin.color,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name=BLANK, value=skin.separator, inline=False)
        embed.add_field(name="⚔  RANK",         value=f"**{skin.rank_prefix}{rank}{skin.rank_suffix}**", inline=True)
        embed.add_field(name="📊  TAX BRACKET", value=f"**{tax_display}**",                              inline=True)
        embed.add_field(name=BLANK,              value=BLANK,                                             inline=True)
        embed.add_field(name=BLANK, value=skin.separator, inline=False)
        embed.add_field(name=f"{skin.wealth_prefix}  COFFERS", value=f"**{format_dc(balance)}**", inline=True)
        embed.add_field(name="🏆  KINGDOM RANK",              value=f"**#{kingdom_rank}**",        inline=True)
        embed.add_field(name=BLANK, value=BLANK, inline=True)
        embed.add_field(name=BLANK, value=skin.separator, inline=False)

        risk_line = f"\nRisk Score      {risk_score:>4}/100" if risk_score > 0 else ""
        embed.add_field(
            name=f"{skin.stat_icon}  RECORD",
            value=(
                f"```"
                f"Taxes Filed  {taxes_paid:>14,}\n"
                f"{risk_line}\n"
                f"Card Skin       {skin.name:>14}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(name=BLANK, value=skin.separator, inline=False)
        embed.set_footer(text=f"{skin.footer_flavor}  ·  Kingdom Treasury")
        return embed

    # ─── Wealth ───────────────────────────────────────────────────────────────

    @staticmethod
    def wealth(user_data: dict) -> discord.Embed:
        balance = user_data.get("balance", 0)
        rank    = user_data.get("rank", "Forsaken")
        embed = discord.Embed(
            title="💰  Kingdom Coffers",
            description=f"*{random.choice(WEALTH_QUOTES)}*",
            color=DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)
        embed.add_field(
            name="💰  Balance",
            value=f"## {format_dc(balance)}",
            inline=False,
        )
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="⚔  Rank",  value=f"**{rank}**",  inline=True)
        embed.add_field(name=BLANK, value=BLANK, inline=True)
        embed.add_field(name=BLANK, value=BLANK, inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    # ─── Vault ────────────────────────────────────────────────────────────────

    @staticmethod
    def vault(treasury_balance: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏦  Kingdom Treasury",
            description="*All wealth flows through here. The reserve is absolute.*",
            color=GOLD,
        )
        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)
        embed.add_field(
            name="🏦  Total Reserves",
            value=f"## {format_dc(treasury_balance)}",
            inline=False,
        )
        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)
        embed.set_footer(text='"All wealth serves the Kingdom."  ·  Kingdom Treasury')
        return embed

    # ─── Grind ────────────────────────────────────────────────────────────────

    @staticmethod
    def grind_result(result: dict) -> discord.Embed:
        outcome    = result.get("outcome_label", "common")
        gross      = result["gross"]
        eff_rate   = result["effective_tax_rate"]
        tax        = result["tax_amount"]
        net        = result["net"]
        balance    = result["new_balance"]
        flat_bonus = result.get("flat_bonus", 0)

        icon   = OUTCOME_ICONS.get(outcome, "⛏")
        color  = OUTCOME_COLORS.get(outcome, CRIMSON)
        flavor = OUTCOME_FLAVOR.get(outcome, OUTCOME_FLAVOR["common"])

        embed = discord.Embed(
            title=f"{icon}  Infernal Mines — Extraction Complete",
            description=flavor,
            color=color,
        )

        # ── Failure: minimal panel ────────────────────────────────────────────
        if outcome == "failure":
            embed.add_field(name=BLANK,        value=BLANK,                       inline=False)
            embed.add_field(name="💼  Wallet", value=f"**{format_dc(balance)}**", inline=False)
            embed.set_footer(text="Recorded by the Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        # ── Extraction value (with optional bonus line) ───────────────────────
        raw = gross - flat_bonus
        if flat_bonus:
            extraction_val = f"**+{format_dc(raw)}**\n*+{format_dc(flat_bonus)} bonus*"
        else:
            extraction_val = f"**+{format_dc(raw)}**"

        # ── Tax value ─────────────────────────────────────────────────────────
        if tax == 0 or eff_rate == 0:
            tax_val = "**Exempt**"
        else:
            tax_val = f"**−{format_dc(tax)}**\n*{format_tax_rate(eff_rate)} rate*"

        # ── Row 1: Extraction | Tax ───────────────────────────────────────────
        embed.add_field(name=BLANK,             value=BLANK,           inline=False)
        embed.add_field(name="🪨  Extraction",  value=extraction_val,  inline=True)
        embed.add_field(name="⚖  Tax Applied", value=tax_val,          inline=True)

        # ── Row 2: Net Gain | Wallet ──────────────────────────────────────────
        embed.add_field(name=BLANK,             value=BLANK,                       inline=False)
        embed.add_field(name="🔥  Net Gain",    value=f"**+{format_dc(net)}**",    inline=True)
        embed.add_field(name="💼  Wallet",      value=f"**{format_dc(balance)}**", inline=True)

        embed.set_footer(text="Recorded by the Kingdom Treasury  ·  Kingdom of Hell")
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
            title="🩸  Kingdom Tribute",
            description="*The Kingdom has taken notice. Your loyalty is recorded.*",
            color=CRIMSON,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        embed.add_field(name="💰  Tribute Reward",  value=f"**+{format_dc(base)}**",                    inline=True)
        if bonus > 0:
            embed.add_field(name="⚡  Activity Bonus", value=f"**+{format_dc(bonus)}**",               inline=True)
        else:
            embed.add_field(name=BLANK,               value=BLANK,                                     inline=True)
        embed.add_field(name="⚖  Tax",               value=f"**−{format_dc(tax)}** `({format_tax_rate(tax_rate)})`", inline=True)

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="🔥  Total Earned",     value=f"## +{format_dc(net)}",                     inline=True)
        embed.add_field(name=BLANK,                  value=BLANK,                                       inline=True)
        embed.add_field(name="💳  Wallet",           value=f"**{format_dc(balance)}**",                 inline=True)

        embed.set_footer(text='"Recognition is never free."  ·  Kingdom Treasury')
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
            title="💸  Wealth Transfer",
            description="*The transaction is sealed. Wealth moves under the Kingdom's gaze.*",
            color=DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        embed.add_field(name="📤  From",       value=f"**{sender_name}**",          inline=True)
        embed.add_field(name="📥  To",         value=f"**{recipient_name}**",       inline=True)
        embed.add_field(name=BLANK,            value=BLANK,                         inline=True)

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💰  Sent",       value=f"**{format_dc(amount)}**",    inline=True)
        embed.add_field(name="⚖  Levy",        value=f"**−{format_dc(tax)}** `(2%)`", inline=True)
        embed.add_field(name="✅  Received",   value=f"**+{format_dc(net)}**",      inline=True)

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💳  Your Wallet", value=f"**{format_dc(sender_balance)}**", inline=False)

        embed.set_footer(text='"No transaction escapes the Kingdom ledger."  ·  Kingdom Treasury')
        return embed

    # ─── Ascend ───────────────────────────────────────────────────────────────

    @staticmethod
    def ascend_confirm(rank_name: str, cost: int, current_balance: int) -> discord.Embed:
        treasury_cut = int(cost * 0.10)
        burned       = cost - treasury_cut
        remaining    = current_balance - cost
        embed = discord.Embed(
            title="👑  Ascension Ritual",
            description=(
                f"*You seek the rank of **{rank_name}**.*\n"
                "*The ritual is irreversible. The Kingdom offers no refunds.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)

        embed.add_field(name="👑  Target Rank",   value=f"**{rank_name}**",             inline=True)
        embed.add_field(name="💰  Cost",          value=f"**{format_dc(cost)}**",        inline=True)
        embed.add_field(name=BLANK,               value=BLANK,                           inline=True)

        embed.add_field(name="🏦  Treasury Cut",  value=f"**{format_dc(treasury_cut)}** `(10%)`", inline=True)
        embed.add_field(name="🔥  Burned",        value=f"**{format_dc(burned)}** `(90%)`",       inline=True)
        embed.add_field(name="💳  After",         value=f"**{format_dc(remaining)}**",             inline=True)

        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)
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
                "*Your rise is sealed into the Kingdom's eternal ledger.*"
            ),
            color=GOLD,
        )
        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)
        embed.add_field(name="👑  New Rank",      value=f"## {rank_name}",             inline=False)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💰  Cost Paid",     value=f"**{format_dc(cost)}**",       inline=True)
        embed.add_field(name="🏦  To Treasury",   value=f"**{format_dc(treasury_cut)}**", inline=True)
        embed.add_field(name="🔥  Burned",        value=f"**{format_dc(burned)}**",     inline=True)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💳  Remaining",     value=f"**{format_dc(new_balance)}**", inline=False)
        embed.set_footer(text='"The Kingdom grows stronger with every ascension."  ·  Kingdom Treasury')
        return embed

    # ─── Market ───────────────────────────────────────────────────────────────

    @staticmethod
    def market_page(ranks: list, page: int, total_pages: int) -> discord.Embed:
        RANK_FLAVOR = {
            "Vermin":      "The first step above nothing. Your name enters the record.",
            "Corrupted":   "Tainted by ambition. The hierarchy begins to notice.",
            "Folklore":    "Spoken of in dark halls. A name that carries weight.",
            "Mythology":   "Your existence becomes legend. The lower ranks defer.",
            "Demonology":  "The language of demons is now your native tongue.",
            "Eschatology": "You study the end of all things. Power through knowledge.",
            "Archangel":   "Between sacred and infernal. A rare and delicate rank.",
            "Archdemon":   "The void bends. The Kingdom watches you closely.",
            "Knight":      "Honor forged through force. The noble class begins here.",
            "Baron":       "Land and blood. A title that carries its own history.",
            "Viscount":    "The court acknowledges you. Doors begin to open.",
            "Count":       "Your decisions carry weight beyond your own walls.",
            "Marquis":     "Between Baron and Duke — quiet, absolute authority.",
            "Duke":        "The upper echelon. The throne is within reach.",
        }

        embed = discord.Embed(
            title="🏪  Kingdom Market",
            description=(
                "*Ascend. Compete. Dominate.*\n"
                "*Ranks must be purchased in sequence. There is no skipping the climb.*"
            ),
            color=BLOOD_RED,
        )
        embed.add_field(name=BLANK, value=SEP_GOLD, inline=False)

        for name, cost, tax_rate in ranks:
            flavor  = RANK_FLAVOR.get(name, "A rank of the Kingdom hierarchy.")
            tax_str = f"{int(tax_rate * 100)}%" if tax_rate > 0 else "Exempt"
            embed.add_field(
                name=f"👑  {name}",
                value=(
                    f"*{flavor}*\n"
                    f"💰  **{format_cost(cost)}**   ⚖  Tax `{tax_str}`\n"
                    f"Use `/ascend {name}` to claim."
                ),
                inline=False,
            )
            embed.add_field(name=BLANK, value=SEP_THIN, inline=False)

        embed.set_footer(
            text=f"Page {page} of {total_pages}  ·  /ascend <rank> to purchase  ·  Kingdom Treasury"
        )
        return embed

    # ─── Black Market (removed) ───────────────────────────────────────────────

    @staticmethod
    def blackmarket_page(
        items: List[Dict[str, Any]], page: int, total_pages: int
    ) -> discord.Embed:
        embed = discord.Embed(
            title="🕵️  Black Market",
            description=(
                "*Items of forbidden provenance. The Kingdom does not sanction these transactions.*\n"
                "*Every deal leaves a trace. Cerberus is always watching.*"
            ),
            color=DEEP_PURPLE,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        for item in items:
            ri = item.get("risk_increase", 0)
            rr = item.get("risk_reduce",   0)
            if ri > 0:
                risk_line = f"⚠️  **+{ri} Risk**"
            elif rr > 0:
                risk_line = f"🟢  **−{rr} Risk**"
            else:
                risk_line = "⬜  No risk change"

            embed.add_field(
                name=f"**{item['name']}**",
                value=(
                    f"*{item['description']}*\n"
                    f"💰  **{format_dc(item['cost'])}**   {risk_line}"
                ),
                inline=False,
            )
            embed.add_field(name=BLANK, value=SEP_THIN, inline=False)

        embed.set_footer(
            text=f"Page {page} of {total_pages}  ·  Rotates every 6 hours  ·  Kingdom Treasury"
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
            "LOW":      "*Transaction sealed. No trace in the official record.*",
            "MEDIUM":   "*The market remembers every soul. Cerberus has taken notice.*",
            "HIGH":     "*The hound stirs. Your record grows increasingly suspicious.*",
            "CRITICAL": "*Cerberus is fully awake. Every move you make is catalogued.*",
        }

        embed = discord.Embed(
            title="🕵️  Black Market — Transaction Sealed",
            description=CERBERUS_LINES[new_label],
            color=ec,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        embed.add_field(name="📦  Item",      value=f"**{item['name']}**",    inline=True)
        embed.add_field(name="💰  Cost",      value=f"**{format_dc(cost)}**", inline=True)
        embed.add_field(name=BLANK,           value=BLANK,                    inline=True)
        embed.add_field(name="⚡  Effect",   value=f"*{item['description']}*", inline=False)

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)

        if risk_delta > 0:
            tier_arrow = f"{old_icon} {old_label}  →  {new_icon} {new_label}" if new_label != old_label else f"{new_icon} {new_label}"
            embed.add_field(name="⚠️  Risk",  value=f"**+{risk_delta}** → `{new_risk}/100`  {tier_arrow}", inline=False)
        elif risk_delta < 0:
            tier_arrow = f"{old_icon} {old_label}  →  {new_icon} {new_label}" if new_label != old_label else f"{new_icon} {new_label}"
            embed.add_field(name="🟢  Risk",  value=f"**{risk_delta}** → `{new_risk}/100`  {tier_arrow}",  inline=False)
        else:
            embed.add_field(name="⬜  Risk",  value=f"Unchanged `{new_risk}/100`",                         inline=False)

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💳  Wallet", value=f"**{format_dc(new_balance)}**", inline=False)

        FOOTER = {
            "LOW":      "No immediate threat detected.",
            "MEDIUM":   "Cerberus is aware of your presence.",
            "HIGH":     "Cerberus is watching. Check /identity for your record.",
            "CRITICAL": "Immediate audit risk. The Kingdom is closing in.",
        }
        embed.set_footer(text=f"{FOOTER[new_label]}  ·  Kingdom Treasury")
        return embed

    # ─── Cerberus Audit ───────────────────────────────────────────────────────

    @staticmethod
    def cerberus_cleared(risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Cleared",
            description="*The hound circles. It sniffs. It finds nothing. This time.*",
            color=VOID_BLACK,
        )
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="✅  Outcome",   value="**Cleared**",        inline=True)
        embed.add_field(name="📉  Risk Delta", value=f"**{risk_delta:+d}**", inline=True)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.set_footer(text='"The hound remembers even when it does not act."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def cerberus_penalty(penalty: int, penalty_pct: float, risk_delta: int) -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Penalty Exacted",
            description="*The hound has found its quarry. The Kingdom collects what is owed.*",
            color=DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)
        embed.add_field(name="⚠️  Outcome",   value="**Penalized**",                                    inline=True)
        embed.add_field(name="💸  Seized",    value=f"**−{format_dc(penalty)}** `({int(penalty_pct * 100)}%)`", inline=True)
        embed.add_field(name="📉  Risk Delta", value=f"**{risk_delta:+d}**",                             inline=True)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.set_footer(text='"Cerberus does not forget. Neither does the ledger."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def cerberus_immune() -> discord.Embed:
        embed = discord.Embed(
            title="🐕  Cerberus Audit — Shadow Cloak",
            description="*The hound circles. Your cloak absorbs the scent. Cerberus finds nothing.*",
            color=VOID_PURPLE,
        )
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="🌑  Outcome", value="**Immune** *(Shadow Cloak consumed)*", inline=False)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.set_footer(text='"The void protects — but only once."  ·  Kingdom Treasury')
        return embed

    # ─── Investments ──────────────────────────────────────────────────────────

    @staticmethod
    def investment_opened(result: dict) -> discord.Embed:
        matures_at = result["matures_at"]
        unix_ts    = int(matures_at.timestamp())
        embed = discord.Embed(
            title="📈  Investment Opened",
            description="*Capital deployed. The infernal markets will render their verdict in time.*",
            color=DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)
        embed.add_field(name="📊  Type",       value=f"**{result['label']}**",             inline=True)
        embed.add_field(name="💰  Principal",  value=f"**{format_dc(result['amount'])}**", inline=True)
        embed.add_field(name="⏳  Matures",   value=f"<t:{unix_ts}:R>",                   inline=True)
        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💳  Remaining",  value=f"**{format_dc(result['new_balance'])}**", inline=False)
        embed.set_footer(text='"Capital deployed. The Kingdom watches it grow."  ·  Kingdom Treasury')
        return embed

    @staticmethod
    def portfolio(investments: list) -> discord.Embed:
        if not investments:
            embed = discord.Embed(
                title="📊  Investment Portfolio",
                description=(
                    "*Your portfolio is empty. No capital is at work.*\n"
                    "*Use `/invest` to open a position.*"
                ),
                color=VOID_BLACK,
            )
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            return embed

        any_ready = any(inv["matured"] for inv in investments)
        embed = discord.Embed(
            title="📊  Investment Portfolio",
            description=(
                "*Capital deployed across the infernal markets.*\n"
                + ("*Positions ready for collection.*" if any_ready else "*Positions still maturing.*")
            ),
            color=GOLD if any_ready else DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        for inv in investments:
            unix_ts = int(inv["matures_at_dt"].timestamp())
            status  = "✅  **Ready to collect**" if inv["matured"] else f"⏳  <t:{unix_ts}:R>"
            embed.add_field(
                name=f"**#{inv['id']}**  ·  {inv['inv_type'].replace('_', ' ').title()}",
                value=(
                    f"💰  Principal: **{format_dc(inv['principal'])}**\n"
                    f"{status}"
                ),
                inline=True,
            )

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.set_footer(text="Use /collect to claim matured positions  ·  Kingdom Treasury")
        return embed

    @staticmethod
    def investment_collected(result: dict) -> discord.Embed:
        results      = result["results"]
        total_payout = result["total_payout"]
        new_balance  = result["new_balance"]
        all_profit   = all(r["success"] for r in results)

        embed = discord.Embed(
            title="📈  Investments Settled",
            description="*The Kingdom renders its verdict. The ledger is updated.*",
            color=GOLD if all_profit else CRIMSON,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        for r in results:
            sign        = "+" if r["profit"] >= 0 else "−"
            profit_val  = abs(r["profit"])
            outcome_tag = "✅  Profit" if r["success"] else "📉  Loss"
            embed.add_field(
                name=f"**#{r['id']}**  ·  {r['inv_type'].replace('_',' ').title()}  ·  {outcome_tag}",
                value=(
                    f"💰  Principal: **{format_dc(r['principal'])}**\n"
                    f"📤  Payout: **{format_dc(r['payout'])}**  `({sign}{format_dc(profit_val)})`"
                ),
                inline=False,
            )

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💰  Total Received", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="💳  Wallet",         value=f"**{format_dc(new_balance)}**",  inline=True)
        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed

    @staticmethod
    def investment_withdrawn(result: dict) -> discord.Embed:
        new_balance  = result["new_balance"]
        total_payout = result["total_payout"]
        embed = discord.Embed(
            title="📉  Early Withdrawal",
            description=(
                "*The Kingdom does not reward impatience.*\n"
                "*A 20% penalty has been levied on all withdrawn positions.*"
            ),
            color=DARK_RED,
        )
        embed.add_field(name=BLANK, value=SEP, inline=False)

        for r in result["results"]:
            embed.add_field(
                name=f"**#{r['id']}**  ·  {r['inv_type'].replace('_',' ').title()}",
                value=(
                    f"💰  Principal: **{format_dc(r['principal'])}**\n"
                    f"🔥  Penalty: **−{format_dc(r['penalty'])}**\n"
                    f"📤  Received: **{format_dc(r['payout'])}**"
                ),
                inline=False,
            )

        embed.add_field(name=BLANK, value=SEP_THIN, inline=False)
        embed.add_field(name="💰  Total Received", value=f"**{format_dc(total_payout)}**", inline=True)
        embed.add_field(name="💳  Wallet",         value=f"**{format_dc(new_balance)}**",  inline=True)
        embed.set_footer(text='"The Kingdom does not forget the impatient."  ·  Kingdom Treasury')
        return embed

    # ─── Error / Cooldown ─────────────────────────────────────────────────────

    @staticmethod
    def cooldown_error(action: str, remaining_str: str) -> discord.Embed:
        FLAVOR = {
            "grind":   "The mines have not recovered. The rock demands rest.",
            "tribute": "The realm has not forgotten your last offering. Wait.",
        }
        flavor = FLAVOR.get(action, "The Kingdom demands patience.")
        embed = discord.Embed(
            title="⏳  Not Yet",
            description=f"*{flavor}*",
            color=IRON,
        )
        embed.add_field(name="⏱  Return In", value=f"**{remaining_str}**", inline=False)
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

    # ─── Cerberus Aggression Levels ────────────────────────────────────────────

    @staticmethod
    def cerberus_routing_deny(level: int, seizure: int = 0, rage_level: int = 0) -> discord.Embed:
        """
        Immersive routing denial embed.

        Levels 1–3 carry escalating tone.
        Level 4 carries rage-aware text + seizure details.
        rage_level reflects how many times this user has been taxed in the
        current loop (0 = first tax ever, increments each subsequent trigger).
        """
        if level == 1:
            embed = discord.Embed(
                title       = "Cerberus watches.",
                description = "*You are misplaced.*",
                color       = 0x1C1C1C,
            )
        elif level == 2:
            embed = discord.Embed(
                title       = "Cerberus grows impatient.",
                description = "*Do not test the Kingdom's patience.*",
                color       = 0x4A0000,
            )
        elif level == 3:
            embed = discord.Embed(
                title       = "The Kingdom rejects you.",
                description = "*You have been warned. Cease.*",
                color       = 0x8B0000,
            )
        else:
            # Level 4 — tone escalates with rage_level
            if rage_level <= 2:
                title = "Enough."
                flavor = "*Cerberus watches.*"
            elif rage_level <= 4:
                title = "You persist."
                flavor = "*Cerberus does not forget.*"
            elif rage_level <= 6:
                title = "The Kingdom takes more."
                flavor = "*You invited this.*"
            else:
                title = "There will be nothing left."
                flavor = "*The end of your defiance.*"

            if seizure > 0:
                description = (
                    f"{flavor}\n"
                    f"*Cerberus has claimed what is owed.*\n"
                    f"**{format_dc(seizure)}** has been seized."
                )
            else:
                description = f"{flavor}\n*Cerberus has claimed what is owed.*"

            embed = discord.Embed(
                title       = title,
                description = description,
                color       = 0x000000,
            )

        embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
        return embed
