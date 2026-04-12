import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "wouter";
import {
  Activity, RefreshCw, Server, Clock, Zap, Database,
  Calendar, AlertTriangle, Wifi, WifiOff, Minus,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { apiGet } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

type BotStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

interface HeartbeatData {
  guildCount:        number | null;
  uptimeSeconds:     number | null;
  latencyMs:         number | null;
  schedulerStatus:   string | null;
  dbStatus:          string | null;
  botUsername:       string | null;
  botUserId:         string | null;
  commandCountToday: number | null;
  writtenAt:         string | null;
}

interface BotStatusResponse {
  status:        BotStatus;
  heartbeatAge:  number | null;  // seconds
  apiStatus:     "ok" | "error";
  dbStatus:      "ok" | "error";
  heartbeat:     HeartbeatData | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatUptime(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatAge(seconds: number | null | undefined): string {
  if (seconds == null) return "never";
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

const STATUS_CONFIG = {
  ONLINE:   { label: "Online",   color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", ring: "bg-emerald-400", Icon: Wifi },
  DEGRADED: { label: "Degraded", color: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/20",   ring: "bg-amber-400",   Icon: Minus },
  OFFLINE:  { label: "Offline",  color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20",     ring: "bg-red-400",     Icon: WifiOff },
} as const;

const STATUS_DESCRIPTION = {
  ONLINE:   "Bot is receiving and processing commands normally.",
  DEGRADED: "Bot is connected but responding slowly. Heartbeat signal is delayed.",
  OFFLINE:  "No heartbeat received recently. Bot may be offline or unreachable.",
} as const;

// ── Sub-components ─────────────────────────────────────────────────────────

function HeroCard({
  data, isLoading, lastRefresh, onRefresh,
}: {
  data:        BotStatusResponse | null;
  isLoading:   boolean;
  lastRefresh: Date | null;
  onRefresh:   () => void;
}) {
  const status = data?.status ?? "OFFLINE";
  const cfg    = STATUS_CONFIG[status];
  const { Icon } = cfg;

  return (
    <div className={`rounded-2xl border ${cfg.border} ${cfg.bg} p-5 sm:p-6`}>
      <div className="flex items-start justify-between gap-4 flex-wrap">

        {/* Status identity */}
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl border ${cfg.border} flex items-center justify-center flex-shrink-0`}>
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/20 border-t-white/70 rounded-full animate-spin" />
            ) : (
              <Icon className={cfg.color} size={22} />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <h2 className="text-[15px] font-bold text-white/90">Kingdom Treasury</h2>
              {data && (
                <span
                  className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold border ${cfg.border} ${cfg.bg} ${cfg.color}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${cfg.ring} ${status === "ONLINE" ? "animate-pulse" : ""}`} />
                  {cfg.label}
                </span>
              )}
            </div>
            <p className={`text-[12px] leading-relaxed ${cfg.color}`}>
              {data ? STATUS_DESCRIPTION[status] : "Loading status…"}
            </p>
            {data?.heartbeat?.botUsername && (
              <p className="text-[11px] text-white/30 mt-1">
                {data.heartbeat.botUsername}
              </p>
            )}
          </div>
        </div>

        {/* Refresh controls */}
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.04] hover:bg-white/[0.08] transition-colors text-[12px] text-white/60 disabled:opacity-40"
          >
            <RefreshCw
              size={12}
              className={isLoading ? "animate-spin text-white/40" : ""}
            />
            Refresh
          </button>
          <div className="flex items-center gap-1.5 text-[11px] text-white/30">
            <div className="w-1.5 h-1.5 rounded-full bg-white/20 animate-pulse" />
            Auto-refresh every 10s
          </div>
          {lastRefresh && (
            <p className="text-[10px] text-white/20">
              Updated {lastRefresh.toLocaleTimeString()}
            </p>
          )}
        </div>

      </div>
    </div>
  );
}

interface MetricCardProps {
  icon:    React.ComponentType<{ className?: string; size?: number }>;
  label:   string;
  value:   string;
  sub?:    string;
  status?: "ok" | "warn" | "error" | "neutral";
}

function MetricCard({ icon: Icon, label, value, sub, status = "neutral" }: MetricCardProps) {
  const dotColor = {
    ok:      "bg-emerald-400",
    warn:    "bg-amber-400",
    error:   "bg-red-400",
    neutral: "bg-white/20",
  }[status];

  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#111113] p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center flex-shrink-0">
          <Icon className="text-white/35" size={15} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <p className="text-[11px] text-white/35 font-medium">{label}</p>
            {status !== "neutral" && (
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotColor}`} />
            )}
          </div>
          <p className="text-[17px] font-bold text-white/85 leading-tight truncate">{value}</p>
          {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

// ── Error state ────────────────────────────────────────────────────────────

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-red-900/30 bg-red-950/20 p-6 flex flex-col items-center gap-3 text-center">
      <AlertTriangle className="text-red-400" size={22} />
      <div>
        <p className="text-[13px] font-semibold text-red-400">Failed to load bot status</p>
        <p className="text-[12px] text-white/35 mt-1">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="text-[12px] text-white/40 hover:text-white/70 transition-colors underline underline-offset-2"
      >
        Try again
      </button>
    </div>
  );
}

// ── Page content ───────────────────────────────────────────────────────────

function BotStatusContent() {
  const { guildId } = useParams<{ guildId: string }>();
  const [data, setData]           = useState<BotStatusResponse | null>(null);
  const [isLoading, setLoading]   = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [lastRefresh, setRefresh] = useState<Date | null>(null);
  const intervalRef               = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!guildId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<BotStatusResponse>(`/guilds/${guildId}/bot-status`);
      setData(result);
      setRefresh(new Date());
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [guildId]);

  // Initial fetch + polling
  useEffect(() => {
    void fetchStatus();
    intervalRef.current = setInterval(() => void fetchStatus(), 10_000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchStatus]);

  const hb = data?.heartbeat;

  // Derived metric values
  const heartbeatAgeFmt = formatAge(data?.heartbeatAge);
  const uptimeFmt       = formatUptime(hb?.uptimeSeconds);
  const latencyFmt      = hb?.latencyMs != null ? `${hb.latencyMs} ms` : "—";
  const guildCountFmt   = hb?.guildCount != null ? hb.guildCount.toString() : "—";

  const apiStatusVariant:  MetricCardProps["status"] = data?.apiStatus === "ok" ? "ok" : "error";
  const dbStatusVariant:   MetricCardProps["status"] = data?.dbStatus  === "ok" ? "ok" : "error";
  const hbDbStatusVariant: MetricCardProps["status"] =
    hb?.dbStatus === "connected" ? "ok" : hb?.dbStatus ? "error" : "neutral";
  const schedulerVariant: MetricCardProps["status"] =
    hb?.schedulerStatus === "running" ? "ok" :
    hb?.schedulerStatus === "stopped" ? "warn" : "neutral";

  return (
    <div className="max-w-3xl space-y-5">

      {/* Page header */}
      <div>
        <h2 className="text-[19px] font-bold text-white/90 mb-1 flex items-center gap-2">
          <Activity size={17} className="text-[#c0392b]" />
          Bot Status
        </h2>
        <p className="text-[13px] text-white/40 leading-relaxed">
          Live connection status and health metrics for the Kingdom Treasury bot.
        </p>
      </div>

      {/* Error */}
      {!isLoading && error && !data && (
        <ErrorState message={error} onRetry={() => void fetchStatus()} />
      )}

      {/* Hero card */}
      <HeroCard
        data={data}
        isLoading={isLoading && !data}
        lastRefresh={lastRefresh}
        onRefresh={() => void fetchStatus()}
      />

      {/* Metric grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">

        <MetricCard
          icon={Server}
          label="Guild Servers"
          value={guildCountFmt}
          sub="Servers the bot is in"
          status={hb?.guildCount != null ? "ok" : "neutral"}
        />

        <MetricCard
          icon={Clock}
          label="Uptime"
          value={uptimeFmt}
          sub="Since last restart"
          status={hb?.uptimeSeconds != null ? "ok" : "neutral"}
        />

        <MetricCard
          icon={Activity}
          label="Last Heartbeat"
          value={heartbeatAgeFmt}
          sub={hb?.writtenAt
            ? new Date(hb.writtenAt).toLocaleTimeString()
            : "No heartbeat received"
          }
          status={
            data?.heartbeatAge == null ? "neutral" :
            data.heartbeatAge < 15    ? "ok"      :
            data.heartbeatAge < 45    ? "warn"    : "error"
          }
        />

        <MetricCard
          icon={Zap}
          label="Latency"
          value={latencyFmt}
          sub="Discord gateway ping"
          status={
            hb?.latencyMs == null  ? "neutral" :
            hb.latencyMs < 100     ? "ok"      :
            hb.latencyMs < 250     ? "warn"    : "error"
          }
        />

        <MetricCard
          icon={Wifi}
          label="API Health"
          value={data?.apiStatus === "ok" ? "Operational" : data ? "Error" : "—"}
          sub="Dashboard API server"
          status={data ? apiStatusVariant : "neutral"}
        />

        <MetricCard
          icon={Database}
          label="Database"
          value={data?.dbStatus === "ok" ? "Connected" : data ? "Error" : "—"}
          sub="PostgreSQL connection"
          status={data ? dbStatusVariant : "neutral"}
        />

        <MetricCard
          icon={Database}
          label="Bot DB"
          value={hb?.dbStatus ?? "—"}
          sub="Bot SQLite connection"
          status={hbDbStatusVariant}
        />

        <MetricCard
          icon={Calendar}
          label="Scheduler"
          value={hb?.schedulerStatus
            ? hb.schedulerStatus.charAt(0).toUpperCase() + hb.schedulerStatus.slice(1)
            : "—"
          }
          sub="Background task loops"
          status={schedulerVariant}
        />

        {hb?.commandCountToday != null && (
          <MetricCard
            icon={Activity}
            label="Commands Today"
            value={hb.commandCountToday.toString()}
            sub="Slash command invocations"
            status="neutral"
          />
        )}

      </div>

      {/* Raw heartbeat detail (collapsed mini-section) */}
      {data && (
        <div className="rounded-xl border border-white/[0.06] bg-[#0f0f10] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-white/25 mb-3">
            Heartbeat Detail
          </p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2">
            {([
              ["Bot User", hb?.botUsername ?? "—"],
              ["Bot ID",   hb?.botUserId  ?? "—"],
              ["Shard",    "0"],
              ["Status",   data.status],
              ["Age",      data.heartbeatAge != null ? `${data.heartbeatAge}s` : "—"],
              ["Updated",  hb?.writtenAt ? new Date(hb.writtenAt).toLocaleString() : "—"],
            ] as [string, string][]).map(([k, v]) => (
              <div key={k} className="flex gap-3">
                <span className="text-[11px] text-white/30 w-20 flex-shrink-0">{k}</span>
                <span className="text-[11px] text-white/65 truncate">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

export default function BotStatusPage() {
  return (
    <DashboardLayout pageTitle="Bot Status">
      <BotStatusContent />
    </DashboardLayout>
  );
}
