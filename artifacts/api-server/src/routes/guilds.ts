/**
 * Guild routes:
 *  GET  /api/guilds               → list guilds user can manage (bot present + admin)
 *  GET  /api/guilds/:id           → full guild detail (channels + roles)
 *  GET  /api/guilds/:id/config    → per-guild bot config
 *  PATCH /api/guilds/:id/config   → update per-guild bot config
 *  GET  /api/guilds/:id/stats     → economy stats from SQLite bot DB
 *  GET  /api/guilds/:id/bot-status → bot online status + uptime
 */
import { Router } from "express";
import axios from "axios";
import {
  fetchUserGuilds,
  fetchBotGuildIds,
  fetchBotGuild,
  guildIconUrl,
  hasAdminPermission,
} from "../lib/discord";
import { requireAuth } from "../lib/session";
import { db, guildConfigsTable } from "@workspace/db";
import { eq } from "drizzle-orm";

const BOT_BASE = "https://discord.com/api/v10";
const botToken = () => process.env["DISCORD_BOT_TOKEN"] ?? "";

const router = Router();

// ── Helper: assert user is admin of a guild ──────────────────────────────────

async function assertGuildAdmin(req: import("express").Request, res: import("express").Response, guildId: string): Promise<boolean> {
  const accessToken = req.session.accessToken!;
  const userGuilds = await fetchUserGuilds(accessToken);
  const guild = userGuilds.find((g) => g.id === guildId);
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

// ── GET /guilds ───────────────────────────────────────────────────────────────

router.get("/guilds", requireAuth, async (req, res) => {
  try {
    const [userGuilds, botGuildIds] = await Promise.all([
      fetchUserGuilds(req.session.accessToken!),
      fetchBotGuildIds(),
    ]);

    const manageable = userGuilds.filter((g) =>
      hasAdminPermission(g.permissions, g.owner)
    );

    const result = manageable.map((g) => ({
      id:          g.id,
      name:        g.name,
      icon:        g.icon,
      iconUrl:     guildIconUrl(g),
      memberCount: g.approximate_member_count ?? 0,
      botPresent:  botGuildIds.has(g.id),
      isAdmin:     true,
    }));

    res.json(result);
  } catch (err) {
    req.log.error({ err }, "Failed to fetch guilds");
    res.status(500).json({ error: "Failed to fetch guilds from Discord." });
  }
});

// ── GET /guilds/:guildId ──────────────────────────────────────────────────────

router.get("/guilds/:guildId", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  const ok = await assertGuildAdmin(req, res, guildId);
  if (!ok) return;

  try {
    const botGuild = await fetchBotGuild(guildId);
    if (!botGuild) {
      res.status(404).json({ error: "Guild not found or bot is not present." });
      return;
    }

    // Fetch channels and roles via bot token
    const [chRes, roleRes] = await Promise.all([
      axios.get(`${BOT_BASE}/guilds/${guildId}/channels`, {
        headers: { Authorization: `Bot ${botToken()}` },
      }),
      axios.get(`${BOT_BASE}/guilds/${guildId}/roles`, {
        headers: { Authorization: `Bot ${botToken()}` },
      }),
    ]);

    type Channel = { id: string; name: string; type: number };
    type Role    = { id: string; name: string; color: number; position: number };

    const textChannels = (chRes.data as Channel[])
      .filter((c) => c.type === 0 || c.type === 5) // text + announcement
      .map((c) => ({ id: c.id, name: c.name, type: c.type }));

    const roles = (roleRes.data as Role[])
      .filter((r) => r.name !== "@everyone")
      .sort((a, b) => b.position - a.position)
      .map((r) => ({ id: r.id, name: r.name, color: r.color, position: r.position }));

    res.json({
      id:          botGuild.id,
      name:        botGuild.name,
      icon:        botGuild.icon,
      iconUrl:     guildIconUrl(botGuild),
      memberCount: botGuild.approximate_member_count ?? 0,
      channels:    textChannels,
      roles,
      botPresent:  true,
    });
  } catch (err) {
    req.log.error({ err }, "Failed to fetch guild detail");
    res.status(500).json({ error: "Failed to fetch guild details from Discord." });
  }
});

// ── GET /guilds/:guildId/config ───────────────────────────────────────────────

async function upsertConfig(guildId: string) {
  const existing = await db
    .select()
    .from(guildConfigsTable)
    .where(eq(guildConfigsTable.guildId, guildId))
    .limit(1);

  if (existing.length > 0) return existing[0];

  const [inserted] = await db
    .insert(guildConfigsTable)
    .values({ guildId })
    .returning();
  return inserted;
}

router.get("/guilds/:guildId/config", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  const ok = await assertGuildAdmin(req, res, guildId);
  if (!ok) return;

  try {
    const config = await upsertConfig(guildId);
    res.json(config);
  } catch (err) {
    req.log.error({ err }, "Failed to fetch guild config");
    res.status(500).json({ error: "Failed to fetch guild configuration." });
  }
});

