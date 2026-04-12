/**
 * Extended guild config routes:
 *
 *  Command Routing:
 *    GET    /api/guilds/:id/routing
 *    PUT    /api/guilds/:id/routing/:command
 *    DELETE /api/guilds/:id/routing/:command
 *
 *  Command Permissions:
 *    GET    /api/guilds/:id/permissions
 *    PUT    /api/guilds/:id/permissions/:command
 *    DELETE /api/guilds/:id/permissions/:command
 *
 *  Rank-Role Mappings:
 *    GET    /api/guilds/:id/rank-roles
 *    PUT    /api/guilds/:id/rank-roles/:rank
 *    DELETE /api/guilds/:id/rank-roles/:rank
 *
 *  Leaderboard Settings:
 *    GET    /api/guilds/:id/leaderboard
 *    PATCH  /api/guilds/:id/leaderboard
 *
 *  Ascension Announcement Settings:
 *    GET    /api/guilds/:id/ascension-announcements
 *    PATCH  /api/guilds/:id/ascension-announcements
 *
 *  Rank Cooldown Settings:
 *    GET    /api/guilds/:id/rank-cooldowns
 *    PUT    /api/guilds/:id/rank-cooldowns/:rank
 *    DELETE /api/guilds/:id/rank-cooldowns/:rank
 *
 *  Reset:
 *    POST   /api/guilds/:id/reset
 *
 *  Ascension History:
 *    GET    /api/guilds/:id/ascension-history
 *
 *  Bot Leaderboard:
 *    GET    /api/guilds/:id/leaderboard/data
 */
import { Router } from "express";
import { requireAuth } from "../lib/session";
import {
  db,
  commandRoutingTable,
  commandPermissionsTable,
  rankRoleMappingTable,
  leaderboardSettingsTable,
  ascensionAnnouncementSettingsTable,
  rankCooldownSettingsTable,
  guildChannelsTable,
  guildRolesTable,
} from "@workspace/db";
import { eq, and } from "drizzle-orm";
import { assertGuildAdmin } from "../lib/discord";

const router = Router();

// ─── Canonical public Kingdom rank list ───────────────────────────────────────
// This is the single source of truth for rank validation in all API routes.
// Excludes Forsaken (starting state) and Chancellor (staff role — not purchasable).
// Must stay in sync with PUBLIC_KINGDOM_RANKS in bot/services/rank_service.py.
const PUBLIC_KINGDOM_RANKS = new Set([
  "Vermin", "Corrupted", "Folklore", "Mythology", "Demonology",
  "Eschatology", "Archangel", "Archdemon",
  "Knight", "Baron", "Viscount", "Count", "Marquis", "Duke",
]);

function assertPublicRank(rank: string, res: any): boolean {
  if (!PUBLIC_KINGDOM_RANKS.has(rank)) {
    res.status(400).json({
      error: `"${rank}" is not a valid public Kingdom rank. ` +
        `Allowed: ${[...PUBLIC_KINGDOM_RANKS].join(", ")}. ` +
        `Chancellor is a staff role and cannot be used in public rank configuration.`,
    });
    return false;
  }
  return true;
}

// ═══════════════════════════════════════════════════════════════
// COMMAND ROUTING
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/routing", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(commandRoutingTable)
    .where(eq(commandRoutingTable.guildId, guildId));
  res.json(rows);
});

router.put("/guilds/:guildId/routing/:command", requireAuth, async (req, res) => {
  const { guildId, command } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const { channelId, isGlobal } = req.body as { channelId?: string | null; isGlobal?: boolean };

  const existing = await db
    .select()
    .from(commandRoutingTable)
    .where(and(eq(commandRoutingTable.guildId, guildId), eq(commandRoutingTable.commandName, command)))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(commandRoutingTable)
      .set({ channelId: channelId ?? null, isGlobal: isGlobal ?? !channelId, updatedAt: new Date() })
      .where(and(eq(commandRoutingTable.guildId, guildId), eq(commandRoutingTable.commandName, command)))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(commandRoutingTable)
      .values({ guildId, commandName: command, channelId: channelId ?? null, isGlobal: isGlobal ?? !channelId })
      .returning();
    res.json(inserted);
  }
});

