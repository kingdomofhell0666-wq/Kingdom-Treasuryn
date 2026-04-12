import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { API_BASE } from "@/lib/api";

interface Guild {
  id:           string;
  name:         string;
  icon:         string | null;
  iconUrl:      string | null;
  memberCount:  number | null;
  botInstalled: boolean;
}

function GuildIcon({ guild }: { guild: Guild }) {
  if (guild.iconUrl) {
    return (
      <img
        src={guild.iconUrl}
        alt={guild.name}
        className="w-14 h-14 rounded-2xl object-cover flex-shrink-0"
      />
    );
  }
  const initials = guild.name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
  return (
    <div className="w-14 h-14 rounded-2xl bg-muted border border-border flex items-center justify-center text-base font-bold text-foreground flex-shrink-0 select-none">
      {initials}
    </div>
  );
}

function StatusBadge({ botInstalled }: { botInstalled: boolean }) {
  if (botInstalled) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        Active
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border">
      <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground opacity-50" />
      Not Installed
    </span>
  );
}

function GuildCard({ guild, onClick }: { guild: Guild; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={!guild.botInstalled}
      className="group w-full text-left flex items-center gap-4 p-4 rounded-xl bg-card border border-border
        transition-all duration-150
        hover:border-primary/50 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-card disabled:hover:shadow-none
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <GuildIcon guild={guild} />

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-foreground text-sm truncate group-hover:text-primary transition-colors">
          {guild.name}
        </p>
        {guild.memberCount != null && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {guild.memberCount.toLocaleString()} members
          </p>
        )}
        <div className="mt-2">
          <StatusBadge botInstalled={guild.botInstalled} />
        </div>
      </div>

      {guild.botInstalled && (
        <svg
          className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      )}
    </button>
  );
}

function UserAvatar({ user }: { user: ReturnType<typeof useAuth>["user"] }) {
  if (!user) return null;
  return (
    <div className="flex items-center gap-2.5">
      {user.avatarUrl ? (
        <img src={user.avatarUrl} alt={user.username} className="w-7 h-7 rounded-full" />
      ) : (
        <div className="w-7 h-7 rounded-full bg-muted border border-border flex items-center justify-center text-xs font-bold text-foreground">
          {user.username[0]?.toUpperCase()}
        </div>
      )}
      <span className="text-sm text-muted-foreground hidden sm:block">{user.username}</span>
    </div>
  );
}

async function logout() {
  await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
  window.location.href = "/dashboard/";
}

export default function GuildsPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const [, navigate] = useLocation();
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [guildsLoading, setGuildsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate("/");
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (!isAuthenticated) return;
    setGuildsLoading(true);
    fetch(`${API_BASE}/guilds`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json() as Promise<{ guilds: Guild[] }>;
      })
      .then(({ guilds }) => {
        setGuilds(guilds);
        setGuildsLoading(false);
      })
      .catch(() => {
        setError("Failed to load your servers. Please try again.");
        setGuildsLoading(false);
      });
  }, [isAuthenticated]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-muted-foreground border-t-foreground rounded-full animate-spin" />
      </div>
    );
  }

  const installed = guilds.filter((g) => g.botInstalled);
  const notInstalled = guilds.filter((g) => !g.botInstalled);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top bar */}
      <header className="border-b border-border px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold select-none">
            K
          </div>
          <span className="text-sm font-semibold text-foreground tracking-wide">
            Kingdom Treasury
          </span>
        </div>
        <div className="flex items-center gap-4">
          <UserAvatar user={user} />
          <button
            onClick={logout}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 sm:px-6 py-10">

        {/* Page heading */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-foreground">Select a Realm</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Choose a server to command your infernal economy.
          </p>
        </div>

        {/* Loading state */}
        {guildsLoading && (
          <div className="flex flex-col items-center gap-4 py-20">
            <div className="w-6 h-6 border-2 border-muted-foreground border-t-foreground rounded-full animate-spin" />
            <p className="text-sm text-muted-foreground">Loading your realms…</p>
          </div>
        )}

        {/* Error state */}
        {!guildsLoading && error && (
          <div className="flex flex-col items-center gap-3 py-20 text-center">
            <p className="text-destructive text-sm">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty state — no eligible guilds at all */}
        {!guildsLoading && !error && guilds.length === 0 && (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-card border border-border flex items-center justify-center text-3xl select-none">
              🏰
            </div>
            <div className="space-y-1">
              <p className="font-semibold text-foreground">No eligible realms found</p>
              <p className="text-sm text-muted-foreground max-w-xs">
                You must have Administrator or Manage Server permission to use Kingdom Treasury.
              </p>
            </div>
          </div>
        )}

        {/* Guild list */}
        {!guildsLoading && !error && guilds.length > 0 && (
          <div className="space-y-8">

            {/* Bot installed servers */}
            {installed.length > 0 && (
              <section>
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">
                  Your Realms
                </p>
                <div className="space-y-2">
                  {installed.map((guild) => (
                    <GuildCard
                      key={guild.id}
                      guild={guild}
                      onClick={() => navigate(`/guilds/${guild.id}`)}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Not installed servers */}
            {notInstalled.length > 0 && (
              <section>
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-3">
                  Add to a Server
                </p>
                <div className="space-y-2">
                  {notInstalled.map((guild) => (
                    <GuildCard
                      key={guild.id}
                      guild={guild}
                      onClick={() => {}}
                    />
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Invite Kingdom Treasury to these servers to manage their economy.
                </p>
              </section>
            )}

          </div>
        )}
      </main>

      <footer className="border-t border-border px-6 py-4 text-center">
        <p className="text-xs text-muted-foreground">Kingdom of Hell · Private Admin Dashboard</p>
      </footer>
    </div>
  );
}
