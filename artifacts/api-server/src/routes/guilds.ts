/**
 * GET /api/guilds
 * Returns the authenticated user's Discord guilds that they can administer,
 * enriched with bot-installed status.
 */
import { Router } from "express";
import {
  fetchUserGuilds,
  fetchBotGuildIds,
  hasAdminPermission,
  guildIconUrl,
} from "../lib/discord";
import { requireAuth } from "../lib/session";

const router = Router();

router.get("/guilds", requireAuth, async (req, res) => {
  const accessToken = req.session.accessToken;
  if (!accessToken) {
    res.status(401).json({ error: "No access token in session." });
    return;
  }

  try {
    const [userGuilds, botGuildIds] = await Promise.all([
      fetchUserGuilds(accessToken),
      fetchBotGuildIds(),
    ]);

    const eligible = userGuilds
      .filter((g) => hasAdminPermission(g.permissions, g.owner))
      .map((g) => ({
        id:           g.id,
        name:         g.name,
        icon:         g.icon,
        iconUrl:      guildIconUrl(g),
        memberCount:  g.approximate_member_count ?? null,
        botInstalled: botGuildIds.has(g.id),
      }));

    res.json({ guilds: eligible });
  } catch (err) {
    req.log.error({ err }, "Failed to fetch guilds");
    res.status(502).json({ error: "Failed to fetch guilds from Discord." });
  }
});

export default router;
