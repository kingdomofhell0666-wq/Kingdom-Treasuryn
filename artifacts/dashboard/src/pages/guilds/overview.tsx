import { useEffect } from "react";
import { useParams, useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Bot,
  Clock,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Wifi,
  WifiOff,
  Minus,
} from "lucide-react";
import { api, BotStatus, Guild } from "@/lib/api";
import { useGuild } from "@/context/guild-context";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function formatLastSeen(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 5) return "Just now";
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function StatusBadge({ online, lastHeartbeat }: { online: boolean; lastHeartbeat: string | null }) {
  const diff = lastHeartbeat
    ? Math.floor((Date.now() - new Date(lastHeartbeat).getTime()) / 1000)
    : 999;

  let status: "online" | "degraded" | "offline";
  if (diff < 15) status = "online";
  else if (diff < 45) status = "degraded";
  else status = "offline";

  const configs = {
    online: {
      icon: CheckCircle2,
      label: "Online",
      className: "text-emerald-400 bg-emerald-400/10",
    },
    degraded: {
      icon: Minus,
      label: "Degraded",
      className: "text-yellow-400 bg-yellow-400/10",
    },
    offline: {
      icon: XCircle,
      label: "Offline",
      className: "text-red-400 bg-red-400/10",
    },
  };

  const { icon: Icon, label, className } = configs[status];

  return (
    <span className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium", className)}>
      <Icon className="w-4 h-4" />
      {label}
    </span>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  iconColor = "text-primary",
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  iconColor?: string;
}) {
  return (
    <div className="bg-card border border-card-border rounded-xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10">
          <Icon className={cn("w-5 h-5", iconColor)} />
        </div>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

export default function OverviewPage() {
  const { guildId } = useParams<{ guildId: string }>();
  const { activeGuild, setActiveGuild } = useGuild();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [, setLocation] = useLocation();

  const { data: botStatus, isLoading, isError, refetch, isFetching } = useQuery<BotStatus>({
    queryKey: ["guilds", guildId, "bot-status"],
    queryFn: () => api.guilds.botStatus(guildId!),
    enabled: !!guildId && isAuthenticated,
    refetchInterval: 15000,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      setLocation("/");
    }
  }, [isAuthenticated, authLoading, setLocation]);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Overview</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Server health and bot status
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", isFetching && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="w-10 h-10 text-destructive mb-3" />
          <p className="font-medium text-foreground mb-1">Failed to load bot status</p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors mt-3"
          >
            <RefreshCw className="w-4 h-4" />
            Try again
          </button>
        </div>
      )}

      {/* Content */}
      {!isLoading && !isError && botStatus && (
        <>
          {/* Bot status card */}
          <div className="bg-card border border-card-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10">
                  <Bot className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">Kingdom Treasury Bot</p>
                  <p className="text-xs text-muted-foreground">Bot heartbeat monitor</p>
                </div>
              </div>
              <StatusBadge online={botStatus.online} lastHeartbeat={botStatus.lastHeartbeat} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-border">
              <div className="flex items-center gap-2 text-sm">
                {botStatus.online ? (
                  <Wifi className="w-4 h-4 text-emerald-400" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-400" />
                )}
                <span className="text-muted-foreground">Status:</span>
                <span className={cn("font-medium", botStatus.online ? "text-emerald-400" : "text-red-400")}>
                  {botStatus.online ? "Connected" : "Disconnected"}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">Last seen:</span>
                <span className="font-medium text-foreground">
                  {formatLastSeen(botStatus.lastHeartbeat)}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Activity className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">Uptime:</span>
                <span className="font-medium text-foreground">
                  {formatUptime(botStatus.uptimeSeconds)}
                </span>
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard
              icon={Bot}
              label="Servers"
              value={botStatus.guildCount.toString()}
              sub="Servers the bot is in"
            />
            <StatCard
              icon={Clock}
              label="Uptime"
              value={formatUptime(botStatus.uptimeSeconds)}
              sub="Since last restart"
            />
            <StatCard
              icon={Activity}
              label="Heartbeat"
              value={botStatus.lastHeartbeat ? formatLastSeen(botStatus.lastHeartbeat) : "N/A"}
              sub="Last bot ping received"
              iconColor={botStatus.online ? "text-emerald-400" : "text-red-400"}
            />
          </div>
        </>
      )}
    </div>
  );
}
