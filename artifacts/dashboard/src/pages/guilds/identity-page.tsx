import { useState, useEffect } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiGet } from "@/lib/api";
import { Crown, Coins, Shield, Info, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type RankEntry = {
  name: string;
  cost: number;
  taxRate: number;
  purchasable: boolean;
  group: string;
  defaultCooldownSeconds: number;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtNumber(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function fmtCooldown(s: number) {
  if (!s) return "—";
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h`;
  return `${m}m`;
}

function groupColor(group: string) {
  if (group === "nobility") return "border-amber-500/30 bg-amber-500/10 text-amber-400";
  if (group === "staff")    return "border-rose-500/30 bg-rose-500/10 text-rose-400";
  return "border-border/50 bg-muted/30 text-muted-foreground";
}

function rankTextColor(group: string, name: string) {
  if (name === "Duke" || name === "Marquis") return "text-yellow-400";
  if (group === "nobility")                   return "text-amber-400";
  if (group === "staff")                      return "text-rose-400";
  return "text-foreground";
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function IdentityPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-5xl mx-auto space-y-8">
          <PageHeader
            title="Identity & Rank Registry"
            description="The canonical centralized rank system — cost, tax rates, and cooldowns used across the entire bot."
          />
          <RankRegistry />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── Registry ─────────────────────────────────────────────────────────────────

function RankRegistry() {
  const [ranks, setRanks]   = useState<RankEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    apiGet<RankEntry[]>("/api/ranks")
      .then(setRanks)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load rank registry."))
      .finally(() => setLoading(false));
  }, []);

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
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  // Split into groups
  const publicRanks  = ranks.filter((r) => r.purchasable || r.name === "Forsaken");
  const staffRanks   = ranks.filter((r) => r.group === "staff");

  const totalCost    = publicRanks.filter((r) => r.purchasable).reduce((a, r) => a + r.cost, 0);

  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryCard icon={Crown} label="Public Ranks" value={String(publicRanks.filter((r) => r.purchasable).length)} sub="Purchasable by players" />
        <SummaryCard icon={Coins} label="Total Cost (max)" value={fmtNumber(totalCost) + " DC"} sub="To reach Duke from Forsaken" />
        <SummaryCard icon={Shield} label="Staff Roles" value={String(staffRanks.length)} sub="Excluded from economy system" />
      </div>

      {/* System note */}
      <div className="rounded-xl border border-border/50 bg-muted/20 p-4 flex gap-3 text-sm">
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <p className="text-muted-foreground">
          This is the <strong className="text-foreground">single source of truth</strong> for rank configuration.
          It drives ascension, market pricing, tax rates, Kingdom Ranks eligibility, and identity card rendering.
          Per-guild role overrides are configured on the <strong className="text-foreground">Ranks &amp; Roles</strong> page.
        </p>
      </div>

      {/* Public rank table */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-primary" />
            Economy Rank Progression
          </CardTitle>
          <CardDescription>
            From Forsaken (default start) to Duke (highest public rank)
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {/* Header */}
          <div className="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr] gap-2 px-6 py-2 text-xs font-medium text-muted-foreground border-b border-border/40 bg-muted/10">
            <span>Rank</span>
            <span className="text-right">Ascension Cost</span>
            <span className="text-right">Tax Rate</span>
            <span className="text-right">Default Cooldown</span>
            <span className="text-center">Purchasable</span>
          </div>
          <div className="divide-y divide-border/30">
            {publicRanks.map((rank, i) => (
              <div
                key={rank.name}
                className={cn(
                  "grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr] gap-2 px-6 py-3.5 items-center",
                  "hover:bg-muted/20 transition-colors text-sm",
                )}
              >
                {/* Rank name + tier badge */}
                <div className="flex items-center gap-2.5">
                  <span className="text-xs text-muted-foreground w-5 shrink-0 font-mono">
                    {rank.name === "Forsaken" ? "0" : i}
                  </span>
                  <span className={cn("font-semibold", rankTextColor(rank.group, rank.name))}>
                    {rank.name}
                  </span>
                  {rank.group === "nobility" && (
                    <Badge className="text-[10px] h-4 px-1.5 border-amber-500/30 bg-amber-500/10 text-amber-400">
                      Nobility
                    </Badge>
                  )}
                </div>
                {/* Cost */}
                <div className="text-right font-mono text-foreground/80">
                  {rank.cost === 0 ? <span className="text-muted-foreground">—</span> : `${fmtNumber(rank.cost)} DC`}
                </div>
                {/* Tax rate */}
                <div className="text-right text-foreground/70 font-mono">
                  {(rank.taxRate * 100).toFixed(0)}%
                </div>
                {/* Cooldown */}
                <div className="text-right text-muted-foreground font-mono">
                  {fmtCooldown(rank.defaultCooldownSeconds)}
                </div>
                {/* Purchasable */}
                <div className="flex justify-center">
                  {rank.purchasable
                    ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    : <XCircle     className="w-4 h-4 text-muted-foreground/40" />}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Staff table */}
      {staffRanks.length > 0 && (
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="w-4 h-4 text-rose-400" />
              Staff Hierarchy
            </CardTitle>
            <CardDescription>
              These roles are managed by the server. They are never assigned or removed by the economy system.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {staffRanks.map((r) => (
                <Badge
                  key={r.name}
                  className={cn("text-xs", groupColor(r.group))}
                >
                  {r.name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Summary card ─────────────────────────────────────────────────────────────

function SummaryCard({
  icon: Icon, label, value, sub,
}: { icon: React.ElementType; label: string; value: string; sub?: string }) {
  return (
    <Card className="border-border/50">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}
