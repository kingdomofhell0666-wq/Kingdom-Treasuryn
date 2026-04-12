/**
 * Express session middleware backed by PostgreSQL via connect-pg-simple.
 */
import session from "express-session";
import connectPgSimple from "connect-pg-simple";
import { pool } from "@workspace/db";

declare module "express-session" {
  interface SessionData {
    discordUser?: {
      id:            string;
      username:      string;
      discriminator: string;
      avatar:        string | null;
    };
    accessToken?:  string;
    oauthState?:   string;
    returnTo?:     string;
  }
}

const PgSession = connectPgSimple(session);

const SESSION_SECRET = process.env["SESSION_SECRET"];
if (!SESSION_SECRET) {
  throw new Error("SESSION_SECRET environment variable is required.");
}

export const sessionMiddleware = session({
  store: new PgSession({
    pool,
    tableName: "dashboard_sessions",
    createTableIfMissing: false,
  }),
  secret:            SESSION_SECRET,
  resave:            false,
  saveUninitialized: false,
  cookie: {
    secure:   process.env["NODE_ENV"] === "production",
    httpOnly: true,
    maxAge:   7 * 24 * 60 * 60 * 1000, // 7 days
    sameSite: "lax",
  },
});

export function requireAuth(
  req: import("express").Request,
  res: import("express").Response,
  next: import("express").NextFunction,
) {
  if (!req.session.discordUser) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  next();
}
