import "../types";
import { Router } from "express";
import { logger } from "../lib/logger";
import { pool } from "../lib/db";
import { requireAuth } from "./guilds";
import { requireGuildAccess } from "../lib/guild-auth";

const router = Router();

// ── Shared helper: fetch latest heartbeat row ──────────────────────────────

interface HeartbeatRow {
  guild_id:            string;
  bot_user_id:         string;
  bot_username:        string;
  latency_ms:          number | null;
  guild_count:         number | null;
  shard_id:            number | null;
  uptime_seconds:      number | null;
  scheduler_status:    string | null;
  db_status:           string | null;
  command_count_today: number | null;
  written_at:          Date;
}

async function getHeartbeat(): Promise<HeartbeatRow | null> {
  const { rows } = await pool.query<HeartbeatRow>(
    "SELECT * FROM bot_heartbeat WHERE guild_id = '__bot__'",
  );
  return rows[0] ?? null;
}

type BotStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

function deriveStatus(heartbeat: HeartbeatRow | null): {
  status:       BotStatus;
  heartbeatAge: number | null;
} {
  if (!heartbeat) return { status: "OFFLINE", heartbeatAge: null };

  const ageMs  = Date.now() - new Date(heartbeat.written_at).getTime();
  const ageSec = Math.floor(ageMs / 1000);

  let status: BotStatus;
  if (ageSec < 15)      status = "ONLINE";
  else if (ageSec < 45) status = "DEGRADED";
  else                  status = "OFFLINE";

  return { status, heartbeatAge: ageSec };
}

async function checkDbAlive(): Promise<boolean> {
  try {
    await pool.query("SELECT 1");
    return true;
  } catch {
    return false;
  }
}

// ── GET /api/guilds/:guildId/health ────────────────────────────────────────

router.get(
  "/:guildId/health",
  requireAuth,
  requireGuildAccess,
  async (req, res) => {
    logger.debug({ guildId: req.params.guildId }, "Guild health check");
    const dbAlive = await checkDbAlive();
    res.json({
      api:       "ok",
      db:        dbAlive ? "ok" : "error",
      guildId:   req.params.guildId,
      timestamp: new Date().toISOString(),
    });
  },
);

// ── GET /api/guilds/:guildId/bot-status ────────────────────────────────────

router.get(
  "/:guildId/bot-status",
  requireAuth,
  requireGuildAccess,
  async (req, res) => {
    logger.debug({ guildId: req.params.guildId }, "Bot status request");

    try {
      const heartbeat         = await getHeartbeat();
      const { status, heartbeatAge } = deriveStatus(heartbeat);
      const dbAlive           = await checkDbAlive();

      res.json({
        status,
        heartbeatAge,
        apiStatus:  "ok",
        dbStatus:   dbAlive ? "ok" : "error",
        heartbeat:  heartbeat
          ? {
              guildCount:        heartbeat.guild_count,
              uptimeSeconds:     heartbeat.uptime_seconds,
              latencyMs:         heartbeat.latency_ms,
              schedulerStatus:   heartbeat.scheduler_status,
              dbStatus:          heartbeat.db_status,
              botUsername:       heartbeat.bot_username,
              botUserId:         heartbeat.bot_user_id,
              commandCountToday: heartbeat.command_count_today,
              writtenAt:         heartbeat.written_at,
            }
          : null,
      });
    } catch (err) {
      logger.error({ err, guildId: req.params.guildId }, "Bot status fetch failed");
      res.status(500).json({ error: "Failed to fetch bot status" });
    }
  },
);

// ── GET /api/guilds/:guildId/overview ──────────────────────────────────────

router.get(
  "/:guildId/overview",
  requireAuth,
  requireGuildAccess,
  async (req, res) => {
    logger.debug({ guildId: req.params.guildId }, "Overview request");

    try {
      const heartbeat               = await getHeartbeat();
      const { status, heartbeatAge } = deriveStatus(heartbeat);
      const dbAlive                 = await checkDbAlive();

      res.json({
        guildId:           req.params.guildId,
        botStatus:         status,
        heartbeatAge,
        botUsername:       heartbeat?.bot_username   ?? null,
        guildCount:        heartbeat?.guild_count    ?? null,
        uptimeSeconds:     heartbeat?.uptime_seconds ?? null,
        latencyMs:         heartbeat?.latency_ms     ?? null,
        schedulerStatus:   heartbeat?.scheduler_status ?? null,
        apiStatus:         "ok",
        dbStatus:          dbAlive ? "ok" : "error",
        lastHeartbeat:     heartbeat?.written_at     ?? null,
      });
    } catch (err) {
      logger.error({ err, guildId: req.params.guildId }, "Overview fetch failed");
      res.status(500).json({ error: "Failed to fetch overview" });
    }
  },
);

export default router;
