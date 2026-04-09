import { useGetGuild, useGetBotStatus, useGetGuildStats, getGetGuildQueryKey, getGetBotStatusQueryKey, getGetGuildStatsQueryKey } from "@workspace/api-client-react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, Users, Coins, TrendingUp, AlertTriangle, Clock, Server } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

export default function GuildDashboardPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-7xl mx-auto space-y-8">
          <DashboardHeader guildId={guildId} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <BotStatusCard guildId={guildId} />
            <EconomyStatsCards guildId={guildId} />
          </div>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function DashboardHeader({ guildId }: { guildId: string }) {
  const { data: guild, isLoading } = useGetGuild(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildQueryKey(guildId) }
  });

  if (isLoading) {
    return <div className="h-20 bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  if (!guild) return null;

  return (
    <div className="flex items-center gap-6 pb-6 border-b border-border/50">
      <div className="w-20 h-20 rounded-2xl bg-muted border border-primary/20 overflow-hidden shadow-[0_0_15px_rgba(220,38,38,0.2)]">
        {guild.iconUrl ? (
          <img src={guild.iconUrl} alt={guild.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-muted-foreground bg-card">
            {guild.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
      <div>
        <h1 className="text-3xl font-bold tracking-tight font-serif text-foreground">{guild.name}</h1>
        <p className="text-muted-foreground mt-1 flex items-center gap-2">
          <Server className="w-4 h-4" />
          {guild.memberCount?.toLocaleString() || 0} Members
        </p>
      </div>
    </div>
  );
}

function BotStatusCard({ guildId }: { guildId: string }) {
  const { data: status, isLoading, isError } = useGetBotStatus(guildId, {
    query: { enabled: !!guildId, queryKey: getGetBotStatusQueryKey(guildId), refetchInterval: 30000 }
  });

  if (isLoading) {
    return <div className="h-[140px] bg-card rounded-xl animate-pulse border border-border"></div>;
  }

  if (isError || !status) {
    return (
      <Card className="border-destructive/20 bg-destructive/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-destructive flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Bot Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">Offline</div>
        </CardContent>
      </Card>
    );
  }

  const uptimeDays = Math.floor(status.uptimeSeconds / 86400);
  const uptimeHours = Math.floor((status.uptimeSeconds % 86400) / 3600);

  return (
    <Card className="border-primary/20 bg-primary/5 shadow-[0_0_10px_rgba(220,38,38,0.05)]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-primary flex items-center gap-2">
          <Activity className="w-4 h-4" /> Bot Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
          <div className="text-2xl font-bold text-foreground">Online</div>
        </div>
        <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
          <Clock className="w-3 h-3" /> Uptime: {uptimeDays}d {uptimeHours}h
        </p>
      </CardContent>
    </Card>
  );
}

function EconomyStatsCards({ guildId }: { guildId: string }) {
  const { data: stats, isLoading } = useGetGuildStats(guildId, {
    query: { enabled: !!guildId, queryKey: getGetGuildStatsQueryKey(guildId) }
  });

  if (isLoading) {
    return (
      <>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-[140px] bg-card rounded-xl animate-pulse border border-border"></div>
        ))}
      </>
    );
  }

  if (!stats) return null;

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Users className="w-4 h-4 text-secondary" /> Active Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalUsers.toLocaleString()}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Coins className="w-4 h-4 text-secondary" /> Economy Size
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-secondary">
            {(stats.totalWalletBalance + stats.totalTreasuryBalance).toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Wallet: {stats.totalWalletBalance.toLocaleString()} | Treasury: {stats.totalTreasuryBalance.toLocaleString()}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" /> Active Investments
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.activeInvestments.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground mt-1 text-primary/80">
            Taxes collected: {stats.totalTaxesPaid.toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </>
  );
}