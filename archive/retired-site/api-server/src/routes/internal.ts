import "../types";
import { Router, type Request, type Response } from "express";
import { logger } from "../lib/logger";
import { pool } from "../lib/db";
import { getInternalToken } from "../lib/internal-token";

const router = Router();

/** Middleware: validate the internal bearer token */
function requireInternalToken(req: Request, res: Response, next: () => void) {
  const auth = req.headers["authorization"] ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : auth;

  if (!token || token !== getInternalToken()) {
    logger.warn(
      { ip: req.ip, ua: req.headers["user-agent"] },
      "Heartbeat auth failure — invalid or missing token",
    );
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  next();
}

/**
 * POST /internal/heartbeat
 * Called by the bot every N seconds to report its liveness.
 *
 * Body:
 *   guild_count          number
 *   latency_ms           number
 *   uptime_seconds       number
 *   shard_id             number   (optional, default 0)
 *   bot_user_id          string
 *   bot_username         string
 *   scheduler_status     string   ("running" | "idle" | "error")
 *   db_status            string   ("connected" | "error")
 *   command_count_today  number   (optional)
 */
router.post("/heartbeat", requireInternalToken, async (req, res) => {
  const {
    guild_count,
    latency_ms,
    uptime_seconds,
    shard_id = 0,
    bot_user_id,
    bot_username,
    scheduler_status,
    db_status,
    command_count_today = null,
  } = req.body as Record<string, unknown>;

  if (!bot_user_id || !bot_username) {
    res.status(400).json({ error: "bot_user_id and bot_username are required" });
    return;
  }

  try {
    await pool.query(
      `INSERT INTO bot_heartbeat
         (guild_id, bot_user_id, bot_username, latency_ms, guild_count,
          shard_id, uptime_seconds, scheduler_status, db_status,
          command_count_today, written_at)
       VALUES ('__bot__', $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
       ON CONFLICT (guild_id) DO UPDATE SET
         bot_user_id         = EXCLUDED.bot_user_id,
         bot_username        = EXCLUDED.bot_username,
         latency_ms          = EXCLUDED.latency_ms,
         guild_count         = EXCLUDED.guild_count,
         shard_id            = EXCLUDED.shard_id,
         uptime_seconds      = EXCLUDED.uptime_seconds,
         scheduler_status    = EXCLUDED.scheduler_status,
         db_status           = EXCLUDED.db_status,
         command_count_today = EXCLUDED.command_count_today,
         written_at          = NOW()`,
      [
        bot_user_id,
        bot_username,
        latency_ms ?? null,
        guild_count ?? null,
        shard_id,
        uptime_seconds ?? null,
        scheduler_status ?? null,
        db_status ?? null,
        command_count_today,
      ],
    );

    logger.debug(
      { bot_username, latency_ms, uptime_seconds, guild_count },
      "Heartbeat received and stored",
    );
    res.json({ ok: true, ts: Date.now() });
  } catch (err) {
    logger.error({ err }, "Failed to store heartbeat");
    res.status(500).json({ error: "Internal error" });
  }
});

export default router;
