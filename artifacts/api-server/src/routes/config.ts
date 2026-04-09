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
} from "@workspace/db";
import { eq, and } from "drizzle-orm";
import {
  fetchUserGuilds,
  fetchBotGuildIds,
  hasAdminPermission,
} from "../lib/discord";

const router = Router();

// ── Auth helper ───────────────────────────────────────────────────────────────

async function assertGuildAdmin(
  req: import("express").Request,
  res: import("express").Response,
  guildId: string
): Promise<boolean> {
  const accessToken = req.session.accessToken!;
  const userGuilds  = await fetchUserGuilds(accessToken);
  const guild       = userGuilds.find((g) => g.id === guildId);
  if (!guild) {
    res.status(403).json({ error: "You are not a member of this guild." });
    return false;
  }
  if (!hasAdminPermission(guild.permissions, guild.owner)) {
    res.status(403).json({ error: "Administrator permission required." });
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
    "enabled", "leaderboardType", "postFrequency",
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
// BOT STATUS (from SQLite + process check)
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/bot-status", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    const meta = botDb.prepare(`
      SELECT value FROM meta WHERE key = ?
    `).get("last_heartbeat") as { value: string } | undefined;

    const guildCount = botDb.prepare(`
      SELECT COUNT(DISTINCT guild_id) as cnt FROM users
    `).get() as { cnt: number };

    const startTime = botDb.prepare(`
      SELECT value FROM meta WHERE key = ?
    `).get("start_time") as { value: string } | undefined;

    botDb.close();

    const lastHeartbeat = meta?.value ?? new Date().toISOString();
    const startedAt = startTime?.value ? new Date(startTime.value).getTime() : Date.now();
    const uptimeSeconds = Math.floor((Date.now() - startedAt) / 1000);

    const heartbeatAge = Date.now() - new Date(lastHeartbeat).getTime();
    const online = heartbeatAge < 60_000;

    res.json({
      online,
      guildCount: guildCount?.cnt ?? 0,
      uptimeSeconds: Math.max(0, uptimeSeconds),
      lastHeartbeat,
    });
  } catch {
    res.json({
      online: false,
      guildCount: 0,
      uptimeSeconds: 0,
      lastHeartbeat: new Date().toISOString(),
    });
  }
});

export default router;

