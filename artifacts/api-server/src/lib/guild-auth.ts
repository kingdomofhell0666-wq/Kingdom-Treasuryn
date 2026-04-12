import type { Request, Response, NextFunction } from "express";
import { logger } from "./logger";
import { fetchDiscordGuilds, hasManagePermission } from "./discord";

/** Guild access cache TTL: 5 minutes */
const GUILD_CACHE_TTL_MS = 5 * 60 * 1000;

/**
 * Middleware: validates that the authenticated user has Manage Guild (or Admin)
 * permission in the guild specified by `req.params.guildId`.
 *
 * Caches the list of authorized guild IDs in the session for GUILD_CACHE_TTL_MS
 * to avoid a Discord API call on every single request.
 */
export async function requireGuildAccess(
  req:  Request,
  res:  Response,
  next: NextFunction,
): Promise<void> {
  const { guildId } = req.params;

  if (!guildId) {
    res.status(400).json({ error: "Missing guild ID" });
    return;
  }

  if (!req.session.discordId) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }

  const now      = Date.now();
  const cacheAge = now - (req.session.guildsLastChecked ?? 0);
  const needsRefresh =
    !req.session.authorizedGuildIds || cacheAge > GUILD_CACHE_TTL_MS;

  if (needsRefresh) {
    try {
      const discordGuilds = await fetchDiscordGuilds(req.session.accessToken!);
      const eligible = discordGuilds
        .filter((g) => hasManagePermission(g.permissions))
        .map((g) => g.id);

      req.session.authorizedGuildIds = eligible;
      req.session.guildsLastChecked  = now;

      logger.debug(
        { userId: req.session.discordId, count: eligible.length },
        "Guild access cache refreshed",
      );
    } catch (err) {
      logger.warn({ err, userId: req.session.discordId }, "Failed to refresh guild cache");

      if (!req.session.authorizedGuildIds) {
        res.status(503).json({ error: "Could not verify guild access — try again" });
        return;
      }
      // Fall through with stale cache rather than denying valid users
    }
  }

  if (!req.session.authorizedGuildIds!.includes(guildId)) {
    logger.warn(
      { userId: req.session.discordId, guildId },
      "Unauthorized guild access attempt",
    );
    res.status(403).json({ error: "You do not have access to this guild" });
    return;
  }

  next();
}
