import { useEffect, useState } from "react";
import { useParams, useLocation } from "wouter";
import {
  Activity, Server, Clock, Zap, Database,
  ArrowRight, Crown, TrendingUp, ShoppingBag, Trophy, Coins,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { useGuild } from "@/context/guild-context";
import { apiGet } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

type BotStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

interface OverviewData {
  guildId:         string;
  botStatus:       BotStatus;
  heartbeatAge:    number | null;
  botUsername:     string | null;
  guildCount:      number | null;
  uptimeSeconds:   number | null;
  latencyMs:       number | null;
  schedulerStatus: string | null;
  apiStatus:       "ok" | "error";
  dbStatus:        "ok" | "error";
  lastHeartbeat:   string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatUptime(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

const STATUS_CONFIG = {
  ONLINE:   { label: "Online",   color: "text-emerald-400", dot: "bg-emerald-400" },
  DEGRADED: { label: "Degraded", color: "text-amber-400",   dot: "bg-amber-400" },
  OFFLINE:  { label: "Offline",  color: "text-red-400",     dot: "bg-red-500" },
} as const;

// ── Sub-components ─────────────────────────────────────────────────────────

function BotStatusBadge({ status }: { status: BotStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className="flex items-center gap-1.5 text-[12px] font-medium">
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${status === "ONLINE" ? "animate-pulse" : ""}`} />
      <span className={cfg.color}>{cfg.label}</span>
    </span>
  );
}

function StatCard({
  icon: Icon, label, value, sub, accent = false, loading = false,
}: {
  icon: typeof Activity; label: string; value: string;
  sub?: string; accent?: boolean; loading?: boolean;
}) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#111113] p-4 sm:p-5 flex items-start gap-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${accent ? "bg-[#c0392b]/10" : "bg-white/[0.05]"}`}>
        <Icon size={15} className={accent ? "text-[#e74c3c]" : "text-white/35"} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] text-white/35 font-medium mb-0.5">{label}</p>
        {loading ? (
          <div className="h-5 w-16 bg-white/[0.06] rounded animate-pulse mt-1" />
        ) : (
          <>
            <p className="text-[18px] font-bold text-white/90 leading-tight truncate">{value}</p>
            {sub && <p className="text-[11px] text-white/30 mt-0.5">{sub}</p>}
          </>
        )}
      </div>
    </div>
  );
}

function QuickLink({ icon: Icon, label, path }: {
  icon: typeof Activity; label: string; path: string;
}) {
  const [, navigate] = useLocation();
  return (
    <button
      onClick={() => navigate(path)}
      className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg border border-white/[0.07] bg-[#0f0f10] hover:border-[#c0392b]/30 hover:bg-[#111113] transition-all group w-full text-left"
    >
      <Icon size={14} className="text-white/30 group-hover:text-[#e74c3c] transition-colors flex-shrink-0" />
      <span className="text-[13px] font-medium text-white/65 group-hover:text-white/85 transition-colors truncate flex-1">
        {label}
      </span>
      <ArrowRight size={12} className="text-white/15 group-hover:text-white/40 transition-colors flex-shrink-0" />
    </button>
  );
}

// ── Page content ───────────────────────────────────────────────────────────

function OverviewContent() {
  const { guildId } = useParams<{ guildId: string }>();
  const { guild, isLoading: guildLoading } = useGuild();
  const base = `/guilds/${guildId}`;

  const [overview, setOverview]     = useState<OverviewData | null>(null);
  const [dataLoading, setDataLoad]  = useState(true);
  const [dataError, setDataError]   = useState<string | null>(null);

  useEffect(() => {
    if (!guildId) return;
    setDataLoad(true);
    apiGet<OverviewData>(`/guilds/${guildId}/overview`)
      .then((d) => { setOverview(d); setDataLoad(false); })
      .catch((err) => {
        setDataError(err instanceof Error ? err.message : "Unknown error");
        setDataLoad(false);
      });
  }, [guildId]);

  const guildName = guild?.name ?? "Your Server";
  const status    = overview?.botStatus ?? "OFFLINE";

  return (
    <div className="max-w-4xl space-y-6">

      {/* Server identity header */}
      <div className="flex items-center gap-4">
        {guildLoading ? (
          <div className="w-14 h-14 rounded-xl bg-white/[0.05] animate-pulse flex-shrink-0" />
        ) : guild?.iconUrl ? (
          <img src={guild.iconUrl} alt={guild.name} className="w-14 h-14 rounded-xl object-cover flex-shrink-0" />
        ) : (
          <div className="w-14 h-14 rounded-xl bg-[#c0392b]/10 border border-[#c0392b]/20 flex items-center justify-center text-xl font-bold text-[#c0392b] flex-shrink-0 select-none">
            {guildName[0]?.toUpperCase()}
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold text-white/90 truncate">{guildName}</h2>
          <div className="flex items-center gap-4 mt-1.5 flex-wrap">
            {overview ? (
              <BotStatusBadge status={status} />
            ) : (
              <div className="h-4 w-16 bg-white/[0.05] rounded animate-pulse" />
            )}
            {guild?.memberCount != null && (
              <span className="text-[12px] text-white/35">
                {guild.memberCount.toLocaleString()} members
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Error state */}
      {!dataLoading && dataError && (
        <div className="rounded-xl border border-red-900/30 bg-red-950/20 p-4">
          <p className="text-[13px] text-red-400">Could not load overview: {dataError}</p>
        </div>
      )}

      {/* Core metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={Activity}
          label="Bot Status"
          value={STATUS_CONFIG[status].label}
          sub={overview
            ? overview.heartbeatAge != null
              ? `Heartbeat ${overview.heartbeatAge}s ago`
              : "No heartbeat"
            : undefined
          }
          accent={status === "ONLINE"}
          loading={dataLoading}
        />
        <StatCard
          icon={Server}
          label="Guild Servers"
          value={overview?.guildCount != null ? overview.guildCount.toString() : "—"}
          sub="Servers bot is in"
          loading={dataLoading}
        />
        <StatCard
          icon={Clock}
          label="Uptime"
          value={formatUptime(overview?.uptimeSeconds)}
          sub="Since last restart"
          loading={dataLoading}
        />
        <StatCard
          icon={Zap}
          label="Latency"
          value={overview?.latencyMs != null ? `${overview.latencyMs} ms` : "—"}
          sub="Discord gateway ping"
          loading={dataLoading}
        />
      </div>

      {/* Server summary + quick access */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* System summary */}
        <div className="lg:col-span-3 rounded-xl border border-white/[0.07] bg-[#111113] p-5">
          <div className="flex items-center gap-2 mb-4">
            <Server size={14} className="text-white/30" />
            <h3 className="text-[13px] font-semibold text-white/70">System Summary</h3>
          </div>
          <div className="divide-y divide-white/[0.05]">
            {[
              ["Server",        guildName],
              ["Guild ID",      guildId ?? "—"],
              ["Members",       guild?.memberCount != null ? guild.memberCount.toLocaleString() : "—"],
              ["Bot",           overview?.botUsername ?? "—"],
              ["API",           overview?.apiStatus === "ok" ? "Operational" : "Error"],
              ["Database",      overview?.dbStatus === "ok" ? "Connected" : "Error"],
              ["Scheduler",     overview?.schedulerStatus ?? "—"],
              ["Last Pulse",    overview?.lastHeartbeat
                ? new Date(overview.lastHeartbeat).toLocaleTimeString()
                : "Never"],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between py-2.5 gap-4">
                <span className="text-[12px] text-white/35 flex-shrink-0">{label}</span>
                <span className="text-[12px] font-medium text-white/70 truncate text-right max-w-[55%]">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick access */}
        <div className="lg:col-span-2 rounded-xl border border-white/[0.07] bg-[#111113] p-5">
          <div className="flex items-center gap-2 mb-4">
            <Database size={14} className="text-white/30" />
            <h3 className="text-[13px] font-semibold text-white/70">Health</h3>
          </div>
          <div className="divide-y divide-white/[0.05] mb-5">
            {[
              { label: "API Server",  status: overview?.apiStatus ?? null },
              { label: "Dashboard DB", status: overview?.dbStatus ?? null },
            ].map(({ label, status: s }) => (
              <div key={label} className="flex items-center justify-between py-2.5">
                <span className="text-[12px] text-white/35">{label}</span>
                {s === null ? (
                  <div className="h-3.5 w-16 bg-white/[0.05] rounded animate-pulse" />
                ) : (
                  <span className={`flex items-center gap-1.5 text-[12px] font-medium ${s === "ok" ? "text-emerald-400" : "text-red-400"}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${s === "ok" ? "bg-emerald-400" : "bg-red-500"}`} />
                    {s === "ok" ? "OK" : "Error"}
                  </span>
                )}
              </div>
            ))}
          </div>

          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-white/25 mb-3">
            Quick Access
          </p>
          <div className="space-y-2">
            <QuickLink icon={Activity}    label="Bot Status"    path={`${base}/bot-status`} />
            <QuickLink icon={Coins}       label="Economy"       path={`${base}/economy`} />
            <QuickLink icon={TrendingUp}  label="Ascension"     path={`${base}/ascension`} />
            <QuickLink icon={Trophy}      label="Kingdom Ranks" path={`${base}/kingdom-ranks`} />
            <QuickLink icon={Crown}       label="Ranks & Roles" path={`${base}/ranks`} />
            <QuickLink icon={ShoppingBag} label="Market"        path={`${base}/market`} />
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
