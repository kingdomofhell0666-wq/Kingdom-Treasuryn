import { pgTable, serial, text, timestamp, unique } from "drizzle-orm/pg-core";

export const guildChannelsTable = pgTable("guild_channels", {
  id:               serial("id").primaryKey(),
  guildId:          text("guild_id").notNull(),
  channelId:        text("channel_id").notNull(),
  channelName:      text("channel_name").notNull(),
  channelType:      text("channel_type").notNull().default("text"),
  parentCategoryId: text("parent_category_id"),
  updatedAt:        timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (t) => [
  unique("guild_channels_guild_channel_uq").on(t.guildId, t.channelId),
]);

export type GuildChannel       = typeof guildChannelsTable.$inferSelect;
export type InsertGuildChannel = typeof guildChannelsTable.$inferInsert;
