import { useEffect } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { Crown, LogOut, RefreshCw, AlertCircle, CheckCircle2, XCircle, Users, Bot } from "lucide-react";
import { api, Guild } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import { useGuild } from "@/context/guild-context";
import { cn } from "@/lib/utils";

function GuildCard({ guild, onClick }: { guild: Guild; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-all group",
        guild.botPresent
          ? "bg-card border-card-border hover:border-primary/50 hover:bg-card/80 cursor-pointer"
          : "bg-card/40 border-card-border/50 cursor-not-allowed opacity-60"
      )}
      disabled={!guild.botPresent}
    >
      {/* Server icon */}
      {guild.iconUrl ? (
        <img
          src={guild.iconUrl}
          alt={guild.name}
          className="w-12 h-12 rounded-xl shrink-0"
        />
      ) : (
        <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
          <span className="text-lg font-bold text-primary">{guild.name.charAt(0)}</span>
        </div>
      )}

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
          {guild.name}
        </p>
        {guild.memberCount && (
          <p className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
            <Users className="w-3 h-3" />
            {guild.memberCount.toLocaleString()} members
          </p>
        )}
      </div>

      <div className="shrink-0">
        {guild.botPresent ? (
          <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Bot active
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-full">
            <XCircle className="w-3.5 h-3.5" />
            No bot
          </span>
        )}
      </div>
    </button>
  );
}

export default function GuildsPage() {
  const { user, logout, isLoggingOut, isLoading: authLoading } = useAuth();
  const { setActiveGuild } = useGuild();
  const [, setLocation] = useLocation();

  const {
    data: guilds,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery<Guild[]>({
    queryKey: ["guilds"],
    queryFn: () => api.guilds.list(),
    enabled: !!user,
  });

  useEffect(() => {
    if (!authLoading && !user) {
      setLocation("/");
    }
  }, [user, authLoading, setLocation]);

  const handleSelectGuild = (guild: Guild) => {
    setActiveGuild(guild);
    setLocation(`/guilds/${guild.id}/overview`);
  };

  const botGuilds = guilds?.filter((g) => g.botPresent) ?? [];
  const otherGuilds = guilds?.filter((g) => !g.botPresent) ?? [];

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle top glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 60% 30% at 50% 0%, rgba(192,57,43,0.1) 0%, transparent 60%)",
        }}
      />

      <div className="relative max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary text-primary-foreground">
              <Crown className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Kingdom Treasury</h1>
              <p className="text-xs text-muted-foreground">Select a server to manage</p>
            </div>
          </div>

          {user && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <img
                  src={user.avatarUrl}
                  alt={user.username}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm text-muted-foreground hidden sm:block">{user.username}</span>
              </div>
              <button
                onClick={logout}
                disabled={isLoggingOut}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:block">Sign out</span>
              </button>
            </div>
          )}
        </div>

        {/* Loading state */}
        {(isLoading || authLoading) && (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin mb-3" />
            <p className="text-sm">Loading your servers...</p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="w-10 h-10 text-destructive mb-3" />
            <p className="font-medium text-foreground mb-1">Failed to load servers</p>
            <p className="text-sm text-muted-foreground mb-4">
              There was a problem fetching your Discord servers.
            </p>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try again
            </button>
          </div>
        )}

        {/* Guild list */}
        {!isLoading && !authLoading && !isError && guilds && (
          <>
            {/* Refresh button */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                {botGuilds.length} server{botGuilds.length !== 1 ? "s" : ""} with bot
              </p>
              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-secondary"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isFetching && "animate-spin")} />
                Refresh
              </button>
            </div>

            {/* Servers with bot */}
            {botGuilds.length > 0 && (
              <div className="space-y-2 mb-6">
                {botGuilds.map((guild) => (
                  <GuildCard key={guild.id} guild={guild} onClick={() => handleSelectGuild(guild)} />
                ))}
              </div>
            )}

            {botGuilds.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center border border-dashed border-border rounded-xl mb-6">
                <Bot className="w-10 h-10 text-muted-foreground mb-3" />
                <p className="font-medium text-foreground mb-1">No servers with the bot</p>
                <p className="text-sm text-muted-foreground">
                  Invite the Kingdom Treasury bot to one of your servers to get started.
                </p>
              </div>
            )}

            {/* Servers without bot */}
            {otherGuilds.length > 0 && (
              <>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Other servers (bot not installed)
                </p>
                <div className="space-y-2">
                  {otherGuilds.map((guild) => (
                    <GuildCard key={guild.id} guild={guild} onClick={() => {}} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