// ── PATCH /guilds/:guildId/config ─────────────────────────────────────────────

router.patch("/guilds/:guildId/config", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  const ok = await assertGuildAdmin(req, res, guildId);
  if (!ok) return;

  try {
    await upsertConfig(guildId); // ensure row exists

    const allowed = [
      "currencyName", "currencyIcon", "timezone",
      "grindCooldownSeconds", "tributeCooldownSeconds",
      "grindMinReward", "grindMaxReward",
      "tributeMinReward", "tributeMaxReward",
      "blackMarketRiskPct", "investmentTaxRate",
      "commandRouting",
    ] as const;

    const patch: Record<string, unknown> = {};
    for (const key of allowed) {
      if (key in req.body) patch[key] = req.body[key];
    }
    patch["updatedAt"] = new Date();

    const [updated] = await db
      .update(guildConfigsTable)
      .set(patch as Parameters<typeof db.update>[0])
      .where(eq(guildConfigsTable.guildId, guildId))
      .returning();

    res.json(updated);
  } catch (err) {
    req.log.error({ err }, "Failed to update guild config");
    res.status(500).json({ error: "Failed to update configuration." });
  }
});

// ── GET /guilds/:guildId/stats ─────────────────────────────────────────────────
// Reads from the bot's SQLite DB file if present; otherwise returns zeroes.

router.get("/guilds/:guildId/stats", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  const ok = await assertGuildAdmin(req, res, guildId);
  if (!ok) return;

  try {
    // Attempt to read from the bot's SQLite DB
    let stats = {
      guildId,
      totalUsers: 0,
      totalWalletBalance: 0,
      totalTreasuryBalance: 0,
      totalTaxesPaid: 0,
      activeInvestments: 0,
      topRankName: null as string | null,
      topRankCount: 0,
    };

    try {
      const Database = (await import("better-sqlite3")).default;
      const botDb = new Database("kingdom_treasury.db", { readonly: true });

      const row = botDb.prepare(`
        SELECT
          COUNT(*)                AS totalUsers,
          COALESCE(SUM(balance), 0) AS totalWalletBalance,
          COALESCE(SUM(taxes_paid), 0) AS totalTaxesPaid
        FROM users
        WHERE guild_id = ?
      `).get(guildId) as any;

      const treasury = botDb.prepare(
        "SELECT COALESCE(balance, 0) AS bal FROM treasury WHERE guild_id = ?"
      ).get(guildId) as any;

      const investments = botDb.prepare(
        "SELECT COUNT(*) AS cnt FROM investments WHERE guild_id = ? AND status = 'active'"
      ).get(guildId) as any;

      const topRank = botDb.prepare(`
        SELECT rank, COUNT(*) AS cnt
        FROM users
        WHERE guild_id = ?
        GROUP BY rank
        ORDER BY cnt DESC
        LIMIT 1
      `).get(guildId) as any;

      botDb.close();

      stats = {
        guildId,
        totalUsers:          Number(row?.totalUsers ?? 0),
        totalWalletBalance:  Number(row?.totalWalletBalance ?? 0),
        totalTreasuryBalance: Number(treasury?.bal ?? 0),
        totalTaxesPaid:      Number(row?.totalTaxesPaid ?? 0),
        activeInvestments:   Number(investments?.cnt ?? 0),
        topRankName:         topRank?.rank ?? null,
        topRankCount:        Number(topRank?.cnt ?? 0),
      };
    } catch {
      // SQLite not available or DB not found — return zeroes
    }

    res.json(stats);
  } catch (err) {
    req.log.error({ err }, "Failed to fetch guild stats");
    res.status(500).json({ error: "Failed to fetch stats." });
  }
});

// ── GET /guilds/:guildId/bot-status ──────────────────────────────────────────

const BOT_START_TIME = Date.now();

router.get("/guilds/:guildId/bot-status", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  const ok = await assertGuildAdmin(req, res, guildId);
  if (!ok) return;

  try {
    const botGuild = await fetchBotGuild(guildId);
    const uptimeSeconds = Math.floor((Date.now() - BOT_START_TIME) / 1000);

    let guildCount = 0;
    try {
      const guildsRes = await axios.get(`${BOT_BASE}/users/@me/guilds`, {
        headers: { Authorization: `Bot ${botToken()}` },
      });
      guildCount = (guildsRes.data as unknown[]).length;
    } catch { /* ignore */ }

    res.json({
      online:         !!botGuild,
      guildCount,
      uptimeSeconds,
      lastHeartbeat:  new Date().toISOString(),
    });
  } catch (err) {
    req.log.error({ err }, "Failed to fetch bot status");
    res.status(500).json({ error: "Failed to fetch bot status." });
  }
});

export default router;
