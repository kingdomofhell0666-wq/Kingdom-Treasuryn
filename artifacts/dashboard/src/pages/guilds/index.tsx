import { useGetGuilds } from "@workspace/api-client-react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Spinner } from "@/components/ui/spinner";
import { AuthGuard, GuildsLayout } from "@/components/layout";
import {
  Shield, Users, PlusCircle, CheckCircle2,
  ChevronRight, ServerCrash,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";

function useAppConfig() {
  return useQuery({
    queryKey: ["app-config"],
    queryFn: () => apiGet<{ discordClientId: string }>("/api/app-config"),
    staleTime: Infinity,
  });
}

export default function GuildsPage() {
  return (
    <AuthGuard>
      <GuildsLayout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10 space-y-10">
          {/* Page header */}
          <div className="space-y-1.5">
            <h1 className="text-3xl font-extrabold tracking-tight font-serif text-foreground">
              Select a Realm
            </h1>
            <p className="text-muted-foreground text-base">
              Choose a server to command your infernal economy.
            </p>
          </div>

          <GuildList />
        </div>
      </GuildsLayout>
    </AuthGuard>
  );
}

function GuildList() {
  const { data: guilds, isLoading, isError } = useGetGuilds();
  const { data: appConfig } = useAppConfig();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="h-[148px] bg-card rounded-xl border border-border/50 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (isError || !guilds) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <div className="w-14 h-14 bg-destructive/10 border border-destructive/20 rounded-xl flex items-center justify-center">
          <ServerCrash className="w-7 h-7 text-destructive" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-foreground">Failed to load servers</p>
          <p className="text-sm text-muted-foreground">Could not reach Discord. Please try again later.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  // Show ALL guilds where the user is admin — bot presence is just a badge status
  const adminGuilds = guilds.filter((g) => g.isAdmin);

  if (adminGuilds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-5 py-20 text-center max-w-md mx-auto">
        <div className="w-16 h-16 bg-muted/50 border border-border/50 rounded-2xl flex items-center justify-center">
          <Shield className="w-8 h-8 text-muted-foreground opacity-40" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-foreground">No eligible realms found</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            You must have <strong>Administrator</strong> or <strong>Manage Server</strong> permission
            in a Discord server to use Kingdom Treasury.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Section labels */}
      {adminGuilds.some((g) => g.botPresent) && (
        <Section label="Active Realms" count={adminGuilds.filter((g) => g.botPresent).length}>
          <GuildGrid guilds={adminGuilds.filter((g) => g.botPresent)} active />
        </Section>
      )}

      {adminGuilds.some((g) => !g.botPresent) && (
        <Section
          label="Not Installed"
          count={adminGuilds.filter((g) => !g.botPresent).length}
        >
          <GuildGrid
            guilds={adminGuilds.filter((g) => !g.botPresent)}
            active={false}
            clientId={appConfig?.discordClientId ?? ""}
          />
        </Section>
      )}
    </>
  );
}

function Section({
  label,
  count,
  children,
}: {
  label: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/70">
          {label}
        </h2>
        <div className="h-px flex-1 bg-border/40" />
        <span className="text-xs text-muted-foreground/50 tabular-nums">{count}</span>
      </div>
      {children}
    </section>
  );
}

function GuildGrid({
  guilds,
  active,
  clientId = "",
}: {
  guilds: ReturnType<typeof useGetGuilds>["data"];
  active: boolean;
  clientId?: string;
}) {
  if (!guilds) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {guilds.map((guild) =>
        active ? (
          <ActiveGuildCard key={guild.id} guild={guild} />
        ) : (
          <InactiveGuildCard key={guild.id} guild={guild} clientId={clientId} />
        )
      )}
    </div>
  );
}

type Guild = NonNullable<ReturnType<typeof useGetGuilds>["data"]>[number];

function GuildIcon({ guild, size = "md" }: { guild: Guild; size?: "md" | "lg" }) {
  const cls = size === "lg" ? "w-14 h-14 rounded-xl text-xl" : "w-12 h-12 rounded-lg text-lg";
  return (
    <div
      className={`${cls} bg-muted border border-border/60 overflow-hidden flex-shrink-0 flex items-center justify-center font-bold text-muted-foreground`}
    >
      {guild.iconUrl ? (
        <img src={guild.iconUrl} alt={guild.name} className="w-full h-full object-cover" />
      ) : (
        <span className="uppercase">{guild.name.charAt(0)}</span>
      )}
    </div>
  );
}

function ActiveGuildCard({ guild }: { guild: Guild }) {
  return (
    <Link href={`/guilds/${guild.id}`} className="block group outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-xl">
      <div className="h-full bg-card/60 border border-border/50 rounded-xl p-4 flex flex-col gap-3 transition-all duration-200 group-hover:border-primary/40 group-hover:bg-card group-hover:shadow-lg group-hover:shadow-primary/5 group-hover:-translate-y-0.5">
        {/* Header row */}
        <div className="flex items-start gap-3">
          <GuildIcon guild={guild} />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm text-foreground truncate group-hover:text-primary transition-colors leading-tight">
              {guild.name}
            </p>
            <div className="flex items-center gap-1.5 mt-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0" />
              <span className="text-[11px] font-medium text-emerald-500">Active</span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary/50 transition-colors flex-shrink-0 mt-1" />
        </div>

        {/* Footer */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-auto pt-2 border-t border-border/30">
          <Users className="w-3.5 h-3.5" />
          <span>{guild.memberCount?.toLocaleString() ?? 0} members</span>
        </div>
      </div>
    </Link>
  );
}

function InactiveGuildCard({ guild, clientId }: { guild: Guild; clientId: string }) {
  const BOT_INVITE = clientId
    ? `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=8&scope=bot%20applications.commands&guild_id=${guild.id}`
    : `https://discord.com/developers/applications`;

  return (
    <div className="bg-card/30 border border-border/30 rounded-xl p-4 flex flex-col gap-3 opacity-70 hover:opacity-90 transition-opacity">
      {/* Header row */}
      <div className="flex items-start gap-3">
        <GuildIcon guild={guild} />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-foreground truncate leading-tight">
            {guild.name}
          </p>
          <div className="flex items-center gap-1.5 mt-1.5">
            <div className="w-2 h-2 rounded-full bg-amber-500/70 flex-shrink-0" />
            <span className="text-[11px] font-medium text-amber-500/90">Not Installed</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between gap-2 mt-auto pt-2 border-t border-border/20">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground/60">
          <Users className="w-3.5 h-3.5" />
          <span>{guild.memberCount?.toLocaleString() ?? 0}</span>
        </div>
        <a
          href={BOT_INVITE}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-xs text-primary/80 hover:text-primary font-medium transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          Add Bot
        </a>
      </div>
    </div>
  );
}
