import { pgTable, serial, text, boolean, timestamp } from "drizzle-orm/pg-core";

export const rankRoleMappingTable = pgTable("rank_role_mapping", {
  id:              serial("id").primaryKey(),
  guildId:         text("guild_id").notNull(),
  rankName:        text("rank_name").notNull(),
  roleId:          text("role_id").notNull(),
  removePrevious:  boolean("remove_previous").notNull().default(true),
  updatedAt:       timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export type RankRoleMapping    = typeof rankRoleMappingTable.$inferSelect;
export type InsertRankRoleMapping = typeof rankRoleMappingTable.$inferInsert;
