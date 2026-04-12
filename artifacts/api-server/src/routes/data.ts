/**
 * Live-data read routes (Block 3):
 *
 *  GET /api/ranks
 *    → Canonical rank registry (name, cost, taxRate, purchasable,
 *      group, defaultCooldownSeconds).  No auth required — public metadata.
 *
 *  GET /api/guilds/:guildId/kingdom-ranks/data
 *    → Current weekly Kingdom Ranks leaderboard from bot SQLite.
 *      Ordered: weekly_active_seconds DESC → weekly_dc_earned DESC → rank index ASC.
 *      Returns top-10 rows plus metadata (week start, next reset Monday 00:00 UTC).
 *
 *  GET /api/guilds/:guildId/market-summary
 *    → Cosmetics ownership stats across the guild (owned/equipped skins,
 *      titles, relics, badges) read from bot SQLite.
 *
 *  GET /api/guilds/:guildId/inventory-summary
 *    → Per-user cosmetic engagement stats (counts with any cosmetic).
 */

import { Router } from "express";
import { requireAuth } from "../lib/session";
import { assertGuildAdmin } from "../lib/discord";

const router = Router();

// ─── Rank index map (mirrors bot/services/rank_service.py) ───────────────────
// Order matters: index 0 = Forsaken, index 15 = Chancellor.
// Used by kingdom-ranks endpoint to resolve rank tier as tiebreaker.

const RANK_INDEX: Record<string, number> = {
  Forsaken: 0, Vermin: 1, Corrupted: 2, Folklore: 3, Mythology: 4,
  Demonology: 5, Eschatology: 6, Archangel: 7, Archdemon: 8,
  Knight: 9, Baron: 10, Viscount: 11, Count: 12, Marquis: 13,
  Duke: 14, Chancellor: 15,
};

// ═══════════════════════════════════════════════════════════════
// GET /api/ranks — public rank registry
// ═══════════════════════════════════════════════════════════════

const RANK_REGISTRY = [
  { name: "Forsaken",    cost: 0,           taxRate: 0.12, purchasable: false, group: "economy",  defaultCooldownSeconds: 0 },
  { name: "Vermin",      cost: 1_500,        taxRate: 0.11, purchasable: true,  group: "economy",  defaultCooldownSeconds: 900 },
  { name: "Corrupted",   cost: 6_000,        taxRate: 0.10, purchasable: true,  group: "economy",  defaultCooldownSeconds: 1800 },
  { name: "Folklore",    cost: 15_000,       taxRate: 0.09, purchasable: true,  group: "economy",  defaultCooldownSeconds: 3600 },
  { name: "Mythology",   cost: 35_000,       taxRate: 0.09, purchasable: true,  group: "economy",  defaultCooldownSeconds: 7200 },
  { name: "Demonology",  cost: 80_000,       taxRate: 0.08, purchasable: true,  group: "economy",  defaultCooldownSeconds: 14400 },
  { name: "Eschatology", cost: 160_000,      taxRate: 0.08, purchasable: true,  group: "economy",  defaultCooldownSeconds: 28800 },
  { name: "Archangel",   cost: 400_000,      taxRate: 0.07, purchasable: true,  group: "economy",  defaultCooldownSeconds: 43200 },
  { name: "Archdemon",   cost: 1_000_000,    taxRate: 0.06, purchasable: true,  group: "economy",  defaultCooldownSeconds: 86400 },
  { name: "Knight",      cost: 2_500_000,    taxRate: 0.05, purchasable: true,  group: "nobility", defaultCooldownSeconds: 172800 },
  { name: "Baron",       cost: 5_000_000,    taxRate: 0.04, purchasable: true,  group: "nobility", defaultCooldownSeconds: 259200 },
  { name: "Viscount",    cost: 10_000_000,   taxRate: 0.03, purchasable: true,  group: "nobility", defaultCooldownSeconds: 432000 },
  { name: "Count",       cost: 20_000_000,   taxRate: 0.03, purchasable: true,  group: "nobility", defaultCooldownSeconds: 604800 },
  { name: "Marquis",     cost: 40_000_000,   taxRate: 0.02, purchasable: true,  group: "nobility", defaultCooldownSeconds: 864000 },
  { name: "Duke",        cost: 80_000_000,   taxRate: 0.01, purchasable: true,  group: "nobility", defaultCooldownSeconds: 1209600 },
  { name: "Chancellor",  cost: 0,            taxRate: 0.00, purchasable: false, group: "staff",    defaultCooldownSeconds: 0 },
];

router.get("/ranks", (_req, res) => {
  res.json(RANK_REGISTRY);
});

// ═══════════════════════════════════════════════════════════════
// GET /api/guilds/:guildId/kingdom-ranks/data
// Weekly Kingdom Ranks leaderboard + schedule metadata
// ═══════════════════════════════════════════════════════════════

