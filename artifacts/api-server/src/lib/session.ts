import session from "express-session";
import connectPg from "connect-pg-simple";
import { pool } from "./db";

const PgStore = connectPg(session);

export const sessionMiddleware = session({
  store: new PgStore({
    pool,
    tableName:            "dashboard_sessions",
    createTableIfMissing: true,
    ttl:                  7 * 24 * 60 * 60, // 7 days in seconds
    disableTouch:         false,
  }),
  secret:            process.env["SESSION_SECRET"] ?? "dev-secret-change-me",
  resave:            false,
  saveUninitialized: false,
  name:              "kt.sid",
  cookie: {
    httpOnly: true,
    secure:   process.env["NODE_ENV"] === "production",
    maxAge:   7 * 24 * 60 * 60 * 1000,
    sameSite: "lax",
  },
});
