"""
Kingdom Exchange — Internal Market HTTP API

aiohttp server bound to 127.0.0.1:8091 (localhost only).
The Node.js API Server proxies web-market requests here;
all purchases run through the bot's own service layer so
wallet mutations, ownership updates, and ledger logs are
handled by the exact same code path as Discord commands.

Endpoints
─────────
  GET  /market/catalog           → full item catalog
  GET  /market/user?discord_id=  → wallet, rank, owned + equipped
  POST /market/purchase          → validate + execute purchase
"""
from __future__ import annotations

import json
import logging
from typing import Optional, List

from aiohttp import web

from ..utils.skins import (
    SKINS, TITLES_CATALOG, RELICS_CATALOG, BADGES_CATALOG,
    RANK_ORDER, DEFAULT_SKIN_ID, DEFAULT_TITLE,
)

logger = logging.getLogger("kingdom_treasury")

KINGDOM_GUILD_ID = "1290484661318975499"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _rank_ok(user_rank: str, min_rank: str) -> bool:
    if not min_rank:
        return True
    return RANK_ORDER.get(user_rank, 0) >= RANK_ORDER.get(min_rank, 0)


# ── Serializers ───────────────────────────────────────────────────────────────

def _skin(s) -> dict:
    return {
        "id": s.id, "name": s.name, "description": s.description,
        "price_dc": s.price_dc, "rarity": s.rarity,
        "theme_tag": s.theme_tag, "stat_icon": s.stat_icon,
        "color": f"#{s.color:06X}",
    }


def _title(key: str, t) -> dict:
    return {
        "id": key, "name": t.name, "description": t.description,
        "price_dc": t.price_dc, "rarity": t.rarity,
    }


def _relic(r) -> dict:
    return {
        "id": r.id, "name": r.name, "description": r.description,
        "effect_desc": r.effect_desc, "price_dc": r.price_dc,
        "rarity": r.rarity, "min_rank": r.min_rank,
    }


def _badge(b) -> dict:
    return {
        "id": b.id, "name": b.name, "description": b.description,
        "price_dc": b.price_dc, "rarity": b.rarity,
        "icon": b.icon, "min_rank": b.min_rank,
    }


# ── Main HTTP API ─────────────────────────────────────────────────────────────

