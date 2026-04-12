/**
 * Bot Status — premium live control and monitoring page.
 *
 * Layout:
 *  1. Hero status card (pulse indicator, ONLINE / DEGRADED / OFFLINE)
 *  2. Live metrics grid (8 cards)
 *  3. System health (4 service status pills)
 *  4. Active commands (pill grid)
 *  5. Alert banner when degraded / offline
 *
 * Auto-refreshes every 10 seconds with a live countdown in the button.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { apiGet } from "@/lib/api";
import {
  Activity, AlertTriangle, CheckCircle2, XCircle, Clock, Server,
  Hash, Users, Coins, TrendingUp, Terminal, RefreshCcw, Wifi,
  WifiOff, Database, Zap, Shield, AlertCircle, Flame, Crown,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type StatusLevel = "online" | "degraded" | "offline";
type HbState     = "live" | "delayed" | "lost";
type ServiceOk   = "connected" | "ok" | "running";
type ServiceBad  = "disconnected" | "error" | "degraded" | "failed" | "stopped" | "unknown";
type ServiceStatus = ServiceOk | ServiceBad;

type BotCommand = { name: string; status: "active" | "unknown" };

type BotStatus = {
  botStatus:            StatusLevel;
  heartbeatState:       HbState;
  heartbeatAgeSeconds:  number | null;
  guildCount:           number;
  uptimeSeconds:        number;
  lastHeartbeat:        string | null;
  startedAt:            string | null;
  discordGatewayStatus: string;
  databaseStatus:       string;
  apiSyncStatus:        string;
  schedulerStatus:      string;
  totalUsers:           number;
  activeUsers24h:       number;
  economySize:          number;
  treasuryValue:        number;
  grindCommands24h:     number;
  tributeTotal:         number;
  commands:             BotCommand[];
};

// ─── Constants ────────────────────────────────────────────────────────────────

const AUTO_REFRESH_SECS = 10;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtUptime(s: number): string {
  if (!s) return "—";
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const parts: string[] = [];
  if (d) parts.push(`${d}d`);
  if (h) parts.push(`${h}h`);
  if (m) parts.push(`${m}m`);
  if (!parts.length) parts.push(`${s}s`);
  return parts.join(" ");
}

function fmtNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function fmtAge(seconds: number | null): string {
  if (seconds === null) return "No signal";
  if (seconds < 5)      return "just now";
  if (seconds < 60)     return `${seconds}s ago`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

function isOkStatus(s: string): boolean {
  return ["connected", "ok", "running"].includes(s);
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BotStatusPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-6xl mx-auto space-y-6">
          <PageHeader
            title="Bot Status"
            description="Live operational status of the Kingdom Treasury core."
          />
          <BotStatusDashboard guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── Dashboard orchestrator ───────────────────────────────────────────────────

function BotStatusDashboard({ guildId }: { guildId: string }) {
  const [data, setData]         = useState<BotStatus | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [countdown, setCountdown] = useState(AUTO_REFRESH_SECS);
  const [fetching, setFetching] = useState(false);

  // Live heartbeat-age ticker (updates every second without re-fetching)
  const [ageTicker, setAgeTicker] = useState(0);

  const load = useCallback(async (manual = false) => {
    if (manual) setFetching(true);
    setError(null);
    try {
      const d = await apiGet<BotStatus>(`/api/guilds/${guildId}/bot-status`);
      setData(d);
      setCountdown(AUTO_REFRESH_SECS);
      setAgeTicker(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load bot status.");
    } finally {
      setLoading(false);
      setFetching(false);
    }
  }, [guildId]);

  // Initial load
  useEffect(() => { load(); }, [load]);

  // Auto-refresh countdown + trigger
  useEffect(() => {
    const id = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { load(); return AUTO_REFRESH_SECS; }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [load]);

  // Local age ticker (so heartbeat age increments each second without an API call)
  useEffect(() => {
    const id = setInterval(() => setAgeTicker((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="w-4 h-4" />
        <AlertDescription className="flex items-center gap-4">
          {error}
          <Button size="sm" variant="outline" onClick={() => load(true)}>Retry</Button>
        </AlertDescription>
      </Alert>
    );
  }

  // Compute live heartbeat age (ticks locally every second between refreshes)
  const liveAgeSeconds = data?.heartbeatAgeSeconds !== null && data?.heartbeatAgeSeconds !== undefined
    ? data.heartbeatAgeSeconds + ageTicker
    : null;

  return (
    <div className="space-y-5">
      {/* Degraded / offline alert */}
      {data && data.botStatus !== "online" && (
        <StatusAlert status={data.botStatus} />
      )}

      {/* ── Hero card ─────────────────────────────────────────── */}
      <HeroCard
        data={data!}
        liveAgeSeconds={liveAgeSeconds}
        countdown={countdown}
        fetching={fetching}
        onRefresh={() => load(true)}
      />

      {/* ── Metrics grid ──────────────────────────────────────── */}
      <MetricsGrid data={data!} liveAgeSeconds={liveAgeSeconds} />

      {/* ── Lower row: health + commands ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div className="lg:col-span-2">
          <SystemHealthCard data={data!} />
        </div>
        <div className="lg:col-span-3">
          <ActiveCommandsCard data={data!} />
        </div>
      </div>
    </div>
  );
}

// ─── Alert banner ─────────────────────────────────────────────────────────────

function StatusAlert({ status }: { status: StatusLevel }) {
  if (status === "degraded") {
    return (
      <Alert className="border-amber-500/40 bg-amber-500/10">
        <AlertTriangle className="w-4 h-4 text-amber-400" />
        <AlertDescription className="text-amber-300">
          <strong>The Core is delayed.</strong> Some live metrics may be outdated. The heartbeat signal has not been received recently.
        </AlertDescription>
      </Alert>
    );
  }
  return (
    <Alert variant="destructive">
      <AlertCircle className="w-4 h-4" />
      <AlertDescription>
        <strong>The Core is not responding.</strong> Dashboard data may be stale. The bot heartbeat signal has been lost.
      </AlertDescription>
    </Alert>
  );
}

// ─── Hero card ────────────────────────────────────────────────────────────────

function HeroCard({
  data, liveAgeSeconds, countdown, fetching, onRefresh,
}: {
  data: BotStatus;
  liveAgeSeconds: number | null;
  countdown: number;
  fetching: boolean;
  onRefresh: () => void;
}) {
  const { botStatus, heartbeatState } = data;

  const statusConfig = {
    online: {
      dot:   "bg-emerald-500",
      ping:  "bg-emerald-400",
      badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      card:  "border-emerald-500/20 bg-emerald-500/5",
      label: "ONLINE",
      desc:  "Core response is stable. All systems nominal.",
    },
    degraded: {
      dot:   "bg-amber-500",
      ping:  "bg-amber-400",
      badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      card:  "border-amber-500/20 bg-amber-500/5",
      label: "DEGRADED",
      desc:  "Heartbeat signal is delayed. Monitoring for recovery.",
    },
    offline: {
      dot:   "bg-destructive",
      ping:  "bg-destructive/60",
      badge: "bg-destructive/15 text-destructive border-destructive/30",
      card:  "border-destructive/20 bg-destructive/5",
      label: "OFFLINE",
      desc:  "No heartbeat received. The Core is not responding.",
    },
  }[botStatus];

  const hbConfig = {
    live:    { label: "LIVE",    color: "text-emerald-400" },
    delayed: { label: "DELAYED", color: "text-amber-400" },
    lost:    { label: "LOST",    color: "text-destructive" },
  }[heartbeatState];

  return (
    <Card className={cn("border transition-colors", statusConfig.card)}>
      <CardContent className="p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
          {/* Pulse indicator */}
          <div className="flex-shrink-0">
            <span className="relative flex h-16 w-16">
              {botStatus !== "offline" && (
                <span className={cn(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-30",
                  statusConfig.ping,
                )} />
              )}
              <span className={cn(
                "relative inline-flex h-16 w-16 rounded-full items-center justify-center",
                botStatus === "online"   && "bg-emerald-500/10 border border-emerald-500/30",
                botStatus === "degraded" && "bg-amber-500/10 border border-amber-500/30",
                botStatus === "offline"  && "bg-destructive/10 border border-destructive/30",
              )}>
                {botStatus === "offline"
                  ? <WifiOff className="w-7 h-7 text-destructive" />
                  : <Wifi    className={cn("w-7 h-7", botStatus === "online" ? "text-emerald-400" : "text-amber-400")} />}
              </span>
            </span>
          </div>

          {/* Identity + status */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold font-serif text-foreground">Kingdom Treasury</h2>
              <Badge className={cn("text-xs font-bold tracking-wider px-2.5 py-0.5", statusConfig.badge)}>
                {statusConfig.label}
              </Badge>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-sm">
              {/* Heartbeat state */}
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Heartbeat:</span>
                <span className={cn("font-semibold", hbConfig.color)}>{hbConfig.label}</span>
                {liveAgeSeconds !== null && (
                  <span className="text-muted-foreground text-xs">· {fmtAge(liveAgeSeconds)}</span>
                )}
              </div>
            </div>

            <p className="text-xs text-muted-foreground mt-2">{statusConfig.desc}</p>
          </div>

          {/* Refresh button + countdown */}
          <div className="flex-shrink-0 flex flex-col items-end gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={fetching}
              className="gap-2 min-w-[110px]"
            >
              <RefreshCcw className={cn("w-3.5 h-3.5", fetching && "animate-spin")} />
              {fetching ? "Loading…" : `Refresh (${countdown}s)`}
            </Button>
            <span className="text-xs text-muted-foreground">Auto-refreshes every {AUTO_REFRESH_SECS}s</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Metrics grid ─────────────────────────────────────────────────────────────

function MetricsGrid({ data, liveAgeSeconds }: { data: BotStatus; liveAgeSeconds: number | null }) {
  // Next Monday 00:00 UTC countdown
  const [secsToReset, setSecsToReset] = useState(0);
  useEffect(() => {
    function calc() {
      const now  = new Date();
      const day  = now.getUTCDay(); // 0=Sun, 1=Mon
      const daysAhead = day === 0 ? 1 : 8 - day;
      const next = new Date(now);
      next.setUTCDate(now.getUTCDate() + daysAhead);
      next.setUTCHours(0, 0, 0, 0);
      setSecsToReset(Math.max(0, Math.floor((next.getTime() - now.getTime()) / 1000)));
    }
    calc();
    const id = setInterval(calc, 1000);
    return () => clearInterval(id);
  }, []);

  function fmtReset(s: number) {
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  const metrics = [
    {
      icon:  Hash,
      label: "Guild Servers",
      value: data.guildCount ? `${data.guildCount}` : "—",
      sub:   "Discord servers connected",
      accent: false,
    },
    {
      icon:  Clock,
      label: "Uptime",
      value: fmtUptime(data.uptimeSeconds),
      sub:   data.startedAt
        ? `Since ${new Date(data.startedAt).toLocaleDateString("en-US", { month: "short", day: "numeric" })}`
        : "Since last restart",
      accent: data.uptimeSeconds > 3600,
    },
    {
      icon:  Activity,
      label: "Last Heartbeat",
      value: fmtAge(liveAgeSeconds),
      sub:   `State: ${data.heartbeatState.toUpperCase()}`,
      accent: data.heartbeatState === "live",
      warn:   data.heartbeatState !== "live",
    },
    {
      icon:  Users,
      label: "Active Today",
      value: data.activeUsers24h ? `${data.activeUsers24h}` : "—",
      sub:   `of ${data.totalUsers.toLocaleString()} total members`,
      accent: false,
    },
    {
      icon:  Coins,
      label: "Economy Size",
      value: data.economySize ? `${fmtNumber(data.economySize)} DC` : "—",
      sub:   "Total wallet balance",
      accent: false,
    },
    {
      icon:  TrendingUp,
      label: "Treasury",
      value: data.treasuryValue ? `${fmtNumber(data.treasuryValue)} DC` : "—",
      sub:   "Kingdom treasury balance",
      accent: false,
    },
    {
      icon:  Terminal,
      label: "Grinds (24h)",
      value: data.grindCommands24h ? `${data.grindCommands24h.toLocaleString()}` : "—",
      sub:   "Grind commands executed today",
      accent: false,
    },
    {
      icon:  Crown,
      label: "KR Reset In",
      value: fmtReset(secsToReset),
      sub:   "Next Monday 00:00 UTC",
      accent: secsToReset < 86400, // highlight last 24h
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4">
      {metrics.map((m) => (
        <MetricCard key={m.label} {...m} />
      ))}
    </div>
  );
}

function MetricCard({
  icon: Icon, label, value, sub, accent, warn,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
  warn?: boolean;
}) {
  return (
    <Card className={cn(
      "border-border/50 transition-colors",
      accent && "border-primary/20 bg-primary/5",
      warn   && "border-amber-500/20 bg-amber-500/5",
    )}>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon className={cn(
            "w-4 h-4",
            accent ? "text-primary"  : "",
            warn   ? "text-amber-400" : "",
            !accent && !warn ? "text-muted-foreground" : "",
          )} />
          <span className="text-xs font-medium text-muted-foreground truncate">{label}</span>
        </div>
        <div className={cn(
          "text-xl sm:text-2xl font-bold font-mono leading-tight",
          accent ? "text-primary"  : "text-foreground",
          warn   ? "text-amber-400" : "",
        )}>
          {value}
        </div>
        {sub && <p className="text-xs text-muted-foreground mt-1 leading-tight">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ─── System Health card ───────────────────────────────────────────────────────

function SystemHealthCard({ data }: { data: BotStatus }) {
  const services = [
    {
      icon:  Wifi,
      label: "Discord Gateway",
      status: data.discordGatewayStatus,
    },
    {
      icon:  Database,
      label: "Database",
      status: data.databaseStatus,
    },
    {
      icon:  Server,
      label: "API Sync",
      status: data.apiSyncStatus,
    },
    {
      icon:  Zap,
      label: "Scheduler",
      status: data.schedulerStatus,
    },
  ];

  return (
    <Card className="border-border/50 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Shield className="w-4 h-4 text-primary" />
          System Health
        </CardTitle>
        <CardDescription>Core service status indicators</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {services.map((s) => (
          <ServiceRow key={s.label} icon={s.icon} label={s.label} status={s.status} />
        ))}
      </CardContent>
    </Card>
  );
}

function ServiceRow({
  icon: Icon, label, status,
}: {
  icon: React.ElementType;
  label: string;
  status: string;
}) {
  const ok = isOkStatus(status);
  const statusLabel = {
    connected:    "Connected",
    disconnected: "Disconnected",
    ok:           "OK",
    degraded:     "Degraded",
    failed:       "Failed",
    running:      "Running",
    stopped:      "Stopped",
    error:        "Error",
    unknown:      "Unknown",
  }[status] ?? status;

  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2.5 min-w-0">
        <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <span className="text-sm text-foreground/80 truncate">{label}</span>
      </div>
      <div className={cn(
        "flex items-center gap-1.5 text-xs font-semibold px-2 py-1 rounded-full border shrink-0",
        ok
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
          : "bg-destructive/10 text-destructive border-destructive/25",
      )}>
        {ok
          ? <CheckCircle2 className="w-3 h-3" />
          : <XCircle      className="w-3 h-3" />}
        {statusLabel}
      </div>
    </div>
  );
}

// ─── Active Commands card ─────────────────────────────────────────────────────

function ActiveCommandsCard({ data }: { data: BotStatus }) {
  const isAlive = data.botStatus !== "offline";

  return (
    <Card className="border-border/50 h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Terminal className="w-4 h-4 text-primary" />
              Active Commands
            </CardTitle>
            <CardDescription>
              {isAlive
                ? `${data.commands.filter((c) => c.status === "active").length} commands registered and active`
                : "Command status unavailable — bot offline"}
            </CardDescription>
          </div>
          {isAlive && (
            <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/25 text-xs">
              All Active
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {data.commands.map((cmd) => (
            <CommandPill key={cmd.name} name={cmd.name} status={cmd.status} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function CommandPill({ name, status }: { name: string; status: string }) {
  const active = status === "active";
  return (
    <div className={cn(
      "inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border font-mono transition-colors",
      active
        ? "bg-muted/40 border-border/60 text-foreground/80 hover:border-primary/30 hover:bg-primary/5"
        : "bg-muted/20 border-border/30 text-muted-foreground/50",
    )}>
      <span className={cn(
        "w-1.5 h-1.5 rounded-full shrink-0",
        active ? "bg-emerald-500" : "bg-muted-foreground/30",
      )} />
      /{name}
    </div>
  );
}
