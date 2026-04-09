import { pgTable, serial, text, boolean, integer, timestamp } from "drizzle-orm/pg-core";

export const leaderboardSettingsTable = pgTable("leaderboard_settings", {
  id:               serial("id").primaryKey(),
  guildId:          text("guild_id").notNull().unique(),
  enabled:          boolean("enabled").notNull().default(false),
  leaderboardType:  text("leaderboard_type").notNull().default("wealth"),
  postFrequency:    text("post_frequency").notNull().default("daily"),
  postChannelId:    text("post_channel_id"),
  postHour:         integer("post_hour").notNull().default(12),
  postMinute:       integer("post_minute").notNull().default(0),
  postDayOfWeek:    integer("post_day_of_week"),
  postDayOfMonth:   integer("post_day_of_month"),
  timezone:         text("timezone").notNull().default("UTC"),
  lastPostedAt:     timestamp("last_posted_at", { withTimezone: true }),
  updatedAt:        timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export type LeaderboardSettings    = typeof leaderboardSettingsTable.$inferSelect;
export type InsertLeaderboardSettings = typeof leaderboardSettingsTable.$inferInsert;
