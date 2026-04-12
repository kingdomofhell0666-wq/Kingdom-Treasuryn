import session from "express-session";

export const sessionMiddleware = session({
  secret:            process.env["SESSION_SECRET"] ?? "dev-secret-change-me",
  resave:            false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure:   process.env["NODE_ENV"] === "production",
    maxAge:   7 * 24 * 60 * 60 * 1000,
  },
});
