import { useParams, useLocation } from "wouter";
import {
  Activity, Users, Coins, Landmark, Server,
  TrendingUp, ShoppingBag, Trophy, Crown, ArrowRight,
} from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/layout";
import { useGuild } from "@/context/guild-context";

// ── Stat card ─────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon, label, value, sub, accent = false,
}: {
  icon: typeof Activity; label: string; value: string | number;
  sub?: string; accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#111113] p-5 flex items-start gap-4">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${accent ? "bg-[#c0392b]/10" : "bg-white/[0.05]"}`}>
        <Icon size={16} className={accent ? "text-[#e74c3c]" : "text-white/35"} />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] text-white/35 font-medium mb-0.5">{label}</p>
        <p className="text-[20px] font-bold text-white/90 leading-none">{value}</p>
        {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

// ── Quick access link ──────────────────────────────────────────────────────

function QuickLink({ icon: Icon, label, path }: {
  icon: typeof Activity; label: string; path: string;
}) {
  const [, navigate] = useLocation();
  return (
    <button
      onClick={() => navigate(path)}
      className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg border border-white/[0.07] bg-[#0f0f10] hover:border-[#c0392b]/30 hover:bg-[#111113] transition-all group"
    >
      <Icon size={14} className="text-white/30 group-hover:text-[#e74c3c] transition-colors flex-shrink-0" />
      <span className="text-[13px] font-medium text-white/65 group-hover:text-white/85 transition-colors truncate flex-1">
        {label}
      </span>
      <ArrowRight size={12} className="text-white/15 group-hover:text-white/40 transition-colors flex-shrink-0" />
    </button>
  );
}

// ── Overview content ───────────────────────────────────────────────────────

function OverviewContent() {
  const { guildId } = useParams<{ guildId: string }>();
  const { guild, isLoading } = useGuild();
  const base = `/guilds/${guildId}`;

  const guildName = guild?.name ?? "Your Server";

  return (
    <div className="max-w-4xl space-y-6">

      {/* Server identity */}
      <div className="flex items-center gap-4">
        {isLoading ? (
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
          <div className="flex items-center gap-3 mt-1">
            {guild?.botInstalled && (
              <span className="flex items-center gap-1.5 text-[12px] text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Bot Active
              </span>
            )}
            {guild?.memberCount != null && (
              <span className="text-[12px] text-white/35">
                {guild.memberCount.toLocaleString()} members
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={Activity}
          label="Bot Status"
          value={guild?.botInstalled ? "Connected" : "Offline"}
          sub={guild?.botInstalled ? "All systems operational" : "Bot not installed"}
          accent={guild?.botInstalled}
        />
        <StatCard
          icon={Users}
          label="Members"
          value={guild?.memberCount != null ? guild.memberCount.toLocaleString() : "—"}
          sub="Discord count"
        />
        <StatCard
          icon={Coins}
          label="Economy Size"
          value="—"
          sub="Phase 3 data"
        />
        <StatCard
          icon={Landmark}
          label="Treasury"
          value="—"
          sub="Phase 3 data"
        />
      </div>

      {/* Server summary + quick access */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Summary */}
        <div className="lg:col-span-3 rounded-xl border border-white/[0.07] bg-[#111113] p-5">
          <div className="flex items-center gap-2 mb-4">
            <Server size={14} className="text-white/30" />
            <h3 className="text-[13px] font-semibold text-white/70">Server Summary</h3>
          </div>
          <div className="divide-y divide-white/[0.05]">
            {[
              { label: "Server Name",  value: guild?.name ?? "—" },
              { label: "Guild ID",     value: guildId ?? "—" },
              { label: "Members",      value: guild?.memberCount != null ? guild.memberCount.toLocaleString() : "—" },
              { label: "Bot Status",   value: guild?.botInstalled ? "Installed" : "Not installed" },
            ].map(({ label, value }) => (
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
            <ArrowRight size={14} className="text-white/30" />
            <h3 className="text-[13px] font-semibold text-white/70">Quick Access</h3>
          </div>
          <div className="space-y-2">
            <QuickLink icon={Coins}       label="Economy"       path={`${base}/economy`} />
            <QuickLink icon={TrendingUp}  label="Ascension"     path={`${base}/ascension`} />
            <QuickLink icon={ShoppingBag} label="Market"        path={`${base}/market`} />
            <QuickLink icon={Trophy}      label="Kingdom Ranks" path={`${base}/kingdom-ranks`} />
            <QuickLink icon={Crown}       label="Ranks & Roles" path={`${base}/ranks`} />
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
