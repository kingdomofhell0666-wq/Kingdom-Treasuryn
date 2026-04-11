export interface CatalogItem {
  id: string;
  name: string;
  description: string;
  price_dc: number;
  rarity: "Default" | "Common" | "Uncommon" | "Rare" | "Epic" | "Legendary";
  min_rank?: string;
  theme_tag?: string;
  stat_icon?: string;
  color?: string;
  icon?: string;
  effect_desc?: string;
}

export interface Catalog {
  relics: CatalogItem[];
  titles: CatalogItem[];
  skins: CatalogItem[];
  badges: CatalogItem[];
}

export interface UserData {
  balance: number;
  rank: string;
  sacrifice_active: boolean;
  owned_relics: string[];
  owned_titles: string[];
  owned_skins: string[];
  owned_badges: string[];
  equipped_relic: string;
  equipped_title: string;
  equipped_skin: string;
  equipped_badges: string[];
}

export interface DiscordUser {
  id: string;
  username: string;
  discriminator: string;
  avatar: string | null;
  avatarUrl: string;
}

export type ItemCategory = "relics" | "titles" | "skins" | "badges";
export type ItemStatus = "available" | "owned" | "equipped" | "locked";

export const RANK_ORDER: Record<string, number> = {
  Forsaken: 0, Vermin: 1, Corrupted: 2, Folklore: 3, Mythology: 4,
  Demonology: 5, Eschatology: 6, Archangel: 7, Archdemon: 8,
  Knight: 9, Baron: 10, Viscount: 11, Count: 12, Marquis: 13,
  Duke: 14, Chancellor: 15,
};

export const RARITY_RANK: Record<string, number> = {
  Default: 0, Common: 1, Uncommon: 2, Rare: 3, Epic: 4, Legendary: 5,
};

export function getItemStatus(
  item: CatalogItem,
  category: ItemCategory,
  userData: UserData,
  userRankIdx: number,
): ItemStatus {
  const minRankIdx = item.min_rank ? (RANK_ORDER[item.min_rank] ?? 0) : 0;
  if (item.min_rank && userRankIdx < minRankIdx) return "locked";

  switch (category) {
    case "relics":
      if (userData.equipped_relic === item.id) return "equipped";
      if (userData.owned_relics.includes(item.id)) return "owned";
      break;
    case "titles":
      if (userData.equipped_title === item.id) return "equipped";
      if (userData.owned_titles.includes(item.id)) return "owned";
      break;
    case "skins":
      if (userData.equipped_skin === item.id) return "equipped";
      if (userData.owned_skins.includes(item.id)) return "owned";
      break;
    case "badges":
      if (userData.equipped_badges.includes(item.id)) return "equipped";
      if (userData.owned_badges.includes(item.id)) return "owned";
      break;
  }
  return "available";
}
