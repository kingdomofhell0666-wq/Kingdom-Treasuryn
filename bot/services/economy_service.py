import random
from typing import Dict, Any, List, Optional, Tuple
from ..database import Database
from .transaction_service import TransactionService
from .rank_service import RankService


# ── Default probability tiers (used when guild_config has no custom values) ──
# Each entry: (cumulative_probability, reward_low, reward_high, label)
# These are calibrated to the default grind_max_reward of 500.
# When the guild sets a different max, all non-zero tiers scale accordingly.
_DEFAULT_GRIND_OUTCOMES: List[Tuple[float, int, int, str]] = [
    (0.60, 250, 350, "common"),
    (0.80, 100, 200, "meager"),
    (0.90, 0,   0,   "failure"),
    (0.97, 400, 600, "rich"),
    (1.00, 800, 1200, "jackpot"),
]

# Default max that the above tiers were designed around (jackpot high = 1200,
# but the config's grind_max_reward default is 500 → scale factor = 500/500 = 1.0)
_DEFAULT_GRIND_MAX = 500


class EconomyService:
    def __init__(self, db: Database, config_service=None):
        self.db             = db
        self.config_service = config_service
        self.tx_service     = TransactionService(db)
        self.rank_service   = RankService()

    TRIBUTE_BASE_MIN        = 500
    TRIBUTE_BASE_MAX        = 700
    TRIBUTE_GRIND_BONUS     = 200
    TRIBUTE_GRIND_THRESHOLD = 5

    # ── Guild-config-backed reward helpers ─────────────────────────────────────

    async def _get_guild_cfg(self, guild_id: str) -> Dict:
        if self.config_service:
            try:
                return await self.config_service.get_guild_config(guild_id)
            except Exception:
                pass
        return {}

    async def _grind_outcomes(self, guild_id: str) -> List[Tuple[float, int, int, str]]:
        """
        Return the grind probability tiers, scaled to the guild's configured
        grind_max_reward.  All non-zero reward values are multiplied by
        (configured_max / _DEFAULT_GRIND_MAX).  The grind_min_reward sets a
        floor on any non-zero result.
        """
        cfg        = await self._get_guild_cfg(guild_id)
        max_reward = int(cfg.get("grind_max_reward") or _DEFAULT_GRIND_MAX)
        min_reward = int(cfg.get("grind_min_reward") or 50)
        scale      = max(0.1, max_reward / _DEFAULT_GRIND_MAX)

        scaled = []
        for prob, low, high, label in _DEFAULT_GRIND_OUTCOMES:
            if high == 0:
                scaled.append((prob, 0, 0, label))
            else:
                new_low  = max(min_reward, int(low * scale))
                new_high = max(new_low + 1, int(high * scale))
                scaled.append((prob, new_low, new_high, label))
        return scaled

    async def _tribute_range(self, guild_id: str) -> Tuple[int, int]:
        """Return (min, max) for tribute reward from guild config."""
        cfg = await self._get_guild_cfg(guild_id)
        return (
            int(cfg.get("tribute_min_reward") or self.TRIBUTE_BASE_MIN),
            int(cfg.get("tribute_max_reward") or self.TRIBUTE_BASE_MAX),
        )

    # ── /grind ────────────────────────────────────────────────────────────────

    async def grind(self, guild_id: str, discord_id: str, username: str) -> Dict[str, Any]:
        user  = await self.db.upsert_user(guild_id, discord_id, username)
        perks = await self._get_active_perks(guild_id, discord_id)

        boost_perk = next((p for p in perks if p["perk_type"] == "grind_boost"), None)
        if boost_perk:
            outcomes = await self._grind_outcomes(guild_id)
            # Jackpot or rich tier — use the top bucket
            jackpot = outcomes[-1]
            rich    = outcomes[-2]
            gross         = random.randint(rich[1], jackpot[2])
            outcome_label = "jackpot" if gross >= jackpot[1] else "rich"
            await self.db.consume_perk(boost_perk["id"])
        else:
            outcomes      = await self._grind_outcomes(guild_id)
            roll          = random.random()
            gross         = 0
            outcome_label = "failure"
            for prob, low, high, label in outcomes:
                if roll < prob:
                    gross         = random.randint(low, high) if high > 0 else 0
                    outcome_label = label
                    break

        bonus_perk = next((p for p in perks if p["perk_type"] == "grind_bonus"), None)
        flat_bonus = 0
        if bonus_perk and gross > 0:
            flat_bonus = int(bonus_perk["perk_value"])
            gross     += flat_bonus
            await self.db.consume_perk(bonus_perk["id"])

        ceiling_perk = next((p for p in perks if p["perk_type"] == "grind_ceiling"), None)
        if ceiling_perk and gross > 0:
            gross += int(ceiling_perk["perk_value"])
            await self.db.consume_perk(ceiling_perk["id"])

        base_tax_rate      = self.rank_service.get_tax_rate(user["rank"])
        effective_tax_rate = base_tax_rate

        exempt_perk = next((p for p in perks if p["perk_type"] == "tax_exempt"), None)
        if exempt_perk and gross > 0:
            effective_tax_rate = 0.0
            await self.db.consume_perk(exempt_perk["id"])
        else:
            reduction_perk = next((p for p in perks if p["perk_type"] == "tax_reduction"), None)
            if reduction_perk and gross > 0:
                effective_tax_rate = max(0.0, base_tax_rate - reduction_perk["perk_value"])
                await self.db.consume_perk(reduction_perk["id"])

        tax_amount = int(gross * effective_tax_rate)
        net        = gross - tax_amount

        if net > 0 or tax_amount > 0:
            await self.tx_service.grind_reward(guild_id, discord_id, gross, tax_amount, net)

        await self.db.increment_grind_count(guild_id, discord_id)
        updated = await self.db.get_user(guild_id, discord_id)

        return {
            "success":          outcome_label != "failure",
            "outcome_label":    outcome_label,
            "gross":            gross,
            "flat_bonus":       flat_bonus,
            "base_tax_rate":    base_tax_rate,
            "effective_tax_rate": effective_tax_rate,
            "tax_amount":       tax_amount,
            "net":              net,
            "new_balance":      updated["balance"]          if updated else 0,
            "rank":             updated["rank"]             if updated else "Forsaken",
            "equipped_skin":    updated.get("equipped_skin") if updated else None,
        }

    # ── /tribute ──────────────────────────────────────────────────────────────

    async def tribute(self, guild_id: str, discord_id: str, username: str) -> Dict[str, Any]:
        user  = await self.db.upsert_user(guild_id, discord_id, username)
        perks = await self._get_active_perks(guild_id, discord_id)

        trib_min, trib_max = await self._tribute_range(guild_id)
        base      = random.randint(trib_min, trib_max)
        grind_24h = await self.db.get_grind_count_24h(guild_id, discord_id)
        bonus     = self.TRIBUTE_GRIND_BONUS if grind_24h >= self.TRIBUTE_GRIND_THRESHOLD else 0
        gross     = base + bonus

        tax_rate = self.rank_service.get_tax_rate(user["rank"])
        exempt_perk = next((p for p in perks if p["perk_type"] == "tax_exempt"), None)
        if exempt_perk:
            tax_rate = 0.0
            await self.db.consume_perk(exempt_perk["id"])

        tax = int(gross * tax_rate)
        net = gross - tax

        await self.tx_service.tribute_reward(guild_id, discord_id, gross, tax, net)
        updated = await self.db.get_user(guild_id, discord_id)

        return {
            "gross":       gross,
            "bonus":       bonus,
            "tax_amount":  tax,
            "tax_rate":    tax_rate,
            "net":         net,
            "new_balance":   updated["balance"]             if updated else 0,
            "rank":          updated.get("rank", "Forsaken") if updated else "Forsaken",
            "equipped_skin": updated.get("equipped_skin")    if updated else None,
        }

    # ── /transfer ─────────────────────────────────────────────────────────────

    async def transfer(
        self,
        guild_id: str,
        sender_id: str,
        sender_name: str,
        recipient_id: str,
        recipient_name: str,
        amount: int,
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")
        if sender_id == recipient_id:
            raise ValueError("You cannot transfer to yourself.")
        sender = await self.db.upsert_user(guild_id, sender_id, sender_name)
        if sender["balance"] < amount:
            raise ValueError(f"Insufficient funds. You have **{sender['balance']:,}** <:devilcoinStack:1492184333392412692>.")
        await self.db.upsert_user(guild_id, recipient_id, recipient_name)

        TAX_RATE         = 0.02
        tax              = int(amount * TAX_RATE)
        net_to_recipient = amount - tax

        await self.tx_service.transfer_funds(guild_id, sender_id, recipient_id, amount, tax, net_to_recipient)
        updated = await self.db.get_user(guild_id, sender_id)

        return {
            "amount":            amount,
            "tax_on_transfer":   tax,
            "net_to_recipient":  net_to_recipient,
            "sender_balance":    updated["balance"]             if updated else 0,
            "sender_rank":       updated.get("rank", "Forsaken") if updated else "Forsaken",
            "equipped_skin":     updated.get("equipped_skin")    if updated else None,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_active_perks(self, guild_id: str, discord_id: str) -> List[dict]:
        return await self.db.get_active_perks(guild_id, discord_id)
