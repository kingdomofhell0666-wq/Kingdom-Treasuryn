import { pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

export const currencyAssetsTable = pgTable("currency_assets", {
  id:         serial("id").primaryKey(),
  guildId:    text("guild_id").notNull(),
  fileUrl:    text("file_url").notNull(),
  uploadedAt: timestamp("uploaded_at", { withTimezone: true }).defaultNow(),
});

export type CurrencyAsset    = typeof currencyAssetsTable.$inferSelect;
export type InsertCurrencyAsset = typeof currencyAssetsTable.$inferInsert;