router.delete("/guilds/:guildId/routing/:command", requireAuth, async (req, res) => {
  const { guildId, command } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  await db
    .delete(commandRoutingTable)
    .where(and(eq(commandRoutingTable.guildId, guildId), eq(commandRoutingTable.commandName, command)));
  res.json({ success: true });
});

// ═══════════════════════════════════════════════════════════════
// COMMAND PERMISSIONS
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/permissions", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(commandPermissionsTable)
    .where(eq(commandPermissionsTable.guildId, guildId));
  res.json(rows);
});

router.put("/guilds/:guildId/permissions/:command", requireAuth, async (req, res) => {
  const { guildId, command } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const { allowedRoles = [], deniedRoles = [], allowedChannels = [], deniedChannels = [] } = req.body as {
    allowedRoles?: string[];
    deniedRoles?: string[];
    allowedChannels?: string[];
    deniedChannels?: string[];
  };

  const existing = await db
    .select()
    .from(commandPermissionsTable)
    .where(and(eq(commandPermissionsTable.guildId, guildId), eq(commandPermissionsTable.commandName, command)))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(commandPermissionsTable)
      .set({ allowedRoles, deniedRoles, allowedChannels, deniedChannels, updatedAt: new Date() })
      .where(and(eq(commandPermissionsTable.guildId, guildId), eq(commandPermissionsTable.commandName, command)))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(commandPermissionsTable)
      .values({ guildId, commandName: command, allowedRoles, deniedRoles, allowedChannels, deniedChannels })
      .returning();
    res.json(inserted);
  }
});

router.delete("/guilds/:guildId/permissions/:command", requireAuth, async (req, res) => {
  const { guildId, command } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  await db
    .delete(commandPermissionsTable)
    .where(and(eq(commandPermissionsTable.guildId, guildId), eq(commandPermissionsTable.commandName, command)));
  res.json({ success: true });
});

// ═══════════════════════════════════════════════════════════════
// RANK-ROLE MAPPINGS
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/rank-roles", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(rankRoleMappingTable)
    .where(eq(rankRoleMappingTable.guildId, guildId));
  res.json(rows);
});

router.put("/guilds/:guildId/rank-roles/:rank", requireAuth, async (req, res) => {
  const { guildId, rank } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;
  if (!assertPublicRank(rank, res)) return;

  const { roleId, removePrevious = true } = req.body as { roleId: string; removePrevious?: boolean };
  if (!roleId) { res.status(400).json({ error: "roleId is required." }); return; }

  const existing = await db
    .select()
    .from(rankRoleMappingTable)
    .where(and(eq(rankRoleMappingTable.guildId, guildId), eq(rankRoleMappingTable.rankName, rank)))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(rankRoleMappingTable)
      .set({ roleId, removePrevious, updatedAt: new Date() })
      .where(and(eq(rankRoleMappingTable.guildId, guildId), eq(rankRoleMappingTable.rankName, rank)))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(rankRoleMappingTable)
      .values({ guildId, rankName: rank, roleId, removePrevious })
      .returning();
    res.json(inserted);
  }
});

router.delete("/guilds/:guildId/rank-roles/:rank", requireAuth, async (req, res) => {
  const { guildId, rank } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  await db
    .delete(rankRoleMappingTable)
    .where(and(eq(rankRoleMappingTable.guildId, guildId), eq(rankRoleMappingTable.rankName, rank)));
  res.json({ success: true });
});

// ═══════════════════════════════════════════════════════════════
// LEADERBOARD SETTINGS
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/leaderboard", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const [row] = await db
    .select()
    .from(leaderboardSettingsTable)
    .where(eq(leaderboardSettingsTable.guildId, guildId))
    .limit(1);

  if (row) { res.json(row); return; }

  const [inserted] = await db
    .insert(leaderboardSettingsTable)
    .values({ guildId })
    .returning();
  res.json(inserted);
});

