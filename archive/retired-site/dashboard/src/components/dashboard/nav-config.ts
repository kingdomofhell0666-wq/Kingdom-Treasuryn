import {
  LayoutDashboard,
  Users,
  Coins,
  TrendingUp,
  ShoppingCart,
  Trophy,
  Settings,
  Shield,
  ScrollText,
} from "lucide-react";
import { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  description?: string;
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: "Overview",
    path: "overview",
    icon: LayoutDashboard,
    description: "Server health and bot status",
  },
  {
    label: "Members",
    path: "members",
    icon: Users,
    description: "Manage server members",
  },
  {
    label: "Economy",
    path: "economy",
    icon: Coins,
    description: "Currency and balances",
  },
  {
    label: "Investments",
    path: "investments",
    icon: TrendingUp,
    description: "Investment tracking",
  },
  {
    label: "Black Market",
    path: "black-market",
    icon: ShoppingCart,
    description: "Black market activity",
  },
  {
    label: "Leaderboard",
    path: "leaderboard",
    icon: Trophy,
    description: "Top earners",
  },
  {
    label: "Ranks",
    path: "ranks",
    icon: Shield,
    description: "Role and rank management",
  },
  {
    label: "Audit Log",
    path: "audit-log",
    icon: ScrollText,
    description: "Recent actions",
  },
  {
    label: "Settings",
    path: "settings",
    icon: Settings,
    description: "Bot configuration",
  },
];
