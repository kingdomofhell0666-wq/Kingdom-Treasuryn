"""
Cerberus Aggression System — Multi-Level Enforcement + Punitive Tax Engine

Tracks per-user violation history entirely in-memory (no schema change needed).
Violations decay after the inactivity window.

Aggression levels:
  Level 1 — first violation      → cold correction
  Level 2 — second violation     → firm warning
  Level 3 — 3–4 violations       → hostile rejection
  Level 4 — 5+ violations        → dominance + financial seizure

Level 4 applies a one-shot punitive tax scaled by player rank.  After the tax
fires the violation counter drops back to 3, preventing infinite escalation.
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("kingdom_treasury")


# ── Tax tiers by rank index ─────────────────────────────────────────────────
# (pct, min_amount, max_amount)
# Rank index matches RANKS list in rank_service.py (0=Forsaken … 14=Duke).
_TAX_TIERS: list[tuple[float, int, int]] = [
    (0.05,  50,  1_000),   # 0  Forsaken    \
    (0.05,  50,  1_000),   # 1  Vermin       |  LOW
    (0.05,  50,  1_000),   # 2  Corrupted    |
    (0.05,  50,  1_000),   # 3  Folklore     |
    (0.05,  50,  1_000),   # 4  Mythology   /
    (0.10, 100,  5_000),   # 5  Demonology  \
    (0.10, 100,  5_000),   # 6  Eschatology  |  MID
    (0.10, 100,  5_000),   # 7  Archangel    |
    (0.10, 100,  5_000),   # 8  Archdemon   /
    (0.15, 500, 10_000),   # 9  Knight      \
    (0.15, 500, 10_000),   # 10 Baron        |  HIGH
    (0.15, 500, 10_000),   # 11 Viscount     |
    (0.15, 500, 10_000),   # 12 Count       /
    (0.20, 1_000, 25_000), # 13 Marquis     \  ELITE
    (0.20, 1_000, 25_000), # 14 Duke        /
]

# Fallback if rank index is somehow out of range
_TAX_DEFAULT = (0.05, 50, 1_000)

_RANK_INDEX: dict[str, int] = {
    "Forsaken": 0, "Vermin": 1, "Corrupted": 2, "Folklore": 3,
    "Mythology": 4, "Demonology": 5, "Eschatology": 6, "Archangel": 7,
    "Archdemon": 8, "Knight": 9, "Baron": 10, "Viscount": 11,
    "Count": 12, "Marquis": 13, "Duke": 14,
}

RESET_WINDOW  = 180    # seconds — inactivity window before counter resets
L4_COOLDOWN   = 300    # seconds — how long before Level 4 can fire again
L4_THRESHOLD  = 5      # violations needed to reach Level 4
L4_POST_RESET = 3      # counter value after Level 4 executes


def _level_from_violations(n: int) -> int:
    if n <= 0:  return 0
    if n == 1:  return 1
    if n == 2:  return 2
    if n <= 4:  return 3
    return 4


class CerberusAggression:
    """
    In-memory aggression tracker.  No DB reads/writes happen here except for
    the Level 4 financial seizure (which uses the DB passed to execute_seizure).
    """

    def __init__(self):
        # { (guild_id, discord_id): {violations, last_violation, l4_taxed_at} }
        self._state: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def record_violation(self, guild_id: str, discord_id: str) -> int:
        """
        Increment the violation counter and return the resulting aggression level.
        Resets the counter if the inactivity window has elapsed since last violation.
        """
        key = (guild_id, discord_id)
        now = time.monotonic()
        state = self._state.get(key)

        if state is None or (now - state["last_violation"]) >= RESET_WINDOW:
            self._state[key] = {
                "violations": 1,
                "last_violation": now,
                "l4_taxed_at": state["l4_taxed_at"] if state else 0.0,
            }
        else:
            state["violations"]    += 1
            state["last_violation"] = now

        violations = self._state[key]["violations"]
        level = _level_from_violations(violations)

        logger.info(
            f"[CERBERUS] guild={guild_id} user={discord_id} "
            f"violations={violations} level={level}"
        )
        return level

    def should_tax(self, guild_id: str, discord_id: str) -> bool:
        """True if Level 4 tax should fire (not on cooldown)."""
        key   = (guild_id, discord_id)
        state = self._state.get(key)
        if state is None:
            return False
        now            = time.monotonic()
        last_taxed_at  = state.get("l4_taxed_at", 0.0)
        return (now - last_taxed_at) >= L4_COOLDOWN

    def mark_taxed(self, guild_id: str, discord_id: str):
        """Record that Level 4 tax fired; drop counter to L4_POST_RESET."""
        key   = (guild_id, discord_id)
        state = self._state.get(key)
        if state:
            state["l4_taxed_at"] = time.monotonic()
            state["violations"]  = L4_POST_RESET

    async def execute_seizure(
        self,
        db,
        guild_id:    str,
        discord_id:  str,
        rank:        str,
    ) -> int:
        """
        Compute and apply the punitive tax for a Level 4 violation.

        Returns the amount seized (0 if wallet was empty or an error occurred).
        Writes balance update + transaction log to the DB.
        """
        rank_idx = _RANK_INDEX.get(rank, 0)
        pct, min_amt, max_amt = _TAX_TIERS[rank_idx] if rank_idx < len(_TAX_TIERS) else _TAX_DEFAULT

        try:
            user    = await db.get_user(guild_id, discord_id)
            balance = user.get("balance", 0) if user else 0

            if balance <= 0:
                self.mark_taxed(guild_id, discord_id)
                return 0

            raw_seizure  = int(balance * pct)
            seizure      = max(min(raw_seizure, max_amt), min_amt)
            seizure      = min(seizure, balance)   # never below 0

            await db.update_balance(guild_id, discord_id, -seizure)
            await db.update_treasury(guild_id, seizure)
            await db.log_transaction(
                guild_id,
                "cerberus_level_4_tax",
                f"user:{discord_id}",
                "treasury",
                seizure,
                f"Cerberus Level 4 punitive seizure ({int(pct * 100)}% — {rank})",
            )

            self.mark_taxed(guild_id, discord_id)
            logger.warning(
                f"[CERBERUS L4 TAX] guild={guild_id} user={discord_id} "
                f"rank={rank} seizure={seizure} pct={pct*100:.0f}%"
            )
            return seizure

        except Exception as exc:
            logger.error(f"[CERBERUS] seizure failed for user={discord_id}: {exc}")
            self.mark_taxed(guild_id, discord_id)
            return 0
