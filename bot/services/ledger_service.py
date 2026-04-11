"""
Kingdom Treasury — Infernal Ledger (Economy Surveillance System)

Logs every real money movement to private staff channels.
Detects suspicious patterns and auto-freezes offenders.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Optional, Literal

import discord

logger = logging.getLogger("kingdom_treasury")

# ── Private surveillance channels ─────────────────────────────────────────────

LEDGER_CHANNELS: list[int] = [1492242938959495168, 1492242905580965991]

_DC  = "<:devilcoinStack:1492184333392412692>"
_SEP = "━━━━━━━━━━━━━━━━━━━"

# ── Gravity thresholds ────────────────────────────────────────────────────────

_LOW_CAP    = 5_000     # < LOW_CAP  → LOW
_HIGH_FLOOR = 50_000    # ≥ HIGH_FLOOR → HIGH (else MEDIUM)

GravityLevel = Literal["LOW", "MEDIUM", "HIGH"]
AlertLevel   = Literal["alert", "critical"]

_GRAVITY_COLORS = {"LOW": 0x1A1A1A, "MEDIUM": 0xB22222, "HIGH": 0xFFD700}
_GRAVITY_FOOTER = {
    "LOW":    "Noted",
    "MEDIUM": "The balance shifts",
    "HIGH":   "The Kingdom has taken notice",
}

# ── Action labels ─────────────────────────────────────────────────────────────

_ACTION_LABELS: dict[str, str] = {
    "grind":           "Extraction",
    "tribute":         "Contract Fulfilled",
    "cerberus":        "Tax",
    "mission_reward":  "Mission Completed",
    "mission_entry":   "Purchase",
    "invest":          "Treasury Shift",
    "collect":         "Treasury Shift",
    "withdraw":        "Treasury Shift",
    "treasury_add":    "Treasury Shift",
    "treasury_remove": "Treasury Shift",
    "treasury_set":    "Treasury Shift",
    "add_dc":          "Treasury Shift",
    "remove_dc":       "Extraction",
    "ascend":          "Ascension Cost",
    "market_purchase":     "Market Purchase",
    "market_purchase_web": "Web Market Purchase",
    "daily_tax":       "Daily Tax",
    "debt_registered": "Debt Registered",
    "debt_repayment":  "Debt Repayment",
    "debt_cleared":    "Debt Cleared",
}


def _gravity(amount: int) -> GravityLevel:
    if amount >= _HIGH_FLOOR:
        return "HIGH"
    if amount >= _LOW_CAP:
        return "MEDIUM"
    return "LOW"


def _action_label(action: str, amount: int) -> str:
    if action == "transfer":
        if amount >= 100_000:
            return "Major Transfer"
        if amount >= 10_000:
            return "Transfer Recorded"
        return "Transfer"
    return _ACTION_LABELS.get(action, action.replace("_", " ").title())


class LedgerService:
    def __init__(self, bot):
        self.bot = bot
        # Per-user activity ring: discord_id → deque[(timestamp, amount, action)]
        self._activity: dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        # Per-user critical alert timestamps for auto-freeze logic
        self._critical_ts: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

    # ── Internal channel sender ────────────────────────────────────────────────

    async def _post(self, embed: discord.Embed) -> None:
        for ch_id in LEDGER_CHANNELS:
            ch = self.bot.get_channel(ch_id)
            if ch is None:
                logger.warning(f"[Ledger] Channel {ch_id} not in cache — cannot post surveillance log")
                continue
            try:
                await ch.send(embed=embed)
            except Exception as exc:
                logger.error(f"[Ledger] Failed to send to channel {ch_id}: {exc}")

    # ── Primary logging entry point ───────────────────────────────────────────

    async def log(
        self,
        *,
        action: str,
        amount: int,
        from_label: str,
        to_label: str,
        guild_id: str,
        from_discord_id: Optional[str] = None,
        wallet_before:   Optional[int] = None,
        wallet_after:    Optional[int] = None,
        treasury_before: Optional[int] = None,
        treasury_after:  Optional[int] = None,
        action_type: str = "transfer",
    ) -> None:
        """Log an economy movement and run alert/behaviour checks."""
        g       = _gravity(amount)
        label   = _action_label(action, amount)
        lines: list[str] = []

        if g == "HIGH":
            lines.append(f"{_SEP}\n🪙  **LEDGER ENTRY — MAJOR**\n{_SEP}")
        elif g == "MEDIUM":
            lines.append(f"{_SEP}\n🪙  **LEDGER ENTRY**\n{_SEP}")

        lines.append(f"**{label}**")
        lines.append(f"\n{from_label}  →  {to_label}")
        lines.append(f"**{amount:,}** {_DC}")

        if wallet_before is not None and wallet_after is not None:
            lines.append(f"\n**Wallet:** {wallet_before:,} → {wallet_after:,}")
        elif wallet_after is not None:
            lines.append(f"\n**Wallet:** {wallet_after:,}")

        if treasury_before is not None and treasury_after is not None:
            lines.append(f"**Treasury:** {treasury_before:,} → {treasury_after:,}")

        lines.append(f"\n*{_GRAVITY_FOOTER[g]}*")

        embed = discord.Embed(
            description="\n".join(lines),
            color=_GRAVITY_COLORS[g],
        )
        await self._post(embed)

        # Behaviour & threshold checks
        if from_discord_id:
            await self._analyse(
                discord_id   = from_discord_id,
                guild_id     = guild_id,
                amount       = amount,
                action       = action,
                action_type  = action_type,
                from_label   = from_label,
                to_label     = to_label,
                label        = label,
            )

    # ── Alert / behaviour analysis ─────────────────────────────────────────────

    async def _analyse(
        self,
        *,
        discord_id: str,
        guild_id: str,
        amount: int,
        action: str,
        action_type: str,
        from_label: str,
        to_label: str,
        label: str,
    ) -> None:
        now = time.monotonic()
        self._activity[discord_id].append((now, amount, action_type))

        level = self._threshold_check(amount, action_type)

        # Behaviour-based overrides
        behaviour = self._behaviour_check(discord_id, now, amount, action_type)
        if behaviour:
            if level is None or behaviour == "critical":
                level = behaviour

        if level is None:
            return

        await self._send_alert(
            level       = level,
            discord_id  = discord_id,
            amount      = amount,
            from_label  = from_label,
            to_label    = to_label,
            label       = label,
            reason      = None,
        )

        if level == "critical":
            self._critical_ts[discord_id].append(now)
            recent = [t for t in self._critical_ts[discord_id] if now - t <= 120]
            if len(recent) >= 2:
                await self._auto_freeze(discord_id, guild_id)

    def _threshold_check(self, amount: int, action_type: str) -> Optional[AlertLevel]:
        if action_type == "transfer":
            if amount >= 100_000:
                return "critical"
            if amount >= 50_000:
                return "alert"
        elif action_type == "treasury":
            if amount >= 100_000:
                return "critical"
            if amount >= 50_000:
                return "alert"
        elif action_type == "mission":
            if amount >= 50_000:
                return "alert"
        return None

    def _behaviour_check(
        self, discord_id: str, now: float, amount: int, action_type: str
    ) -> Optional[AlertLevel]:
        acts = list(self._activity[discord_id])

        # 5+ transfers or market actions in 30 s
        rapid = [e for e in acts if now - e[0] <= 30
                 and e[2] in ("transfer", "mission_entry", "market")]
        if len(rapid) >= 5:
            return "alert"

        # 3+ large transfers (≥50 k) in 2 min
        large = [e for e in acts if now - e[0] <= 120 and e[1] >= 50_000]
        if len(large) >= 3:
            return "critical"

        # Wallet gain ≥100 k in 1 min
        gain = sum(
            e[1] for e in acts
            if now - e[0] <= 60
            and e[2] in ("grind", "tribute", "mission_reward", "collect")
        )
        if gain >= 100_000:
            return "critical"

        return None

    async def _send_alert(
        self,
        *,
        level: AlertLevel,
        discord_id: str,
        amount: int,
        from_label: str,
        to_label: str,
        label: str,
        reason: Optional[str],
    ) -> None:
        if level == "critical":
            desc = (
                f"{_SEP}\n💀  **CRITICAL ALERT**\n{_SEP}\n\n"
                f"**Suspicious Activity Detected**\n\n"
                f"**User:** {from_label}\n"
                f"**Action:** {label}\n"
                f"**Amount:** {amount:,} {_DC}"
            )
            if reason:
                desc += f"\n**Reason:** {reason}"
            desc += "\n\n🕯️ *Judgment may be required*"
            color = 0x8B0000
        else:
            desc = (
                f"{_SEP}\n🚨  **ECONOMY ALERT**\n{_SEP}\n\n"
                f"**{label}**\n\n"
                f"{from_label}  →  {to_label}\n"
                f"**{amount:,}** {_DC}\n\n"
                f"🕯️ *The Kingdom has taken notice*"
            )
            color = 0xFF4500

        embed = discord.Embed(description=desc, color=color)
        await self._post(embed)

    async def _auto_freeze(self, discord_id: str, guild_id: str) -> None:
        """Freeze a user automatically after 2 criticals within 2 minutes."""
        try:
            db   = self.bot.db
            user = await db.get_user(guild_id, discord_id)
            if user and user.get("is_frozen"):
                return  # already frozen
            await db.freeze_user(
                guild_id   = guild_id,
                discord_id = discord_id,
                reason     = "Auto-freeze: repeated critical alerts",
                frozen_by  = "SYSTEM",
            )
            logger.warning(f"[Ledger] Auto-freeze: guild={guild_id} user={discord_id}")
            desc = (
                f"{_SEP}\n❄️  **AUTO-FREEZE EXECUTED**\n{_SEP}\n\n"
                f"**User:** <@{discord_id}>\n"
                f"**Reason:** Repeated critical alerts (2 in 2 min)\n"
                f"**Source:** System\n\n"
                f"🕯️ *The ledger has been sealed.*"
            )
            await self._post(discord.Embed(description=desc, color=0x00BFFF))
        except Exception as exc:
            logger.error(f"[Ledger] Auto-freeze error: {exc}")

    # ── Freeze / unfreeze log helpers (called by FreezeCog) ───────────────────

    async def log_freeze(
        self,
        *,
        target: discord.Member,
        executor: str,
        reason: str,
        auto: bool,
    ) -> None:
        desc = (
            f"{_SEP}\n❄️  **LEDGER SEALED**\n{_SEP}\n\n"
            f"**Target:** {target.mention}\n"
            f"**By:** {executor}\n"
            f"**Reason:** {reason or 'Not specified'}\n"
            f"**Type:** {'Automatic' if auto else 'Manual'}\n\n"
            f"🕯️ *No transactions may pass.*"
        )
        await self._post(discord.Embed(description=desc, color=0x00BFFF))

    async def log_unfreeze(self, *, target: discord.Member, executor: str) -> None:
        desc = (
            f"{_SEP}\n🔓  **SEAL LIFTED**\n{_SEP}\n\n"
            f"**Target:** {target.mention}\n"
            f"**By:** {executor}\n\n"
            f"🕯️ *The ledger has been reopened.*"
        )
        await self._post(discord.Embed(description=desc, color=0x00FF7F))