/** Return the most recent past Monday at 00:00:00 UTC */
function lastMondayUtc(): Date {
  const now = new Date();
  const day = now.getUTCDay(); // 0 = Sunday, 1 = Monday …
  const daysBack = day === 0 ? 6 : day - 1;
  const monday = new Date(now);
  monday.setUTCDate(now.getUTCDate() - daysBack);
  monday.setUTCHours(0, 0, 0, 0);
  return monday;
}

/** Return the next Monday at 00:00:00 UTC (including today if it IS Monday and not yet midnight) */
function nextMondayUtc(): Date {
  const monday = lastMondayUtc();
  monday.setUTCDate(monday.getUTCDate() + 7);
  return monday;
}

function fmtDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

router.get("/guilds/:guildId/kingdom-ranks/data", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const weekStart  = lastMondayUtc();
  const nextReset  = nextMondayUtc();
  const now        = new Date();
  const secsToReset = Math.max(0, Math.floor((nextReset.getTime() - now.getTime()) / 1000));

  const empty = {
    weekStart:    weekStart.toISOString(),
    nextReset:    nextReset.toISOString(),
    secsToReset,
    totalEligible: 0,
    topUsers: [] as unknown[],
  };

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    // Top-10 weekly ranking:
    //   1. weekly_active_seconds DESC   (primary — most active in voice/text)
    //   2. weekly_dc_earned DESC        (secondary — most DC earned this week)
    //   3. RANK_INDEX ASC via CASE      (tertiary tiebreaker — higher tier wins)
    // Staff/authority roles are excluded by the bot at reset time (they don't
    // accumulate weekly stats), so no server-side role filtering needed here.
    const rows = botDb.prepare(`
      SELECT
        discord_id,
        username,
        rank,
        balance,
        weekly_active_seconds,
        weekly_dc_earned,
        CASE rank
          WHEN 'Duke'        THEN 14
          WHEN 'Marquis'     THEN 13
          WHEN 'Count'       THEN 12
          WHEN 'Viscount'    THEN 11
          WHEN 'Baron'       THEN 10
          WHEN 'Knight'      THEN 9
          WHEN 'Archdemon'   THEN 8
          WHEN 'Archangel'   THEN 7
          WHEN 'Eschatology' THEN 6
          WHEN 'Demonology'  THEN 5
          WHEN 'Mythology'   THEN 4
          WHEN 'Folklore'    THEN 3
          WHEN 'Corrupted'   THEN 2
          WHEN 'Vermin'      THEN 1
          ELSE 0
        END AS rank_tier
      FROM users
      WHERE guild_id = ?
        AND (weekly_active_seconds > 0 OR weekly_dc_earned > 0)
      ORDER BY
        weekly_active_seconds DESC,
        weekly_dc_earned DESC,
        rank_tier DESC
      LIMIT 10
    `).all(guildId) as Array<{
      discord_id: string;
      username: string;
      rank: string;
      balance: number;
      weekly_active_seconds: number;
      weekly_dc_earned: number;
      rank_tier: number;
    }>;

    const countRow = botDb.prepare(`
      SELECT COUNT(*) AS cnt
      FROM users
      WHERE guild_id = ?
        AND (weekly_active_seconds > 0 OR weekly_dc_earned > 0)
    `).get(guildId) as { cnt: number };

    botDb.close();

    const topUsers = rows.map((r, i) => ({
      position:            i + 1,
      discordId:           r.discord_id,
      username:            r.username,
      economyRank:         r.rank,
      weeklyActiveSeconds: r.weekly_active_seconds,
      weeklyActiveFmt:     fmtDuration(r.weekly_active_seconds),
      weeklyDcEarned:      r.weekly_dc_earned,
      balance:             r.balance,
    }));

    res.json({
      weekStart:     weekStart.toISOString(),
      nextReset:     nextReset.toISOString(),
      secsToReset,
      totalEligible: Number(countRow?.cnt ?? 0),
      topUsers,
    });
  } catch {
    // SQLite not available — return empty state
    res.json(empty);
  }
});

