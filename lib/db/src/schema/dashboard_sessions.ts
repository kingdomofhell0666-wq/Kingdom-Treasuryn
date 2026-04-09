import { pgTable, text, jsonb, timestamp } from "drizzle-orm/pg-core";

export const dashboardSessionsTable = pgTable("dashboard_sessions", {
  sid:       text("sid").primaryKey(),
  sess:      jsonb("sess").notNull(),
  expire:    timestamp("expire", { withTimezone: true }).notNull(),
});
