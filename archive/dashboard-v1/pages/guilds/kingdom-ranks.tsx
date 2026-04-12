import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiGet } from "@/lib/api";
import {
  Trophy, Clock, Users, Flame, Timer, Crown,
  ChevronUp, AlertCircle, RefreshCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type KrUser = {
  position: number;
  discordId: string;
  username: string;
  economyRank: string;
  weeklyActiveSeconds: number;
  weeklyActiveFmt: string;
  weeklyDcEarned: number;
  balance: number;
};

type KrData = {
  weekStart: string;
  nextReset: string;
  secsToReset: number;
  totalEligible: number;
  topUsers: KrUser[];
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const MEDAL = ["🥇", "🥈", "🥉"];

function fmtNumber(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function useCountdown(secsToReset: number) {
  const [secs, setSecs] = useState(secsToReset);
  useEffect(() => {
    setSecs(secsToReset);
    if (secsToReset <= 0) return;
    const id = setInterval(() => setSecs((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [secsToReset]);
  const d = Math.floor(secs / 86400);
  const h = Math.floor((secs % 86400) / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
}

function rankColor(rank: string) {
  const nobility = ["Knight", "Baron", "Viscount", "Count", "Marquis", "Duke"];
  const high     = ["Archdemon", "Archangel", "Eschatology", "Demonology"];
  if (rank === "Duke" || rank === "Marquis") return "text-yellow-400";
  if (nobility.includes(rank)) return "text-amber-400";
  if (high.includes(rank))     return "text-rose-400";
  return "text-muted-foreground";
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function KingdomRanksPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-5xl mx-auto space-y-8">
          <PageHeader
            title="Kingdom Ranks"
            description="Live weekly ranking — most active infernal citizens rise to the top of the Kingdom."
          />
          <KingdomRanksBoard guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── Board ────────────────────────────────────────────────────────────────────

function KingdomRanksBoard({ guildId }: { guildId: string }) {
  const [data, setData]     = useState<KrData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await apiGet<KrData>(`/api/guilds/${guildId}/kingdom-ranks/data`);
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load Kingdom Ranks data.");
    } finally {
      setLoading(false);
    }
  }, [guildId]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="w-4 h-4" />
        <AlertDescription className="flex items-center gap-4">
          {error}
          <Button size="sm" variant="outline" onClick={load}>Retry</Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!data) return null;

  const weekStartDate = new Date(data.weekStart).toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
  });

  return (
    <div className="space-y-6">
      {/* Summary cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetaCard
          icon={Timer}
          label="Resets In"
          value={<Countdown secs={data.secsToReset} />}
          sub={`Next Monday 00:00 UTC`}
          highlight
        />
        <MetaCard
          icon={Users}
          label="Active This Week"
          value={data.totalEligible.toLocaleString()}
          sub="Members with tracked activity"
        />
        <MetaCard
          icon={Flame}
          label="Week Started"
          value={weekStartDate}
          sub="Resets every Monday 00:00 UTC"
        />
      </div>

      {/* Ranking rule banner */}
      <RankingRuleBanner />

      {/* Leaderboard */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-primary" />
                Weekly Top 10
              </CardTitle>
              <CardDescription>
                Ranked by voice &amp; activity time · ties broken by DC earned this week
              </CardDescription>
            </div>
            <Button size="sm" variant="ghost" onClick={load} className="gap-1.5 text-muted-foreground">
              <RefreshCcw className="w-3.5 h-3.5" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {data.topUsers.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <Trophy className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p className="font-medium">No activity recorded yet this week.</p>
              <p className="text-sm mt-1">Rankings appear once members start earning DC or joining voice channels.</p>
            </div>
          ) : (
            <div className="divide-y divide-border/40">
              {data.topUsers.map((user) => (
                <LeaderboardRow key={user.discordId} user={user} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Eligibility rules */}
      <EligibilityCard />
    </div>
  );
}

// ─── Countdown ────────────────────────────────────────────────────────────────

function Countdown({ secs }: { secs: number }) {
  const label = useCountdown(secs);
  return <span>{label}</span>;
}

// ─── LeaderboardRow ───────────────────────────────────────────────────────────

function LeaderboardRow({ user }: { user: KrUser }) {
  const medal     = MEDAL[user.position - 1];
  const isPodium  = user.position <= 3;

  return (
    <div
      className={cn(
        "flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/30",
        isPodium && "bg-primary/3",
      )}
    >
      {/* Position */}
      <div className="w-10 text-center flex-shrink-0">
        {medal ? (
          <span className="text-xl leading-none">{medal}</span>
        ) : (
          <span className="text-sm font-bold text-muted-foreground">
            #{user.position}
          </span>
        )}
      </div>

      {/* Username + rank */}
      <div className="flex-1 min-w-0">
        <p className={cn(
          "font-semibold truncate",
          isPodium ? "text-foreground" : "text-foreground/80",
        )}>
          {user.username}
        </p>
        <p className={cn("text-xs font-medium", rankColor(user.economyRank))}>
          {user.economyRank}
        </p>
      </div>

      {/* Weekly active time */}
      <div className="text-right hidden sm:block flex-shrink-0 w-28">
        <p className="text-sm font-semibold text-foreground">{user.weeklyActiveFmt || "0s"}</p>
        <p className="text-xs text-muted-foreground">Active time</p>
      </div>

      {/* Weekly DC earned */}
      <div className="text-right flex-shrink-0 w-28">
        <p className="text-sm font-semibold text-foreground">
          {fmtNumber(user.weeklyDcEarned)} DC
        </p>
        <p className="text-xs text-muted-foreground">Earned this week</p>
      </div>

      {/* Balance (total) */}
      <div className="text-right hidden lg:block flex-shrink-0 w-28">
        <p className="text-sm text-muted-foreground">{fmtNumber(user.balance)} DC</p>
        <p className="text-xs text-muted-foreground">Wallet</p>
      </div>
    </div>
  );
}

// ─── Meta card ────────────────────────────────────────────────────────────────

function MetaCard({
  icon: Icon, label, value, sub, highlight,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <Card className={cn("border-border/50", highlight && "border-primary/20 bg-primary/5")}>
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon className={cn("w-4 h-4", highlight ? "text-primary" : "text-muted-foreground")} />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        <div className={cn("text-2xl font-bold font-mono", highlight ? "text-primary" : "text-foreground")}>
          {value}
        </div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ─── Ranking Rule Banner ──────────────────────────────────────────────────────

function RankingRuleBanner() {
  return (
    <div className="rounded-xl border border-border/50 bg-muted/20 p-4">
      <div className="flex items-center gap-2 mb-3">
        <ChevronUp className="w-4 h-4 text-primary" />
        <span className="text-sm font-semibold text-foreground">Ranking Criteria</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <div className="flex items-start gap-2">
          <Badge className="text-xs shrink-0 mt-0.5 bg-primary/20 text-primary border-primary/30 font-bold">1st</Badge>
          <div>
            <p className="font-medium text-foreground">Weekly Active Time</p>
            <p className="text-xs text-muted-foreground">Total voice + activity seconds this week</p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <Badge className="text-xs shrink-0 mt-0.5 bg-muted text-muted-foreground border-border font-bold">2nd</Badge>
          <div>
            <p className="font-medium text-foreground">DevilCoins Earned</p>
            <p className="text-xs text-muted-foreground">DC earned via grind &amp; tribute this week</p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <Badge className="text-xs shrink-0 mt-0.5 bg-muted text-muted-foreground border-border font-bold">3rd</Badge>
          <div>
            <p className="font-medium text-foreground">Economy Rank Tier</p>
            <p className="text-xs text-muted-foreground">Higher rank tier wins the tiebreak</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Eligibility Card ─────────────────────────────────────────────────────────

function EligibilityCard() {
  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Crown className="w-4 h-4 text-primary" />
          Eligibility &amp; Rules
        </CardTitle>
      </CardHeader>
      <CardContent className="grid sm:grid-cols-2 gap-4 text-sm text-muted-foreground">
        <ul className="space-y-2 list-disc list-inside">
          <li>Staff hierarchy is excluded from Kingdom Ranks eligibility.</li>
          <li>Sovereign, Consorts, Princes, Princesses, Chancellor, Legates, Centurion, and Legionnaires are excluded.</li>
          <li>All other members with any weekly activity are eligible.</li>
        </ul>
        <ul className="space-y-2 list-disc list-inside">
          <li>Rankings reset every <strong className="text-foreground">Monday at 00:00 UTC</strong>.</li>
          <li>Top 10 results are posted in the configured leaderboard channel automatically.</li>
          <li>Weekly stats accumulate from Monday 00:00 UTC to Sunday 23:59 UTC.</li>
        </ul>
      </CardContent>
    </Card>
  );
}
