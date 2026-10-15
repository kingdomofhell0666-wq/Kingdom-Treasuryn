import { pgTable, serial, text, boolean, integer, timestamp } from "drizzle-orm/pg-core";

export const ascensionAnnouncementSettingsTable = pgTable("ascension_announcement_settings", {
  id:              serial("id").primaryKey(),
  guildId:         text("guild_id").notNull().unique(),
  enabled:         boolean("enabled").notNull().default(false),
  channelId:       text("channel_id"),
  messageTemplate: text("message_template").notNull().default("{user} has ascended to {rank} in the Kingdom of Hell! 🔥"),
  updatedAt:       timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export const rankCooldownSettingsTable = pgTable("rank_cooldown_settings", {
  id:              serial("id").primaryKey(),
  guildId:         text("guild_id").notNull(),
  rankName:        text("rank_name").notNull(),
  cooldownSeconds: integer("cooldown_seconds").notNull().default(0),
  updatedAt:       timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export type AscensionAnnouncementSettings    = typeof ascensionAnnouncementSettingsTable.$inferSelect;
export type InsertAscensionAnnouncementSettings = typeof ascensionAnnouncementSettingsTable.$inferInsert;
export type RankCooldownSettings    = typeof rankCooldownSettingsTable.$inferSelect;
export type InsertRankCooldownSettings = typeof rankCooldownSettingsTable.$inferInsert;
