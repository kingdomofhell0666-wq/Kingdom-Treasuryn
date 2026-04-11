/**
 * Discord OAuth2 authentication routes:
 *  GET  /api/auth/discord          → redirect to Discord
 *  GET  /api/auth/discord/callback → exchange code, store session
 *  POST /api/auth/logout           → clear session
 *  GET  /api/auth/me               → return current user
 */
import { Router } from "express";
import crypto from "crypto";
import {
  buildOAuthUrl,
  exchangeCode,
  fetchMe,
  avatarUrl,
} from "../lib/discord";
import { requireAuth } from "../lib/session";

const router = Router();

// GET /auth/discord — kick off OAuth flow
router.get("/auth/discord", (req, res) => {
  const state = crypto.randomBytes(16).toString("hex");
  req.session.oauthState = state;

  // Store return destination (only allow relative paths starting with /)
  const returnTo = req.query.returnTo as string | undefined;
  if (returnTo && returnTo.startsWith("/")) {
    req.session.returnTo = returnTo;
  }

  const url = buildOAuthUrl(state);
  res.redirect(url);
});

// GET /auth/discord/callback — Discord redirects back here
router.get("/auth/discord/callback", async (req, res) => {
  const { code, error, state } = req.query as Record<string, string>;

  const domains = process.env["REPLIT_DOMAINS"] ?? process.env["REPLIT_DEV_DOMAIN"] ?? "localhost:80";
  const primary = domains.split(",")[0]?.trim() ?? "localhost:80";
  const dashboardBase = primary.includes("localhost")
    ? `http://${primary}/dashboard`
    : `https://${primary}/dashboard`;

  if (error) {
    req.log.warn({ error }, "Discord OAuth error");
    res.redirect(`${dashboardBase}/?error=discord_denied`);
    return;
  }

  if (!code) {
    res.redirect(`${dashboardBase}/?error=missing_code`);
    return;
  }

  // CSRF state check
  if (state !== req.session.oauthState) {
    res.redirect(`${dashboardBase}/?error=state_mismatch`);
    return;
  }
  delete req.session.oauthState;

  try {
    const tokens = await exchangeCode(code);
    const user   = await fetchMe(tokens.access_token);

    req.session.discordUser = {
      id:            user.id,
      username:      user.global_name ?? user.username,
      discriminator: user.discriminator,
      avatar:        user.avatar,
    };
    req.session.accessToken = tokens.access_token;

    // Redirect to stored returnTo (exchange, dashboard, etc.)
    const returnTo = req.session.returnTo;
    delete req.session.returnTo;

    if (returnTo && returnTo.startsWith("/")) {
      res.redirect(returnTo);
    } else {
      res.redirect(`${dashboardBase}/guilds`);
    }
  } catch (err) {
    req.log.error({ err }, "OAuth exchange failed");
    res.redirect(`${dashboardBase}/?error=auth_failed`);
  }
});

// POST /auth/logout
router.post("/auth/logout", requireAuth, (req, res) => {
  req.session.destroy(() => {
    res.clearCookie("connect.sid");
    res.json({ ok: true });
  });
});

// GET /auth/me
router.get("/auth/me", requireAuth, (req, res) => {
  const u = req.session.discordUser!;
  res.json({
    id:            u.id,
    username:      u.username,
    discriminator: u.discriminator,
    avatar:        u.avatar,
    avatarUrl:     u.avatar
      ? `https://cdn.discordapp.com/avatars/${u.id}/${u.avatar}.png?size=128`
      : `https://cdn.discordapp.com/embed/avatars/${Number(u.discriminator) % 5}.png`,
  });
});

export default router;