router.patch("/guilds/:guildId/leaderboard", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const allowed = [
    "enabled", "postFrequency",
    "postChannelId", "postHour", "postMinute",
    "postDayOfWeek", "postDayOfMonth", "timezone",
  ] as const;

  const patch: Record<string, unknown> = { updatedAt: new Date() };
  for (const key of allowed) {
    if (key in req.body) patch[key] = req.body[key];
  }

  const existing = await db
    .select()
    .from(leaderboardSettingsTable)
    .where(eq(leaderboardSettingsTable.guildId, guildId))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(leaderboardSettingsTable)
      .set(patch as Parameters<typeof db.update>[0])
      .where(eq(leaderboardSettingsTable.guildId, guildId))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(leaderboardSettingsTable)
      .values({ guildId, ...patch } as Parameters<typeof db.insert>[0])
      .returning();
    res.json(inserted);
  }
});

// ═══════════════════════════════════════════════════════════════
// ASCENSION ANNOUNCEMENT SETTINGS
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/ascension-announcements", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const [row] = await db
    .select()
    .from(ascensionAnnouncementSettingsTable)
    .where(eq(ascensionAnnouncementSettingsTable.guildId, guildId))
    .limit(1);

  if (row) { res.json(row); return; }

  const [inserted] = await db
    .insert(ascensionAnnouncementSettingsTable)
    .values({ guildId })
    .returning();
  res.json(inserted);
});

router.patch("/guilds/:guildId/ascension-announcements", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const { enabled, channelId, messageTemplate } = req.body as {
    enabled?: boolean;
    channelId?: string | null;
    messageTemplate?: string;
  };

  const patch: Record<string, unknown> = { updatedAt: new Date() };
  if (enabled !== undefined) patch["enabled"] = enabled;
  if (channelId !== undefined) patch["channelId"] = channelId;
  if (messageTemplate !== undefined) patch["messageTemplate"] = messageTemplate;

  const existing = await db
    .select()
    .from(ascensionAnnouncementSettingsTable)
    .where(eq(ascensionAnnouncementSettingsTable.guildId, guildId))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(ascensionAnnouncementSettingsTable)
      .set(patch as Parameters<typeof db.update>[0])
      .where(eq(ascensionAnnouncementSettingsTable.guildId, guildId))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(ascensionAnnouncementSettingsTable)
      .values({ guildId, ...patch } as Parameters<typeof db.insert>[0])
      .returning();
    res.json(inserted);
  }
});

// ═══════════════════════════════════════════════════════════════
// RANK COOLDOWN SETTINGS
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/rank-cooldowns", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(rankCooldownSettingsTable)
    .where(eq(rankCooldownSettingsTable.guildId, guildId));
  res.json(rows);
});

router.put("/guilds/:guildId/rank-cooldowns/:rank", requireAuth, async (req, res) => {
  const { guildId, rank } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;
  if (!assertPublicRank(rank, res)) return;

  const { cooldownSeconds } = req.body as { cooldownSeconds: number };
  if (cooldownSeconds === undefined) { res.status(400).json({ error: "cooldownSeconds is required." }); return; }

  const existing = await db
    .select()
    .from(rankCooldownSettingsTable)
    .where(and(eq(rankCooldownSettingsTable.guildId, guildId), eq(rankCooldownSettingsTable.rankName, rank)))
    .limit(1);

  if (existing.length > 0) {
    const [updated] = await db
      .update(rankCooldownSettingsTable)
      .set({ cooldownSeconds, updatedAt: new Date() })
      .where(and(eq(rankCooldownSettingsTable.guildId, guildId), eq(rankCooldownSettingsTable.rankName, rank)))
      .returning();
    res.json(updated);
  } else {
    const [inserted] = await db
      .insert(rankCooldownSettingsTable)
      .values({ guildId, rankName: rank, cooldownSeconds })
      .returning();
    res.json(inserted);
  }
});

router.delete("/guilds/:guildId/rank-cooldowns/:rank", requireAuth, async (req, res) => {
  const { guildId, rank } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  await db
    .delete(rankCooldownSettingsTable)
    .where(and(eq(rankCooldownSettingsTable.guildId, guildId), eq(rankCooldownSettingsTable.rankName, rank)));
  res.json({ success: true });
});

