import { pgTable, serial, text, jsonb, timestamp } from "drizzle-orm/pg-core";

export const commandPermissionsTable = pgTable("command_permissions", {
  id:              serial("id").primaryKey(),
  guildId:         text("guild_id").notNull(),
  commandName:     text("command_name").notNull(),
  allowedRoles:    jsonb("allowed_roles").$type<string[]>().default([]),
  deniedRoles:     jsonb("denied_roles").$type<string[]>().default([]),
  allowedChannels: jsonb("allowed_channels").$type<string[]>().default([]),
  deniedChannels:  jsonb("denied_channels").$type<string[]>().default([]),
  updatedAt:       timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export type CommandPermissions    = typeof commandPermissionsTable.$inferSelect;
export type InsertCommandPermissions = typeof commandPermissionsTable.$inferInsert;
