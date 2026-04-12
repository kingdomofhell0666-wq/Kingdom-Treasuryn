import { Users, Coins, TrendingUp, ShoppingCart, Trophy, Shield, ScrollText, Settings } from "lucide-react";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export function MembersPage() {
  return (
    <PlaceholderPage
      title="Members"
      description="View and manage all server members, their balances, and activity."
      icon={Users}
    />
  );
}

export function EconomyPage() {
  return (
    <PlaceholderPage
      title="Economy"
      description="Monitor currency flow, wallet balances, and treasury totals across the server."
      icon={Coins}
    />
  );
}

export function InvestmentsPage() {
  return (
    <PlaceholderPage
      title="Investments"
      description="Track active investments and their returns across all members."
      icon={TrendingUp}
    />
  );
}

export function BlackMarketPage() {
  return (
    <PlaceholderPage
      title="Black Market"
      description="Monitor black market activity, transactions, and risk statistics."
      icon={ShoppingCart}
    />
  );
}

export function LeaderboardPage() {
  return (
    <PlaceholderPage
      title="Leaderboard"
      description="See the top earners and most active members in your server."
      icon={Trophy}
    />
  );
}

export function RanksPage() {
  return (
    <PlaceholderPage
      title="Ranks"
      description="Configure rank roles, thresholds, and ascension settings."
      icon={Shield}
    />
  );
}

export function AuditLogPage() {
  return (
    <PlaceholderPage
      title="Audit Log"
      description="Review recent bot actions, admin commands, and configuration changes."
      icon={ScrollText}
    />
  );
}

export function SettingsPage() {
  return (
    <PlaceholderPage
      title="Settings"
      description="Configure currency name, cooldowns, rewards, tax rates, and command routing."
      icon={Settings}
    />
  );
}
