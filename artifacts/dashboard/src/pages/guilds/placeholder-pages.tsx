import {
  Activity, Coins, CircleDollarSign, Landmark, Share2, Shield,
  Crown, TrendingUp, ShoppingBag, Package, IdCard, Trophy, Zap,
  Settings, AlertTriangle,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";
import type { LucideIcon } from "lucide-react";

function makePage(
  pageTitle: string,
  icon: LucideIcon,
  title: string,
  description: string,
  badge?: string,
  badgeColor?: "default" | "red",
) {
  return function Page() {
    return (
      <DashboardLayout pageTitle={pageTitle}>
        <PlaceholderPage
          icon={icon}
          title={title}
          description={description}
          badge={badge}
          badgeColor={badgeColor}
        />
      </DashboardLayout>
    );
  };
}

export const BotStatusPage = makePage(
  "Bot Status", Activity, "Bot Status",
  "Monitor your Kingdom Treasury bot's connection, latency, and command health in real time.",
);

export const EconomyPage = makePage(
  "Economy", Coins, "Economy",
  "Configure grind rewards, tribute yields, sinks, and infernal financial flow for your realm.",
);

export const CurrencyPage = makePage(
  "Currency", CircleDollarSign, "Currency",
  "Customise DevilCoin display settings, currency name, icon, and conversion parameters.",
);

export const TreasuryPage = makePage(
  "Treasury", Landmark, "Treasury",
  "Monitor and manage the Kingdom Treasury balance, tribute flow, and reserve allocation.",
);

export const RoutingPage = makePage(
  "Command Routing", Share2, "Command Routing",
  "Define which channels each bot command can be used in across your server.",
);

export const PermissionsPage = makePage(
  "Permissions", Shield, "Permissions",
  "Set role-based access control for each bot command. Restrict sensitive actions to Kingdom staff.",
);

export const RanksPage = makePage(
  "Ranks & Roles", Crown, "Ranks & Roles",
  "Edit the Kingdom rank registry — role mappings, ascension costs, tax rates, and hierarchy order.",
);

export const AscensionPage = makePage(
  "Ascension", TrendingUp, "Ascension",
  "Configure ascension cooldowns, eligibility rules, role promotion logic, and announcement settings.",
);

export const MarketPage = makePage(
  "Market", ShoppingBag, "Market",
  "Browse the infernal market catalog — skins, titles, relics, and badges available to players.",
);

export const InventoryPage = makePage(
  "Inventory", Package, "Inventory",
  "View player inventory — owned cosmetic items, active relics, and equipped badge loadouts.",
);

export const IdentityPage = makePage(
  "Identity", IdCard, "Identity",
  "Configure player identity card display options and inspect equipped cosmetic states.",
);

export const KingdomRanksPage = makePage(
  "Kingdom Ranks", Trophy, "Kingdom Ranks",
  "Manage automated leaderboard posts, weekly rank announcements, and scoring configuration.",
);

export const AutomationPage = makePage(
  "Automation", Zap, "Automation",
  "Set up scheduled tasks, event triggers, and automated kingdom announcements.",
);

export const SettingsPage = makePage(
  "Settings", Settings, "Server Settings",
  "Manage bot configuration, log channels, and server-level behaviour preferences.",
);

export const ResetPage = makePage(
  "Reset / Maintenance", AlertTriangle, "Reset / Maintenance",
  "Perform dangerous maintenance actions — economy resets, data wipes, and emergency controls.",
  "Restricted", "red",
);
