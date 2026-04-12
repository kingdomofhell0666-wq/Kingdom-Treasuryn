import {
  useGetGuild, useGetBotStatus, useGetGuildStats,
  getGetGuildQueryKey, getGetBotStatusQueryKey, getGetGuildStatsQueryKey,
} from "@workspace/api-client-react";
import { useParams } from "wouter";
import { Link } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Activity, Users, Coins, TrendingUp, AlertTriangle, Clock,
  Server, Wifi, WifiOff, Crown, ShoppingBag, ArrowUpCircle, Trophy,
  Hash, ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function GuildDashboardPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
          <PageHeader
            title="Overview"
            description="A live snapshot of your server's infernal economy."
          />

          {/* Stat cards row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <BotStatusCard guildId={guildId} />
            <EconomyStatsCards guildId={guildId} />
          </div>

          {/* Secondary row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ServerSummaryCard guildId={guildId} />
            </div>
            <QuickAccessCard guildId={guildId} />
          </div>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── Stat Cards ──────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  variant = "default",
}: {
  title: string;
  value: React.ReactNode;
  sub?: string;
  icon: React.ElementType;
  variant?: "default" | "primary" | "success";
}) {
  return (
    <Card
      className={cn(
        "border transition-colors",
        variant === "primary" && "border-primary/20 bg-primary/5",
        variant === "success" && "border-emerald-500/20 bg-emerald-500/5",
        variant === "default" && "border-border/50",
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-muted-foreground">{title}</span>
          <div
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              variant === "primary" && "bg-primary/10",
              variant === "success" && "bg-emerald-500/10",
              variant === "default" && "bg-muted/60",
            )}
          >
            <Icon
              className={cn(
                "w-4 h-4",
                variant === "primary" && "text-primary",
                variant === "success" && "text-emerald-500",
                variant === "default" && "text-muted-foreground",
              )}
            />
          </div>
        </div>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1 truncate">{sub}</p>}
      </CardContent>
    </Card>
  );
}

function BotStatusCard({ guildId }: { guildId: string }) {
  const { data: status, isLoading, isError } = useGetBotStatus(guildId, {
    query: { enabled: !!guildId, queryKey: getGetBotStatusQueryKey(guildId), refetchInterval: 30000 },
  });

  if (isLoading) return <div className="h-[108px] bg-card rounded-xl animate-pulse border border-border/40" />;

  if (isError || !status) {
    return (
      <StatCard
        title="Bot Status"
        value={
          <span className="flex items-center gap-2 text-destructive">
            <WifiOff className="w-5 h-5" /> Offline
          </span>
        }
        icon={AlertTriangle}
        variant="primary"
      />
    );
  }

  const d = Math.floor(status.uptimeSeconds / 86400);
  const h = Math.floor((status.uptimeSeconds % 86400) / 3600);

  return (
    <StatCard
      title="Bot Status"
      value={
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.7)]" />
          Online
        </span>
      }
      sub={`Uptime ${d}d ${h}h`}
      icon={Wifi}
      variant="success"
    />
  );
}

function EconomyStatsCards({ guildId }: { guildId: string }) {
  const { data: stats, isLoading } = useGetGuildStats(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildStatsQueryKey(guildId) },
  });

  if (isLoading) {
    return (
      <>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-[108px] bg-card rounded-xl animate-pulse border border-border/40" />
        ))}
      </>
    );
  }

  if (!stats) {
    return (
      <>
        <StatCard title="Active Users" value="—" icon={Users} />
        <StatCard title="Economy Size" value="—" sub="DC in circulation" icon={Coins} />
        <StatCard title="Investments" value="—" icon={TrendingUp} />
      </>
    );
  }

  const totalEconomy = stats.totalWalletBalance + stats.totalTreasuryBalance;

  return (
    <>
      <StatCard
        title="Active Users"
        value={stats.totalUsers.toLocaleString()}
        sub="Registered in economy"
        icon={Users}
      />
      <StatCard
        title="Economy Size"
        value={totalEconomy.toLocaleString()}
        sub={`Wallet ${stats.totalWalletBalance.toLocaleString()} · Treasury ${stats.totalTreasuryBalance.toLocaleString()}`}
        icon={Coins}
        variant="primary"
      />
      <StatCard
        title="Active Investments"
        value={stats.activeInvestments.toLocaleString()}
        sub={`${stats.totalTaxesPaid.toLocaleString()} DC collected in taxes`}
        icon={TrendingUp}
      />
    </>
  );
}

// ─── Server Summary ──────────────────────────────────────────────────────────

function ServerSummaryCard({ guildId }: { guildId: string }) {
  const { data: guild, isLoading } = useGetGuild(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildQueryKey(guildId) },
  });
  const { data: status } = useGetBotStatus(guildId, {
    query: { enabled: !!guildId, queryKey: getGetBotStatusQueryKey(guildId) },
  });

  if (isLoading) {
    return <div className="h-[200px] bg-card rounded-xl animate-pulse border border-border/40" />;
  }

  if (!guild) return null;

  const rows: { label: string; value: string }[] = [
    { label: "Server ID",    value: guildId },
    { label: "Members",      value: guild.memberCount?.toLocaleString() ?? "—" },
    { label: "Bot Presence", value: guild.botPresent ? "Installed" : "Not installed" },
    { label: "Last Heartbeat",
      value: status?.lastHeartbeat
        ? new Date(status.lastHeartbeat).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        : "—",
    },
  ];

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
          <Server className="w-4 h-4 text-muted-foreground" />
          Server Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0">
        <div className="flex items-center gap-4 mb-5">
          <div className="w-14 h-14 rounded-xl bg-muted border border-border/60 overflow-hidden flex-shrink-0 flex items-center justify-center font-bold text-xl text-muted-foreground">
            {guild.iconUrl ? (
              <img src={guild.iconUrl} alt={guild.name} className="w-full h-full object-cover" />
            ) : (
              guild.name.charAt(0).toUpperCase()
            )}
          </div>
          <div>
            <p className="font-bold text-foreground text-lg leading-tight">{guild.name}</p>
            {guild.botPresent && (
              <Badge variant="outline" className="mt-1.5 text-emerald-500 border-emerald-500/30 bg-emerald-500/5 text-[10px]">
                Bot Active
              </Badge>
            )}
          </div>
        </div>

        <div className="divide-y divide-border/40 rounded-lg border border-border/40 overflow-hidden">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between px-3 py-2.5 text-sm">
              <span className="text-muted-foreground text-xs">{row.label}</span>
              <span className="font-medium text-foreground text-xs font-mono truncate max-w-[160px]">{row.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Quick Access ─────────────────────────────────────────────────────────────

const QUICK_LINKS = [
  { label: "Economy",       href: "/economy",       icon: Coins,          desc: "Tune grind & tribute rewards" },
  { label: "Ascension",     href: "/ascension",     icon: ArrowUpCircle,  desc: "Rank-up thresholds & costs" },
  { label: "Market",        href: "/market",        icon: ShoppingBag,    desc: "Skins, titles & relics" },
  { label: "Kingdom Ranks", href: "/kingdom-ranks", icon: Trophy,         desc: "Weekly leaderboard tiers" },
  { label: "Ranks & Roles", href: "/ranks",         icon: Crown,          desc: "Role-to-rank bindings" },
  { label: "Leaderboard",   href: "/leaderboard",   icon: Hash,           desc: "Automated posting config" },
];

function QuickAccessCard({ guildId }: { guildId: string }) {
  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
          <Activity className="w-4 h-4 text-muted-foreground" />
          Quick Access
        </CardTitle>
        <CardDescription className="text-xs">Jump to any section instantly.</CardDescription>
      </CardHeader>
      <CardContent className="p-3 pt-0 space-y-1">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.href}
            href={`/guilds/${guildId}${link.href}`}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-muted/50 transition-colors group"
          >
            <div className="w-7 h-7 rounded-md bg-muted/60 border border-border/50 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/10 group-hover:border-primary/20 transition-colors">
              <link.icon className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-foreground leading-tight">{link.label}</p>
              <p className="text-[10px] text-muted-foreground/60 truncate">{link.desc}</p>
            </div>
            <ExternalLink className="w-3 h-3 text-muted-foreground/30 group-hover:text-muted-foreground/60 flex-shrink-0 transition-colors" />
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
