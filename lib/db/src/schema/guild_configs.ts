import { pgTable, text, integer, real, jsonb, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const guildConfigsTable = pgTable("guild_configs", {
  guildId:                text("guild_id").primaryKey(),
  currencyName:           text("currency_name").notNull().default("DevilCoins"),
  currencyIcon:           text("currency_icon").notNull().default("🪙"),
  timezone:               text("timezone").notNull().default("UTC"),
  grindCooldownSeconds:   integer("grind_cooldown_seconds").notNull().default(3600),
  tributeCooldownSeconds: integer("tribute_cooldown_seconds").notNull().default(86400),
  grindMinReward:         integer("grind_min_reward").notNull().default(50),
  grindMaxReward:         integer("grind_max_reward").notNull().default(500),
  tributeMinReward:       integer("tribute_min_reward").notNull().default(100),
  tributeMaxReward:       integer("tribute_max_reward").notNull().default(800),
  blackMarketRiskPct:     real("black_market_risk_pct").notNull().default(0.35),
  investmentTaxRate:      real("investment_tax_rate").notNull().default(0.08),
  commandRouting:         jsonb("command_routing").$type<Record<string, string>>().default({}),
  updatedAt:              timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export const insertGuildConfigSchema = createInsertSchema(guildConfigsTable);
export const selectGuildConfigSchema = createSelectSchema(guildConfigsTable);
export type GuildConfig = typeof guildConfigsTable.$inferSelect;
export type InsertGuildConfig = typeof guildConfigsTable.$inferInsert;
