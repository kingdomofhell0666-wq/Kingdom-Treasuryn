import {
  Activity, Coins, CircleDollarSign, Landmark, Share2, Shield,
  Crown, TrendingUp, ShoppingBag, Package, IdCard, Trophy, Zap,
  Settings, AlertTriangle,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

function make(
  pageTitle: string,
  icon: React.ComponentType<{ className?: string }>,
  title: string,
  description: string,
  badge?: string,
) {
  return function Page() {
    return (
      <DashboardLayout pageTitle={pageTitle}>
        <PlaceholderPage icon={icon as Parameters<typeof PlaceholderPage>[0]["icon"]} title={title} description={description} badge={badge} />
      </DashboardLayout>
    );
  };
}

export const BotStatusPage = make(
  "Bot Status",
  Activity,
  "Bot Status",
  "Monitor your Kingdom Treasury bot's connection, latency, and command health in real time.",
);

export const EconomyPage = make(
  "Economy",
  Coins,
  "Economy",
  "Configure rewards, sinks, daily yields, and infernal financial flow for your realm.",
);

export const CurrencyPage = make(
  "Currency",
  CircleDollarSign,
  "Currency",
  "Customise DevilCoin settings, conversion rates, and currency display options.",
);

export const TreasuryPage = make(
  "Treasury",
  Landmark,
  "Treasury",
  "Manage the Kingdom Treasury balance, tribute flow, and reserve allocation.",
);

export const RoutingPage = make(
  "Command Routing",
  Share2,
  "Command Routing",
  "Define which channels commands can be used in and configure routing rules across the server.",
);

export const PermissionsPage = make(
  "Permissions",
  Shield,
  "Permissions",
  "Set role-based access for bot commands and restrict sensitive actions to Kingdom staff.",
);

export const RanksPage = make(
  "Ranks & Roles",
  Crown,
  "Ranks & Roles",
  "Edit the Kingdom rank registry — titles, role mappings, thresholds, and hierarchy order.",
);

export const AscensionPage = make(
  "Ascension",
  TrendingUp,
  "Ascension",
  "Configure ascension eligibility rules, costs, and role promotion logic.",
);

export const MarketPage = make(
  "Market",
  ShoppingBag,
  "Market",
  "Browse and manage the infernal market — listings, pricing, and trade restrictions.",
);

export const InventoryPage = make(
  "Inventory",
  Package,
  "Inventory",
  "View and manage player inventory items, tradeable assets, and item metadata.",
);

export const IdentityPage = make(
  "Identity",
  IdCard,
  "Identity",
  "Configure player identity cards, profile display options, and cosmetic unlocks.",
);

export const KingdomRanksPage = make(
  "Kingdom Ranks",
  Trophy,
  "Kingdom Ranks",
  "Automate rank announcements, assign award roles, and manage the public leaderboard.",
);

export const AutomationPage = make(
  "Automation",
  Zap,
  "Automation",
  "Set up scheduled tasks, event triggers, and automated kingdom announcements.",
);

export const SettingsPage = make(
  "Settings",
  Settings,
  "Server Settings",
  "Manage bot configuration, log channels, and server-level preferences.",
);

export const ResetPage = make(
  "Reset / Maintenance",
  AlertTriangle,
  "Reset / Maintenance",
  "Perform dangerous maintenance actions — economy resets, data wipes, and emergency controls.",
  "Restricted",
);