class MarketHTTPAPI:
    PORT = 8091

    def __init__(self, bot):
        self.bot = bot
        self._runner: Optional[web.AppRunner] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        app = web.Application()
        app.router.add_get("/market/catalog",   self.handle_catalog)
        app.router.add_get("/market/user",      self.handle_user)
        app.router.add_post("/market/purchase", self.handle_purchase)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", self.PORT)
        await site.start()
        logger.info(f"[MarketAPI] Listening on http://127.0.0.1:{self.PORT}")

    async def stop(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            logger.info("[MarketAPI] Stopped.")

    # ── GET /market/catalog ───────────────────────────────────────────────────

    async def handle_catalog(self, _request: web.Request) -> web.Response:
        catalog = {
            "relics": [_relic(r) for r in RELICS_CATALOG.values()],
            "titles": [_title(k, t) for k, t in TITLES_CATALOG.items() if t.price_dc > 0],
            "skins":  [_skin(s)  for s in SKINS.values()           if s.price_dc > 0],
            "badges": [_badge(b) for b in BADGES_CATALOG.values()],
        }
        return web.json_response(catalog)

    # ── GET /market/user?discord_id=X ─────────────────────────────────────────

    async def handle_user(self, request: web.Request) -> web.Response:
        discord_id = request.rel_url.query.get("discord_id", "").strip()
        if not discord_id:
            return web.json_response({"error": "discord_id required"}, status=400)

        db   = self.bot.db
        user = await db.get_user(KINGDOM_GUILD_ID, discord_id)
        if not user:
            return web.json_response(
                {"error": "Not found. Use any economy command in Discord first."},
                status=404,
            )

        return web.json_response({
            "balance":         user.get("balance", 0),
            "rank":            user.get("rank", "Forsaken"),
            "sacrifice_active": bool(user.get("sacrifice_active")),
            "owned_relics":    _parse(user.get("owned_relics",  "[]")),
            "owned_titles":    _parse(user.get("owned_titles",  "[]")),
            "owned_skins":     _parse(user.get("owned_skins",   "[]")),
            "owned_badges":    _parse(user.get("owned_badges",  "[]")),
            "equipped_relic":  user.get("equipped_relic")  or "",
            "equipped_title":  user.get("equipped_title")  or DEFAULT_TITLE,
            "equipped_skin":   user.get("equipped_skin")   or DEFAULT_SKIN_ID,
            "equipped_badges": _parse(user.get("equipped_badges", "[]")),
        })

    # ── POST /market/purchase ─────────────────────────────────────────────────

    async def handle_purchase(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "Invalid JSON."}, status=400)

        discord_id = str(data.get("discord_id", "")).strip()
        item_type  = str(data.get("item_type",  "")).strip()
        item_id    = str(data.get("item_id",    "")).strip()

        if not discord_id or not item_type or not item_id:
            return web.json_response(
                {"ok": False, "error": "discord_id, item_type and item_id are required."},
                status=400,
            )

        db     = self.bot.db
        svc    = self.bot.cosmetic_service
        ledger = self.bot.ledger_service

        user = await db.get_user(KINGDOM_GUILD_ID, discord_id)
        if not user:
            return web.json_response(
                {"ok": False, "error": "Not found. Use any economy command in Discord first."},
                status=404,
            )

        # Sacrifice gate
        if user.get("sacrifice_active"):
            return web.json_response(
                {"ok": False, "error": "The gates are sealed. Settle your debt before you may enter."},
                status=403,
            )

        user_rank     = user.get("rank", "Forsaken")
        wallet_before = user.get("balance", 0)

        # Rank lock
        min_rank = ""
        if item_type == "relics":
            r = RELICS_CATALOG.get(item_id)
            if r:
                min_rank = r.min_rank
        elif item_type == "badges":
            b = BADGES_CATALOG.get(item_id)
            if b:
                min_rank = b.min_rank

        if min_rank and not _rank_ok(user_rank, min_rank):
            return web.json_response(
                {"ok": False, "error": f"Requires {min_rank} rank to unlock."},
                status=403,
            )

        # Execute purchase
        try:
            if item_type == "relics":
                result = await svc.buy_relic(KINGDOM_GUILD_ID, discord_id, item_id)
                name   = result["relic"].name
            elif item_type == "titles":
                result = await svc.buy_title(KINGDOM_GUILD_ID, discord_id, item_id)
                name   = result["title"].name
            elif item_type == "skins":
                result = await svc.buy_skin(KINGDOM_GUILD_ID, discord_id, item_id)
                name   = result["skin"].name
            elif item_type == "badges":
                result = await svc.buy_badge(KINGDOM_GUILD_ID, discord_id, item_id)
                name   = result["badge"].name
            else:
                return web.json_response({"ok": False, "error": "Invalid item_type."}, status=400)
        except ValueError as exc:
            return web.json_response({"ok": False, "error": str(exc)}, status=400)

        cost        = result["cost"]
        new_balance = result["new_balance"]

        # Ledger → both surveillance channels
        try:
            await ledger.log(
                action          = "market_purchase_web",
                amount          = cost,
                from_label      = f"@{discord_id}",
                to_label        = "Exchange",
                guild_id        = KINGDOM_GUILD_ID,
                from_discord_id = discord_id,
                wallet_before   = wallet_before,
                wallet_after    = new_balance,
            )
        except Exception as exc:
            logger.error(f"[MarketAPI] Ledger log failed: {exc}")

        return web.json_response({
            "ok":          True,
            "name":        name,
            "cost":        cost,
            "new_balance": new_balance,
        })
