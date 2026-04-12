import { Router } from "express";
import crypto from "crypto";
import { logger } from "../lib/logger";
import {
  exchangeCode, fetchDiscordUser,
  getRedirectUri, avatarUrl,
} from "../lib/discord";
import "../types";

const router = Router();

function generateState(): string {
  return crypto.randomBytes(20).toString("hex");
}

/** GET /api/auth/discord  →  redirect to Discord OAuth */
router.get("/discord", (req, res) => {
  const state = generateState();
  req.session.oauthState = state;

  const params = new URLSearchParams({
    client_id:     process.env["DISCORD_CLIENT_ID"] ?? "",
    redirect_uri:  getRedirectUri(),
    response_type: "code",
    scope:         "identify guilds",
    state,
    prompt:        "none",
  });

  res.redirect(`https://discord.com/api/oauth2/authorize?${params}`);
});

/** GET /api/auth/discord/callback  →  OAuth code exchange */
router.get("/discord/callback", async (req, res) => {
  const { code, state, error } = req.query as Record<string, string>;

  if (error) {
    logger.warn({ error }, "Discord OAuth denied by user");
    return res.redirect("/dashboard/?error=oauth_denied");
  }

  if (!code) {
    return res.redirect("/dashboard/?error=no_code");
  }

  if (!state || state !== req.session.oauthState) {
    logger.warn("OAuth state mismatch — possible CSRF");
    return res.redirect("/dashboard/?error=invalid_state");
  }

  try {
    const tokens = await exchangeCode(code);
    const user   = await fetchDiscordUser(tokens.access_token);

    req.session.discordId      = user.id;
    req.session.username       = user.username;
    req.session.globalName     = user.global_name ?? null;
    req.session.discriminator  = user.discriminator;
    req.session.avatar         = user.avatar;
    req.session.avatarUrl      = avatarUrl(user.id, user.avatar, user.discriminator);
    req.session.accessToken    = tokens.access_token;
    req.session.refreshToken   = tokens.refresh_token;
    req.session.tokenExpiresAt = Date.now() + tokens.expires_in * 1000;
    delete req.session.oauthState;

    await new Promise<void>((resolve, reject) =>
      req.session.save((err) => (err ? reject(err) : resolve()))
    );

    logger.info({ userId: user.id, username: user.username }, "User authenticated");
    res.redirect("/dashboard/guilds");
  } catch (err) {
    logger.error({ err }, "OAuth callback error");
    res.redirect("/dashboard/?error=oauth_failed");
  }
});

/** POST /api/auth/logout  →  destroy session */
router.post("/logout", (req, res) => {
  req.session.destroy((err) => {
    if (err) logger.warn({ err }, "Session destroy error");
    res.clearCookie("kt.sid");
    res.json({ ok: true });
  });
});

/** GET /api/auth/me  →  return session user (401 if not logged in) */
router.get("/me", (req, res) => {
  if (!req.session.discordId) {
    return res.status(401).json({ error: "Not authenticated" });
  }
  res.json({
    id:            req.session.discordId,
    username:      req.session.username,
    globalName:    req.session.globalName ?? null,
    discriminator: req.session.discriminator,
    avatar:        req.session.avatar,
    avatarUrl:     req.session.avatarUrl,
  });
});

export default router;
