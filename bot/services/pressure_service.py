"""
Kingdom Treasury — Pressure System

Handles: daily taxes, debt tracking, sacrifice state, rank downgrade.
All balance-state transitions (debt entry/exit, sacrifice entry/exit)
are detected here and posted to the correct channels.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Optional, Tuple

import discord

from .rank_service import PUBLIC_KINGDOM_RANKS

logger = logging.getLogger("kingdom_treasury")

# ── Surveillance channels ─────────────────────────────────────────────────────
TAX_CHANNEL       = 1488260129446039572   # #💵┃taxes
DEBT_CHANNEL      = 1488244912746008617   # #🧾┃debt
SACRIFICE_CHANNEL = 1488244484717154486   # #🔪┃sacrifices

# ── Thresholds ────────────────────────────────────────────────────────────────
SACRIFICE_THRESHOLD  = -10_000    # wallet ≤ this → sacrifice activates
DOWNGRADE_COOLDOWN_S = 86_400 * 3  # 72 hours in seconds

_DC  = "<:devilcoinStack:1492184333392412692>"
_SEP = "━━━━━━━━━━━━━━━━━━━"

# ── Daily tax per rank ────────────────────────────────────────────────────────
DAILY_TAX: dict[str, int] = {
    "Forsaken":    0,
    "Vermin":      0,
    "Corrupted":   500,
    "Folklore":    1_000,
    "Mythology":   2_000,
    "Demonology":  4_000,
    "Eschatology": 8_000,
    "Archangel":   15_000,
    "Archdemon":   30_000,
    "Knight":      50_000,
    "Baron":       75_000,
    "Viscount":    100_000,
    "Count":       150_000,
    "Marquis":     200_000,
    "Duke":        300_000,
}

# ── Tax announcement templates ────────────────────────────────────────────────
_TAX_TEMPLATES = [
    (
        "💵  **Treasury Collection**\n\n"
        "The Kingdom has collected **{{total:,}}** {{dc}} in taxes today.\n\n"
        "**{{count}}** souls have fulfilled their obligation.\n\n"
        "*Your labor is... appreciated.*\n"
        "*The essence gathered will be put to far greater use.*\n\n"
        "The Kingdom grows."
    ),
    (
        "💵  **Treasury Collection**\n\n"
        "**{{total:,}}** {{dc}} have been extracted from **{{count}}** souls.\n\n"
        "*Your obedience does not go unnoticed.*\n\n"
        "*Continue your labor.*\n"
        "*The Kingdom will decide how your essence is spent.*"
    ),
    (
        "💵  **Treasury Collection**\n\n"
        "The Treasury has claimed **{{total:,}}** {{dc}} from **{{count}}** souls.\n\n"
        "*Your effort sustains the Kingdom.*\n\n"
        "*You exist to produce.*\n"
        "*We exist to take.*\n\n"
        "The balance is maintained."
    ),
]

# ── Rank downgrade order (Forsaken is the floor) ─────────────────────────────
_DOWNGRADE_ORDER = ["Forsaken"] + list(PUBLIC_KINGDOM_RANKS)


class PressureService:

    # ── Internal channel helper ───────────────────────────────────────────────

    async def _send(self, bot, channel_id: int, embed: discord.Embed):
        ch = bot.get_channel(channel_id)
        if ch is None:
            logger.warning(f"[Pressure] Channel {channel_id} not in cache")
            return
        try:
            await ch.send(embed=embed)
        except Exception as exc:
            logger.error(f"[Pressure] Failed to send to channel {channel_id}: {exc}")

    # ── Daily tax collection ──────────────────────────────────────────────────

    async def collect_and_announce_taxes(self, bot, guild_id: str) -> Tuple[int, int]:
        """
        Deduct daily taxes from every user in the guild.
        Posts one announcement to the tax channel.
        Returns (total_dc_collected, number_of_taxed_users).
        """
        db    = bot.db
        users = await db.get_all_users_for_guild(guild_id)
        if not users:
            return 0, 0

        total = 0
        count = 0

        for user in users:
            rank = user.get("rank", "Forsaken")
            tax  = DAILY_TAX.get(rank, 0)
            if tax == 0:
                continue

            old_bal = user["balance"]
            new_bal = old_bal - tax

            await db.update_balance(guild_id, user["discord_id"], -tax)
            await db.add_taxes_paid(guild_id, user["discord_id"], tax)
            total += tax
            count += 1

            await self.after_balance_change(
                bot        = bot,
                guild_id   = guild_id,
                discord_id = user["discord_id"],
                username   = user.get("username", "Unknown"),
                old_balance = old_bal,
                new_balance = new_bal,
            )

        if total > 0 and count > 0:
            raw = random.choice(_TAX_TEMPLATES)
            text = raw.replace("{{total:,}}", f"{total:,}") \
                      .replace("{{dc}}", _DC) \
                      .replace("{{count}}", str(count))
            embed = discord.Embed(description=text, color=0xFFD700)
            embed.set_footer(text="Kingdom Treasury  ·  Kingdom of Hell")
            await self._send(bot, TAX_CHANNEL, embed)

        return total, count

    # ── Balance-change state machine ──────────────────────────────────────────

    async def after_balance_change(
        self,
        *,
        bot,
        guild_id:    str,
        discord_id:  str,
        username:    str,
        old_balance: int,
        new_balance: int,
    ):
        """
        Call after ANY wallet change.
        Detects and announces: debt entry, debt exit, sacrifice entry, sacrifice exit.
        Reads current sacrifice_active from DB — no parameter needed.
        """
        db   = bot.db
        user = await db.get_user(guild_id, discord_id)
        if not user:
            return

        sacrifice_active = bool(user.get("sacrifice_active", 0))

        # ── Sacrifice: enter (wallet just crossed -10,000) ────────────────────
        if new_balance <= SACRIFICE_THRESHOLD and not sacrifice_active:
            await db.set_sacrifice_active(guild_id, discord_id, True)
            desc = (
                f"{_SEP}\n🔪  **Sacrifice Declared**\n{_SEP}\n\n"
                f"<@{discord_id}> has fallen too deep.\n\n"
                f"**Balance:** {new_balance:,} {_DC}\n\n"
                "**Penalty:**\n"
                "Ascension sealed\n"
                "Market access revoked\n"
                "Transfers revoked\n"
                "External aid denied\n\n"
                "*The Kingdom has taken notice.*"
            )
            await self._send(bot, SACRIFICE_CHANNEL,
                             discord.Embed(description=desc, color=0x8B0000))

        # ── Debt: enter (crossed zero going down) ─────────────────────────────
        if old_balance >= 0 and new_balance < 0:
            desc = (
                f"🧾  **Debt Registered**\n\n"
                f"<@{discord_id}> has fallen below 0.\n\n"
                f"**Balance:** {new_balance:,} {_DC}\n\n"
                "*The debt is now recorded.*"
            )
            await self._send(bot, DEBT_CHANNEL,
                             discord.Embed(description=desc, color=0x4A0000))

        # ── Sacrifice: exit (wallet returned to 0 or above) ──────────────────
        if new_balance >= 0 and sacrifice_active:
            await db.set_sacrifice_active(guild_id, discord_id, False)
            desc = (
                f"{_SEP}\n🔪  **Sacrifice Lifted**\n{_SEP}\n\n"
                f"<@{discord_id}> has returned to balance.\n\n"
                "*Access restored. The Kingdom loosens its grip.*"
            )
            await self._send(bot, SACRIFICE_CHANNEL,
                             discord.Embed(description=desc, color=0x2E4A2E))

        # ── Debt: exit (crossed zero going up) ────────────────────────────────
        if old_balance < 0 and new_balance >= 0:
            desc = (
                f"🧾  **Debt Cleared**\n\n"
                f"<@{discord_id}> has returned above 0.\n\n"
                f"**Balance:** {new_balance:,} {_DC}\n\n"
                "*The ledger is balanced again.*"
            )
            await self._send(bot, DEBT_CHANNEL,
                             discord.Embed(description=desc, color=0x1A5C1A))

    # ── Rank downgrade ────────────────────────────────────────────────────────

    def _get_previous_rank(self, rank: str) -> Optional[str]:
        """Return the rank one step below, or None if already at Forsaken."""
        try:
            idx = _DOWNGRADE_ORDER.index(rank)
        except ValueError:
            return None
        if idx <= 0:
            return None
        return _DOWNGRADE_ORDER[idx - 1]

    async def check_downgrades(self, bot, guild_id: str):
        """
        For every user currently in sacrifice, check if 72h have elapsed since
        their last downgrade (or they have never been downgraded). If so,
        reduce their rank by one step and post to sacrifice channel.
        """
        db    = bot.db
        users = await db.get_sacrifice_users(guild_id)
        now   = datetime.now(timezone.utc)

        for user in users:
            discord_id = user["discord_id"]
            rank       = user.get("rank", "Forsaken")

            last_str = user.get("last_downgrade_at")
            if last_str:
                try:
                    last_dt = datetime.fromisoformat(last_str)
                    if (now - last_dt).total_seconds() < DOWNGRADE_COOLDOWN_S:
                        continue
                except Exception:
                    pass

            prev_rank = self._get_previous_rank(rank)
            if prev_rank is None:
                continue

            await db.set_rank(guild_id, discord_id, prev_rank)
            await db.set_last_downgrade_at(guild_id, discord_id, now.isoformat())

            desc = (
                f"{_SEP}\n🔪  **Rank Forfeit**\n{_SEP}\n\n"
                f"<@{discord_id}> remained beneath the threshold.\n\n"
                f"**Penalty:** {rank} → {prev_rank}\n\n"
                "*The Kingdom has claimed its due.*"
            )
            await self._send(bot, SACRIFICE_CHANNEL,
                             discord.Embed(description=desc, color=0x6B0000))
            logger.info(f"[Pressure] Downgrade: guild={guild_id} user={discord_id} {rank}→{prev_rank}")
