import { pgTable, serial, text, boolean, timestamp } from "drizzle-orm/pg-core";

export const commandRoutingTable = pgTable("command_routing", {
  id:          serial("id").primaryKey(),
  guildId:     text("guild_id").notNull(),
  commandName: text("command_name").notNull(),
  channelId:   text("channel_id"),
  isGlobal:    boolean("is_global").notNull().default(true),
  updatedAt:   timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export type CommandRouting    = typeof commandRoutingTable.$inferSelect;
export type InsertCommandRouting = typeof commandRoutingTable.$inferInsert;