// ═══════════════════════════════════════════════════════════════
// GET /api/guilds/:guildId/market-summary
// Cosmetics ownership stats across the guild
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/market-summary", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  const empty = {
    guildId,
    totalUsers: 0,
    usersWithSkins: 0,
    usersWithTitles: 0,
    usersWithRelics: 0,
    usersWithBadges: 0,
    totalOwnedSkins: 0,
    totalOwnedTitles: 0,
    mostPopularRank: null as string | null,
  };

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    const row = botDb.prepare(`
      SELECT
        COUNT(*)                                    AS totalUsers,
        SUM(CASE WHEN equipped_skin IS NOT NULL AND equipped_skin != '' THEN 1 ELSE 0 END) AS usersWithSkins,
        SUM(CASE WHEN equipped_title IS NOT NULL AND equipped_title != '' THEN 1 ELSE 0 END) AS usersWithTitles,
        SUM(CASE WHEN equipped_relic IS NOT NULL AND equipped_relic != '' THEN 1 ELSE 0 END) AS usersWithRelics,
        SUM(CASE WHEN equipped_badges != '[]' AND equipped_badges != '' THEN 1 ELSE 0 END) AS usersWithBadges
      FROM users
      WHERE guild_id = ?
    `).get(guildId) as any;

    const skinCount = botDb.prepare(`
      SELECT SUM(json_array_length(owned_skins)) AS total
      FROM users
      WHERE guild_id = ? AND owned_skins != '[]' AND owned_skins != ''
    `).get(guildId) as any;

    const titleCount = botDb.prepare(`
      SELECT SUM(json_array_length(owned_titles)) AS total
      FROM users
      WHERE guild_id = ? AND owned_titles != '[]' AND owned_titles != ''
    `).get(guildId) as any;

    const topRank = botDb.prepare(`
      SELECT rank, COUNT(*) AS cnt
      FROM users
      WHERE guild_id = ?
      GROUP BY rank
      ORDER BY cnt DESC
      LIMIT 1
    `).get(guildId) as any;

    botDb.close();

    res.json({
      guildId,
      totalUsers:      Number(row?.totalUsers ?? 0),
      usersWithSkins:  Number(row?.usersWithSkins ?? 0),
      usersWithTitles: Number(row?.usersWithTitles ?? 0),
      usersWithRelics: Number(row?.usersWithRelics ?? 0),
      usersWithBadges: Number(row?.usersWithBadges ?? 0),
      totalOwnedSkins:  Number(skinCount?.total ?? 0),
      totalOwnedTitles: Number(titleCount?.total ?? 0),
      mostPopularRank: topRank?.rank ?? null,
    });
  } catch {
    res.json(empty);
  }
});

// ═══════════════════════════════════════════════════════════════
// GET /api/guilds/:guildId/inventory-summary
// Per-user cosmetic engagement summary
// ═══════════════════════════════════════════════════════════════

router.get("/guilds/:guildId/inventory-summary", requireAuth, async (req, res) => {
  const { guildId } = req.params;
  if (!(await assertGuildAdmin(req, res, guildId))) return;

  try {
    const Database = (await import("better-sqlite3")).default;
    const botDb    = new Database("kingdom_treasury.db", { readonly: true });

    const rows = botDb.prepare(`
      SELECT
        discord_id,
        username,
        rank,
        balance,
        equipped_skin,
        equipped_title,
        equipped_relic,
        equipped_badges,
        owned_skins,
        owned_titles
      FROM users
      WHERE guild_id = ?
        AND (
          equipped_skin IS NOT NULL AND equipped_skin != ''
          OR equipped_title IS NOT NULL AND equipped_title != ''
          OR equipped_relic IS NOT NULL AND equipped_relic != ''
          OR equipped_badges != '[]' AND equipped_badges != ''
        )
      ORDER BY balance DESC
      LIMIT 20
    `).all(guildId) as Array<{
      discord_id: string;
      username: string;
      rank: string;
      balance: number;
      equipped_skin: string | null;
      equipped_title: string | null;
      equipped_relic: string | null;
      equipped_badges: string;
      owned_skins: string;
      owned_titles: string;
    }>;

    const totalRow = botDb.prepare(`
      SELECT COUNT(*) AS cnt
      FROM users
      WHERE guild_id = ?
        AND (
          equipped_skin IS NOT NULL AND equipped_skin != ''
          OR equipped_title IS NOT NULL AND equipped_title != ''
          OR equipped_relic IS NOT NULL AND equipped_relic != ''
          OR equipped_badges != '[]' AND equipped_badges != ''
        )
    `).get(guildId) as { cnt: number };

    botDb.close();

    const users = rows.map((r) => {
      let badgeCount = 0;
      let skinCount  = 0;
      let titleCount = 0;
      try { badgeCount = JSON.parse(r.equipped_badges || "[]").length; } catch {}
      try { skinCount  = JSON.parse(r.owned_skins     || "[]").length; } catch {}
      try { titleCount = JSON.parse(r.owned_titles    || "[]").length; } catch {}
      return {
        discordId:     r.discord_id,
        username:      r.username,
        rank:          r.rank,
        balance:       r.balance,
        equippedSkin:  r.equipped_skin   || null,
        equippedTitle: r.equipped_title  || null,
        equippedRelic: r.equipped_relic  || null,
        badgeCount,
        ownedSkins:    skinCount,
        ownedTitles:   titleCount,
      };
    });

    res.json({
      guildId,
      totalWithCosmetics: Number(totalRow?.cnt ?? 0),
      users,
    });
  } catch {
    res.json({ guildId, totalWithCosmetics: 0, users: [] });
  }
});

export default router;
