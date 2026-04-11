/**
 * Market API routes — proxy to bot's internal HTTP API (port 8091)
 *
 *  GET  /api/market/catalog  → full item catalog
 *  GET  /api/market/me       → current user wallet + inventory
 *  POST /api/market/purchase → execute item purchase
 *
 * All routes require a valid Discord session (requireAuth).
 * The bot HTTP API is localhost-only — no additional token needed.
 */
import { Router } from "express";
import axios from "axios";
import { requireAuth } from "../lib/session";

const router = Router();
const BOT_API = "http://127.0.0.1:8091";

type BotError = { response?: { status?: number; data?: unknown } };

async function botGet(path: string) {
  const res = await axios.get(`${BOT_API}${path}`, { timeout: 8_000 });
  return res.data;
}

async function botPost(path: string, body: unknown) {
  const res = await axios.post(`${BOT_API}${path}`, body, {
    timeout: 12_000,
    headers: { "Content-Type": "application/json" },
  });
  return res.data;
}

// ── GET /api/market/catalog ──────────────────────────────────────────────────

router.get("/market/catalog", requireAuth, async (req, res) => {
  try {
    const data = await botGet("/market/catalog");
    res.json(data);
  } catch (err) {
    req.log?.error({ err }, "market catalog fetch failed");
    res.status(502).json({ error: "The Exchange is temporarily unavailable." });
  }
});

// ── GET /api/market/me ───────────────────────────────────────────────────────

router.get("/market/me", requireAuth, async (req, res) => {
  const discordId = req.session.discordUser!.id;
  try {
    const data = await botGet(`/market/user?discord_id=${discordId}`);
    res.json(data);
  } catch (err) {
    const status = (err as BotError)?.response?.status;
    if (status === 404) {
      res.status(404).json({
        error: "Not found. Use any economy command in Discord first to register.",
      });
    } else {
      req.log?.error({ err }, "market user fetch failed");
      res.status(502).json({ error: "The Exchange is temporarily unavailable." });
    }
  }
});

// ── POST /api/market/purchase ────────────────────────────────────────────────

router.post("/market/purchase", requireAuth, async (req, res) => {
  const discordId = req.session.discordUser!.id;
  const { item_type, item_id } = req.body as { item_type?: string; item_id?: string };

  if (!item_type || !item_id) {
    res.status(400).json({ error: "item_type and item_id are required." });
    return;
  }

  try {
    const data = await botPost("/market/purchase", {
      discord_id: discordId,
      item_type,
      item_id,
    });
    res.json(data);
  } catch (err) {
    const resp = (err as BotError)?.response;
    if (resp?.status === 400 || resp?.status === 403 || resp?.status === 404) {
      res.status(resp.status!).json(resp.data);
    } else {
      req.log?.error({ err }, "market purchase failed");
      res.status(502).json({ error: "The Exchange is temporarily unavailable." });
    }
  }
});

export default router;
