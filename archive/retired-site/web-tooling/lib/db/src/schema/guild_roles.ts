import { pgTable, serial, text, integer, timestamp, unique } from "drizzle-orm/pg-core";

export const guildRolesTable = pgTable("guild_roles", {
  id:        serial("id").primaryKey(),
  guildId:   text("guild_id").notNull(),
  roleId:    text("role_id").notNull(),
  roleName:  text("role_name").notNull(),
  position:  integer("position").notNull().default(0),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (t) => [
  unique("guild_roles_guild_role_uq").on(t.guildId, t.roleId),
]);

export type GuildRole       = typeof guildRolesTable.$inferSelect;
export type InsertGuildRole = typeof guildRolesTable.$inferInsert;
