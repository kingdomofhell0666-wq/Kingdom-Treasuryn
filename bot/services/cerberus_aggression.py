"""
Cerberus Aggression System — Multi-Level Enforcement + Punitive Tax Engine
with Escalating Rage Multiplier

STATE per (guild_id, discord_id):
  violations      — increments on each wrong-channel command
  last_violation  — monotonic timestamp; used to detect inactivity reset
  l4_taxed_at     — monotonic timestamp; short cooldown to prevent click-spam
  rage_level      — counts how many times L4 has fired this loop; resets on inactivity

FLOW:
  violation 1     → Level 1  (cold)
  violation 2     → Level 2  (firm)
  violations 3–4  → Level 3  (hostile)
  violations 5+   → Level 4  (seizure; rage_level increments, violations reset to 1)

After Level 4 fires:
  - violations reset to 1 (user is back at Level 1)
  - rage_level increments (tax gets heavier next time)
  - loop continues — "same action re-triggers escalation"

Loop stops when:
  - wallet == 0
  - OR seizure computes to 0
  - OR user goes quiet (inactivity window expires → rage_level resets to 0)
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("kingdom_treasury")


# ── Constants ──────────────────────────────────────────────────────────────────

RESET_WINDOW   = 180    # seconds — inactivity window → reset violations + rage_level
L4_COOLDOWN    = 10     # seconds — minimum gap between two L4 seizures (click-spam guard)
RAGE_INCREMENT = 0.02   # +2% tax per rage level
MAX_TAX_PCT    = 0.50   # hard cap — never exceed 50%


# ── Rank → (base_pct, min_amount, max_amount) ─────────────────────────────────
# max_amount is not clamped on the high end for the rage system (only min/wallet safety).

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

_TAX_DEFAULT = (0.05, 50, 1_000)

_RANK_INDEX: dict[str, int] = {
    "Forsaken": 0, "Vermin": 1, "Corrupted": 2, "Folklore": 3,
    "Mythology": 4, "Demonology": 5, "Eschatology": 6, "Archangel": 7,
    "Archdemon": 8, "Knight": 9, "Baron": 10, "Viscount": 11,
    "Count": 12, "Marquis": 13, "Duke": 14,
}


# ── Level mapping ──────────────────────────────────────────────────────────────

def _level_from_violations(n: int) -> int:
    if n <= 0:  return 0
    if n == 1:  return 1
    if n == 2:  return 2
    if n <= 4:  return 3
    return 4


# ── Service ────────────────────────────────────────────────────────────────────

class CerberusAggression:
    """
    In-memory aggression + rage tracker.
    The only DB I/O is inside execute_seizure (balance deduct + tx log).
    """

    def __init__(self):
        # { (guild_id, discord_id): {violations, last_violation, l4_taxed_at, rage_level} }
        self._state: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # ──────────────────────────────────────────────────────────────────────────

    def _get_or_reset(self, guild_id: str, discord_id: str, now: float) -> Dict[str, Any]:
        """Return existing state or create/reset a fresh entry."""
        key   = (guild_id, discord_id)
        state = self._state.get(key)

        if state is None or (now - state["last_violation"]) >= RESET_WINDOW:
            # Inactivity → full reset (rage_level goes back to 0)
            self._state[key] = {
                "violations":     1,
                "last_violation": now,
                "l4_taxed_at":    state["l4_taxed_at"] if state else 0.0,
                "rage_level":     0,
            }
        else:
            state["violations"]    += 1
            state["last_violation"] = now

        return self._state[key]

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def record_violation(self, guild_id: str, discord_id: str) -> int:
        """
        Record a routing violation.  Returns the current aggression level (1–4).
        If inactivity window elapsed, counter and rage_level are reset first.
        """
        now   = time.monotonic()
        state = self._get_or_reset(guild_id, discord_id, now)

        violations = state["violations"]
        level      = _level_from_violations(violations)

        logger.info(
            f"[CERBERUS] guild={guild_id} user={discord_id} "
            f"violations={violations} level={level} rage={state['rage_level']}"
        )
        return level

    def get_rage_level(self, guild_id: str, discord_id: str) -> int:
        """Return current rage_level (0 = first L4 trigger in this loop)."""
        state = self._state.get((guild_id, discord_id))
        return state["rage_level"] if state else 0

    def should_tax(self, guild_id: str, discord_id: str) -> bool:
        """True if Level 4 tax may fire (click-spam guard not active)."""
        state = self._state.get((guild_id, discord_id))
        if state is None:
            return False
        return (time.monotonic() - state.get("l4_taxed_at", 0.0)) >= L4_COOLDOWN

    def _mark_taxed(self, guild_id: str, discord_id: str):
        """
        Record that Level 4 fired:
          - increment rage_level (heavier punishment next time)
          - reset violations to 1  (user is back at Level 1)
          - stamp l4_taxed_at  (click-spam guard)
        """
        key   = (guild_id, discord_id)
        state = self._state.get(key)
        if state:
            state["l4_taxed_at"] = time.monotonic()
            state["rage_level"] += 1
            state["violations"]  = 1   # reset to Level 1, not Level 3

    # ──────────────────────────────────────────────────────────────────────────

    async def execute_seizure(
        self,
        db,
        guild_id:   str,
        discord_id: str,
        rank:       str,
    ) -> dict:
        """
        Compute and apply the Level 4 punitive tax with rage scaling.

        Returns a dict:
          seizure      — amount actually taken (0 if wallet empty or error)
          rage_level   — rage_level at the moment of this trigger (before increment)
          base_pct     — rank tier base percentage
          final_pct    — base + rage scaling, capped at MAX_TAX_PCT
          wallet_before
          wallet_after
        """
        key      = (guild_id, discord_id)
        state    = self._state.get(key, {})
        rage_lvl = state.get("rage_level", 0)

        # ── Tax rate ─────────────────────────────────────────────────────────
        rank_idx         = _RANK_INDEX.get(rank, 0)
        base_pct, min_amt, max_amt = (
            _TAX_TIERS[rank_idx] if rank_idx < len(_TAX_TIERS) else _TAX_DEFAULT
        )
        final_pct = min(base_pct + rage_lvl * RAGE_INCREMENT, MAX_TAX_PCT)

        empty_result = {
            "seizure": 0, "rage_level": rage_lvl,
            "base_pct": base_pct, "final_pct": final_pct,
            "wallet_before": 0, "wallet_after": 0,
        }

        try:
            user           = await db.get_user(guild_id, discord_id)
            wallet_before  = user.get("balance", 0) if user else 0

            if wallet_before <= 0:
                self._mark_taxed(guild_id, discord_id)
                return {**empty_result, "wallet_before": wallet_before}

            raw_seizure = int(wallet_before * final_pct)
            seizure     = max(raw_seizure, min_amt)        # enforce minimum
            seizure     = min(seizure, wallet_before)      # never drop below 0

            if seizure <= 0:
                self._mark_taxed(guild_id, discord_id)
                return {**empty_result, "wallet_before": wallet_before}

            wallet_after = wallet_before - seizure

            await db.update_balance(guild_id, discord_id, -seizure)
            await db.update_treasury(guild_id, seizure)
            await db.log_transaction(
                guild_id,
                "cerberus_level_4_tax",
                f"user:{discord_id}",
                "treasury",
                seizure,
                (
                    f"Cerberus L4 seizure — "
                    f"rage={rage_lvl} "
                    f"base={int(base_pct*100)}% "
                    f"final={int(final_pct*100)}% "
                    f"rank={rank} "
                    f"before={wallet_before} "
                    f"after={wallet_after}"
                ),
            )

            self._mark_taxed(guild_id, discord_id)

            logger.warning(
                f"[CERBERUS L4] guild={guild_id} user={discord_id} "
                f"rank={rank} rage={rage_lvl} "
                f"base={base_pct*100:.0f}% final={final_pct*100:.0f}% "
                f"seized={seizure} before={wallet_before} after={wallet_after}"
            )

            return {
                "seizure":       seizure,
                "rage_level":    rage_lvl,
                "base_pct":      base_pct,
                "final_pct":     final_pct,
                "wallet_before": wallet_before,
                "wallet_after":  wallet_after,
            }

        except Exception as exc:
            logger.error(f"[CERBERUS] seizure failed for user={discord_id}: {exc}")
            self._mark_taxed(guild_id, discord_id)
            return empty_result
