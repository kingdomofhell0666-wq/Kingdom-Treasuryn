import "../types";
import { Router, type Request, type Response, type NextFunction } from "express";
import { logger } from "../lib/logger";
import { fetchDiscordGuilds, hasManagePermission, guildIconUrl } from "../lib/discord";
import { pool } from "../lib/db";

const router = Router();

/** Middleware: require authenticated session */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.session.discordId) {
    return res.status(401).json({ error: "Not authenticated" });
  }
  next();
}

/** GET /api/guilds  →  user's eligible guilds with bot-installed flag */
router.get("/", requireAuth, async (req, res) => {
  try {
    const discordGuilds = await fetchDiscordGuilds(req.session.accessToken!);

    // Filter to guilds where user can manage
    const eligible = discordGuilds.filter((g) =>
      hasManagePermission(g.permissions)
    );

    // Determine which guilds have the bot installed from our DB
    let botGuildIds = new Set<string>();
    try {
      const result = await pool.query<{ guild_id: string }>(
        "SELECT DISTINCT guild_id FROM guild_channels"
      );
      botGuildIds = new Set(result.rows.map((r) => r.guild_id));
    } catch (err) {
      logger.warn({ err }, "Could not query bot guild IDs — showing all as not installed");
    }

    const guilds = eligible.map((g) => ({
      id:           g.id,
      name:         g.name,
      icon:         g.icon,
      iconUrl:      guildIconUrl(g.id, g.icon),
      memberCount:  g.approximate_member_count ?? null,
      botInstalled: botGuildIds.has(g.id),
    }));

    // Sort: bot-installed first, then alphabetical
    guilds.sort((a, b) => {
      if (a.botInstalled !== b.botInstalled) return a.botInstalled ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

    res.json({ guilds });
  } catch (err) {
    logger.error({ err }, "Failed to fetch guilds");
    res.status(502).json({ error: "Failed to fetch guilds from Discord" });
  }
});

export default router;
