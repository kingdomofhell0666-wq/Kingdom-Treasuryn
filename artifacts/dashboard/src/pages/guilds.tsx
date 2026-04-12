import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { apiGet, API_BASE } from "@/lib/api";

interface Guild {
  id:           string;
  name:         string;
  icon:         string | null;
  iconUrl:      string | null;
  memberCount:  number | null;
  botInstalled: boolean;
}

// ── Sub-components ─────────────────────────────────────────────────────────

function GuildIcon({ guild }: { guild: Guild }) {
  if (guild.iconUrl) {
    return (
      <img
        src={guild.iconUrl}
        alt={guild.name}
        className="w-12 h-12 rounded-xl object-cover flex-shrink-0"
      />
    );
  }
  const initials = guild.name
    .split(/\s+/).filter(Boolean).slice(0, 2)
    .map((w) => w[0]).join("").toUpperCase();
  return (
    <div className="w-12 h-12 rounded-xl bg-[#c0392b]/15 border border-[#c0392b]/20 flex items-center justify-center text-sm font-bold text-[#c0392b] flex-shrink-0 select-none">
      {initials}
    </div>
  );
}

function StatusBadge({ installed }: { installed: boolean }) {
  if (installed) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/50 text-emerald-400 border border-emerald-800/40">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        Active
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-white/[0.04] text-white/35 border border-white/[0.08]">
      <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
      Not Installed
    </span>
  );
}

function GuildCard({
  guild, onClick,
}: { guild: Guild; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={!guild.botInstalled}
      className={[
        "w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-all duration-100",
        guild.botInstalled
          ? "bg-[#111113] border-white/[0.07] hover:border-[#c0392b]/40 hover:bg-[#111113] group cursor-pointer"
          : "bg-[#0f0f10] border-white/[0.04] opacity-50 cursor-not-allowed",
      ].join(" ")}
    >
      <GuildIcon guild={guild} />

      <div className="flex-1 min-w-0">
        <p className={`text-[14px] font-semibold truncate transition-colors ${guild.botInstalled ? "text-white/85 group-hover:text-white" : "text-white/50"}`}>
          {guild.name}
        </p>
        {guild.memberCount != null && (
          <p className="text-[12px] text-white/35 mt-0.5">
            {guild.memberCount.toLocaleString()} members
          </p>
        )}
        <div className="mt-2">
          <StatusBadge installed={guild.botInstalled} />
        </div>
      </div>

      {guild.botInstalled && (
        <svg
          className="w-4 h-4 text-white/20 group-hover:text-[#c0392b] transition-colors flex-shrink-0"
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      )}
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function GuildsPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const [, navigate] = useLocation();
  const [guilds, setGuilds]           = useState<Guild[]>([]);
  const [guildsLoading, setGuildsLoad] = useState(true);
  const [error, setError]             = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) navigate("/");
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (!isAuthenticated) return;
    apiGet<{ guilds: Guild[] }>("/guilds")
      .then(({ guilds: g }) => { setGuilds(g); setGuildsLoad(false); })
      .catch(() => { setError("Failed to load your servers. Please try again."); setGuildsLoad(false); });
  }, [isAuthenticated]);

  async function logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    window.location.href = "/dashboard/";
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-white/20 border-t-white/70 rounded-full animate-spin" />
      </div>
    );
  }

  const installed    = guilds.filter((g) => g.botInstalled);
  const notInstalled = guilds.filter((g) => !g.botInstalled);

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex flex-col">

      {/* Header */}
      <header className="border-b border-white/[0.07] px-4 sm:px-6 py-3.5 flex items-center justify-between gap-4 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-[#c0392b] flex items-center justify-center text-white text-xs font-black select-none">
            K
          </div>
          <span className="text-[13px] font-semibold text-white/80 tracking-wide">
            Kingdom Treasury
          </span>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden sm:flex items-center gap-2">
              {user.avatarUrl && (
                <img src={user.avatarUrl} alt={user.username} className="w-6 h-6 rounded-full" />
              )}
              <span className="text-[12px] text-white/45">{user.globalName ?? user.username}</span>
            </div>
          )}
          <button
            onClick={logout}
            className="text-[12px] text-white/35 hover:text-white/70 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 w-full max-w-xl mx-auto px-4 sm:px-6 py-10">

        <div className="mb-7">
          <h1 className="text-[22px] font-bold text-white/90">Select a Realm</h1>
          <p className="text-[13px] text-white/40 mt-1.5">
            Choose a server to command your infernal systems.
          </p>
        </div>

        {/* Loading */}
        {guildsLoading && (
          <div className="flex flex-col items-center gap-4 py-20">
            <div className="w-5 h-5 border-2 border-white/20 border-t-white/70 rounded-full animate-spin" />
            <p className="text-[13px] text-white/35">Loading your realms…</p>
          </div>
        )}

        {/* Error */}
        {!guildsLoading && error && (
          <div className="flex flex-col items-center gap-3 py-20 text-center">
            <p className="text-[13px] text-red-400">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-[12px] text-white/35 hover:text-white/70 transition-colors underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty */}
        {!guildsLoading && !error && guilds.length === 0 && (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#111113] border border-white/[0.08] flex items-center justify-center text-2xl">
              🏰
            </div>
            <div>
              <p className="text-[14px] font-semibold text-white/80">No eligible realms found</p>
              <p className="text-[12px] text-white/40 mt-1 max-w-xs mx-auto">
                You need Administrator or Manage Server permission in a server where the bot is installed.
              </p>
            </div>
          </div>
        )}

        {/* Guild lists */}
        {!guildsLoading && !error && guilds.length > 0 && (
          <div className="space-y-8">

            {installed.length > 0 && (
              <section>
                <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-white/25 mb-3">
                  Your Realms
                </p>
                <div className="space-y-2">
                  {installed.map((g) => (
                    <GuildCard
                      key={g.id}
                      guild={g}
                      onClick={() => navigate(`/guilds/${g.id}`)}
                    />
                  ))}
                </div>
              </section>
            )}

            {notInstalled.length > 0 && (
              <section>
                <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-white/25 mb-3">
                  Add to a Server
                </p>
                <div className="space-y-2">
                  {notInstalled.map((g) => (
                    <GuildCard key={g.id} guild={g} onClick={() => {}} />
                  ))}
                </div>
                <p className="text-[11px] text-white/25 mt-3">
                  Invite Kingdom Treasury to these servers to manage their economy.
                </p>
              </section>
            )}

          </div>
        )}

      </main>

      <footer className="border-t border-white/[0.07] px-6 py-4 text-center flex-shrink-0">
        <p className="text-[11px] text-white/20">Kingdom of Hell · Private Admin Dashboard</p>
      </footer>
    </div>
  );
}
