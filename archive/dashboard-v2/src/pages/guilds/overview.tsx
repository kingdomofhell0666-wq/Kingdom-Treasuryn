import { useParams, useLocation } from "wouter";
import {
  Activity, Users, Coins, Landmark, Server, LayoutDashboard,
  TrendingUp, ShoppingBag, Trophy, Crown, ExternalLink,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { useGuild } from "@/context/guild-context";

function StatCard({
  icon: Icon, label, value, sub, color = "text-muted-foreground",
}: {
  icon: typeof Activity; label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex items-start gap-4">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${color === "text-emerald-400" ? "bg-emerald-400/10" : color === "text-primary" ? "bg-primary/10" : color === "text-amber-400" ? "bg-amber-400/10" : "bg-muted"}`}>
        <Icon className={`w-4.5 h-4.5 ${color}`} style={{ width: "1.125rem", height: "1.125rem" }} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground font-medium mb-0.5">{label}</p>
        <p className="text-xl font-bold text-foreground leading-none">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </div>
    </div>
  );
}

function QuickLink({
  icon: Icon, label, path,
}: {
  icon: typeof Activity; label: string; path: string;
}) {
  const [, navigate] = useLocation();
  return (
    <button
      onClick={() => navigate(path)}
      className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg border border-border bg-card hover:bg-accent hover:border-primary/30 transition-all group text-left"
    >
      <Icon className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
      <span className="text-sm font-medium text-foreground truncate">{label}</span>
      <ExternalLink className="w-3 h-3 text-muted-foreground/0 group-hover:text-muted-foreground/60 transition-colors ml-auto flex-shrink-0" />
    </button>
  );
}

function OverviewContent() {
  const { guildId } = useParams<{ guildId: string }>();
  const { guild, isLoading } = useGuild();
  const base = `/guilds/${guildId}`;

  const guildName = guild?.name ?? "Your Server";
  const memberCount = guild?.memberCount;

  return (
    <div className="max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        {isLoading ? (
          <div className="w-14 h-14 rounded-xl bg-muted animate-pulse" />
        ) : guild?.iconUrl ? (
          <img src={guild.iconUrl} alt={guild.name} className="w-14 h-14 rounded-xl object-cover flex-shrink-0" />
        ) : (
          <div className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-xl font-bold text-primary flex-shrink-0">
            {guildName[0]?.toUpperCase()}
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-2xl font-bold text-foreground truncate">{guildName}</h2>
          <div className="flex items-center gap-3 mt-1">
            {guild?.botInstalled && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Bot Active
              </span>
            )}
            {memberCount != null && (
              <span className="text-xs text-muted-foreground">
                {memberCount.toLocaleString()} members
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Activity}
          label="Bot Status"
          value={guild?.botInstalled ? "Connected" : "Not Installed"}
          sub={guild?.botInstalled ? "All systems operational" : "Add bot to this server"}
          color={guild?.botInstalled ? "text-emerald-400" : "text-muted-foreground"}
        />
        <StatCard
          icon={Users}
          label="Total Members"
          value={memberCount != null ? memberCount.toLocaleString() : "—"}
          sub="Discord member count"
          color="text-primary"
        />
        <StatCard
          icon={Coins}
          label="Economy Size"
          value="—"
          sub="Live data in Block 3"
          color="text-amber-400"
        />
        <StatCard
          icon={Landmark}
          label="Treasury Balance"
          value="—"
          sub="Live data in Block 3"
          color="text-amber-400"
        />
      </div>

      {/* Server summary + quick access */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Server summary */}
        <div className="lg:col-span-3 rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Server Summary</h3>
          </div>
          <div className="divide-y divide-border">
            {[
              { label: "Server Name",  value: guild?.name ?? "—" },
              { label: "Guild ID",     value: guildId ?? "—" },
              { label: "Member Count", value: memberCount != null ? memberCount.toLocaleString() : "—" },
              { label: "Bot Presence", value: guild?.botInstalled ? "Installed" : "Not installed" },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-2.5 gap-4">
                <span className="text-xs text-muted-foreground">{label}</span>
                <span className="text-xs font-medium text-foreground truncate text-right max-w-[60%]">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick access */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-3">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Quick Access</h3>
          </div>
          <div className="space-y-2">
            <QuickLink icon={Coins}      label="Economy"       path={`${base}/economy`} />
            <QuickLink icon={TrendingUp} label="Ascension"     path={`${base}/ascension`} />
            <QuickLink icon={ShoppingBag} label="Market"       path={`${base}/market`} />
            <QuickLink icon={Trophy}     label="Kingdom Ranks" path={`${base}/kingdom-ranks`} />
            <QuickLink icon={Crown}      label="Ranks & Roles" path={`${base}/ranks`} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OverviewPage() {
  return (
    <DashboardLayout pageTitle="Dashboard">
      <OverviewContent />
    </DashboardLayout>
  );
}
