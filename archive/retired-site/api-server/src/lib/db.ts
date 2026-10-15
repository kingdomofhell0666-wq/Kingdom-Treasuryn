import { Pool } from "pg";
import { logger } from "./logger";

export const pool = new Pool({
  connectionString: process.env["DATABASE_URL"],
  max:                     10,
  idleTimeoutMillis:   30_000,
  connectionTimeoutMillis: 5_000,
});

pool.on("error", (err) => {
  logger.error({ err }, "PostgreSQL pool error");
});

export async function initDb(): Promise<void> {
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS bot_heartbeat (
        guild_id             TEXT PRIMARY KEY,
        bot_user_id          TEXT NOT NULL,
        bot_username         TEXT NOT NULL,
        latency_ms           INTEGER,
        guild_count          INTEGER,
        shard_id             INTEGER,
        uptime_seconds       BIGINT,
        scheduler_status     TEXT,
        db_status            TEXT,
        command_count_today  INTEGER,
        written_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `);

    // Safe migrations — add columns that may not exist on older installs
    const alterations = [
      "ALTER TABLE bot_heartbeat ADD COLUMN IF NOT EXISTS uptime_seconds       BIGINT",
      "ALTER TABLE bot_heartbeat ADD COLUMN IF NOT EXISTS scheduler_status     TEXT",
      "ALTER TABLE bot_heartbeat ADD COLUMN IF NOT EXISTS db_status            TEXT",
      "ALTER TABLE bot_heartbeat ADD COLUMN IF NOT EXISTS command_count_today  INTEGER",
    ];
    for (const sql of alterations) {
      await pool.query(sql);
    }

    logger.info("Database initialised.");
  } catch (err) {
    logger.warn({ err }, "DB init warning (may be harmless)");
  }
}