// ═══════════════════════════════════════════════════════════════
// RESET
// ═══════════════════════════════════════════════════════════════

router.post("/guilds/:guildId/reset", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const { confirm } = req.body as { confirm?: string };
  if (confirm !== "CONFIRM_RESET") {
    res.status(400).json({ error: "Send { confirm: 'CONFIRM_RESET' } to proceed." });
    return;
  }

  try {
    // Wipe economy tables in the bot's SQLite DB
    const Database = (await import("better-sqlite3")).default;
    const botDb = new Database("kingdom_treasury.db");

    botDb.exec(`
      DELETE FROM users       WHERE guild_id = '${guildId.replace(/'/g, "")}';
      DELETE FROM transactions WHERE guild_id = '${guildId.replace(/'/g, "")}';
      DELETE FROM treasury    WHERE guild_id = '${guildId.replace(/'/g, "")}';
      DELETE FROM cooldowns   WHERE guild_id = '${guildId.replace(/'/g, "")}';
      DELETE FROM investments  WHERE guild_id = '${guildId.replace(/'/g, "")}';
    `);
    botDb.close();

    res.json({ success: true, message: "Economy data for guild has been reset." });
  } catch {
    res.status(500).json({ error: "Failed to reset economy data." });
  }
});

// ═══════════════════════════════════════════════════════════════
// GUILD CHANNELS (synced from bot on startup/join)
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/channels", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(guildChannelsTable)
    .where(eq(guildChannelsTable.guildId, guildId));

  res.json(rows.map((r) => ({
    id:       r.channelId,
    name:     r.channelName,
    type:     r.channelType,
    parentId: r.parentCategoryId,
  })));
});

// ═══════════════════════════════════════════════════════════════
// GUILD ROLES (synced from bot on startup/join)
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/roles", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const rows = await db
    .select()
    .from(guildRolesTable)
    .where(eq(guildRolesTable.guildId, guildId));

  // Sort by position descending (highest position = most privileged, shown first)
  rows.sort((a, b) => b.position - a.position);

  res.json(rows.map((r) => ({
    id:       r.roleId,
    name:     r.roleName,
    position: r.position,
  })));
});

// ═══════════════════════════════════════════════════════════════
// LEADERBOARD DATA (from SQLite)
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/leaderboard/data", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    const topWealth = botDb.prepare(`
      SELECT discord_id, username, balance, rank, taxes_paid
      FROM users
      WHERE guild_id = ?
      ORDER BY balance DESC
      LIMIT 20
    `).all(guildId) as Array<{ discord_id: string; username: string; balance: number; rank: string; taxes_paid: number }>;

    botDb.close();
    res.json({ guildId, entries: topWealth });
  } catch {
    res.json({ guildId, entries: [] });
  }
});

// ═══════════════════════════════════════════════════════════════
// ASCENSION HISTORY (from SQLite)
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/ascension-history", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    const history = botDb.prepare(`
      SELECT discord_id, username, rank, ascended_at
      FROM ascension_history
      WHERE guild_id = ?
      ORDER BY ascended_at DESC
      LIMIT 50
    `).all(guildId) as Array<{ discord_id: string; username: string; rank: string; ascended_at: string }>;

    botDb.close();
    res.json({ guildId, history });
  } catch {
    res.json({ guildId, history: [] });
  }
});

// ═══════════════════════════════════════════════════════════════
// BOT STATUS — enriched (heartbeat, health, economy, commands)
// ═══════════════════════════════════════════════════════════════

const COMMANDS = [
  "grind","tribute","transfer","wealth","ascend",
  "invest","portfolio","withdraw","collect",
  "treasury","market","blackmarket","identity",
  "skins","equip-skin","titles","equip-title",
];

router.get("/guilds/:guildId/bot-status", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  // Offline fallback — returned on any hard error
  const offlineFallback = {
    botStatus:            "offline" as const,
    heartbeatState:       "lost"    as const,
    heartbeatAgeSeconds:  null      as number | null,
    guildCount:           0,
    uptimeSeconds:        0,
    lastHeartbeat:        null      as string | null,
    startedAt:            null      as string | null,
    discordGatewayStatus: "disconnected" as const,
    databaseStatus:       "error"   as const,
    apiSyncStatus:        "failed"  as const,
    schedulerStatus:      "stopped" as const,
    totalUsers:           0,
    activeUsers24h:       0,
    economySize:          0,
    treasuryValue:        0,
    grindCommands24h:     0,
    tributeTotal:         0,
    commands: COMMANDS.map((name) => ({ name, status: "unknown" as const })),
  };

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    // ── heartbeat ──────────────────────────────────────────────
    const hbRow  = botDb.prepare("SELECT value FROM meta WHERE key = ?").get("last_heartbeat") as { value: string } | undefined;
    const stRow  = botDb.prepare("SELECT value FROM meta WHERE key = ?").get("start_time")     as { value: string } | undefined;

    // ── guild-level counts ─────────────────────────────────────
    const guildCount = (botDb.prepare("SELECT COUNT(DISTINCT guild_id) AS cnt FROM users").get() as { cnt: number })?.cnt ?? 0;

    const econRow = botDb.prepare(`
      SELECT
        COUNT(*)                           AS totalUsers,
        COALESCE(SUM(balance), 0)          AS economySize,
        COALESCE(SUM(grind_count_24h), 0)  AS grindCommands24h,
        COALESCE(SUM(tribute_count), 0)    AS tributeTotal,
        COUNT(CASE WHEN grind_count_24h > 0 THEN 1 END) AS activeUsers24h
      FROM users
      WHERE guild_id = ?
    `).get(guildId) as any;

    const treasuryRow = botDb.prepare(
      "SELECT COALESCE(balance, 0) AS bal FROM treasury WHERE guild_id = ?"
    ).get(guildId) as { bal: number } | undefined;

    botDb.close();

    // ── derive status ──────────────────────────────────────────
    const lastHeartbeat     = hbRow?.value ?? null;
    const startedAt         = stRow?.value ?? null;
    const uptimeSeconds     = startedAt ? Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)) : 0;
    const heartbeatAgeMs    = lastHeartbeat ? (Date.now() - new Date(lastHeartbeat).getTime()) : Infinity;
    const heartbeatAgeSecs  = lastHeartbeat ? Math.floor(heartbeatAgeMs / 1000) : null;

    // Thresholds: ONLINE < 15s, DEGRADED 15–45s, OFFLINE > 45s
    let botStatus:      "online" | "degraded" | "offline";
    let heartbeatState: "live"   | "delayed"  | "lost";
    if (heartbeatAgeMs < 15_000) {
      botStatus = "online";   heartbeatState = "live";
    } else if (heartbeatAgeMs < 45_000) {
      botStatus = "degraded"; heartbeatState = "delayed";
    } else {
      botStatus = "offline";  heartbeatState = "lost";
    }

    const isAlive = botStatus !== "offline";

    res.json({
      botStatus,
      heartbeatState,
      heartbeatAgeSeconds:  heartbeatAgeSecs,
      guildCount,
      uptimeSeconds,
      lastHeartbeat,
      startedAt,
      discordGatewayStatus: isAlive ? "connected"    : "disconnected",
      databaseStatus:       "connected", // reached here = DB readable
      apiSyncStatus:        isAlive ? "ok"           : "degraded",
      schedulerStatus:      heartbeatAgeMs < 120_000 ? "running" : "stopped",
      totalUsers:           Number(econRow?.totalUsers     ?? 0),
      activeUsers24h:       Number(econRow?.activeUsers24h ?? 0),
      economySize:          Number(econRow?.economySize    ?? 0),
      treasuryValue:        Number(treasuryRow?.bal        ?? 0),
      grindCommands24h:     Number(econRow?.grindCommands24h ?? 0),
      tributeTotal:         Number(econRow?.tributeTotal   ?? 0),
      commands: COMMANDS.map((name) => ({
        name,
        status: isAlive ? "active" : "unknown",
      })),
    });
  } catch {
    res.json(offlineFallback);
  }
});

export default router;

