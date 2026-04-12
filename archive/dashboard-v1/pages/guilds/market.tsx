import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";
import {
  ShoppingBag, Users, Star, Palette, Type, Gem, RefreshCcw,
  AlertCircle, Crown,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type MarketSummary = {
  guildId: string;
  totalUsers: number;
  usersWithSkins: number;
  usersWithTitles: number;
  usersWithRelics: number;
  usersWithBadges: number;
  totalOwnedSkins: number;
  totalOwnedTitles: number;
  mostPopularRank: string | null;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function pct(n: number, total: number) {
  if (!total) return 0;
  return Math.round((n / total) * 100);
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function MarketPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-5xl mx-auto space-y-8">
          <PageHeader
            title="Market"
            description="Cosmetics ownership overview — skins, titles, relics, and badges across your server's economy."
          />
          <MarketView guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── MarketView ───────────────────────────────────────────────────────────────

function MarketView({ guildId }: { guildId: string }) {
  const [data, setData]       = useState<MarketSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await apiGet<MarketSummary>(`/api/guilds/${guildId}/market-summary`);
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load market data.");
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

  const total = data.totalUsers;

  return (
    <div className="space-y-6">
      {/* Top stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Total Members"
          value={total.toLocaleString()}
          sub="In economy system"
        />
        <StatCard
          icon={Palette}
          label="Skins Owned"
          value={data.totalOwnedSkins.toLocaleString()}
          sub={`${data.usersWithSkins} members have a skin equipped`}
          accent
        />
        <StatCard
          icon={Type}
          label="Titles Owned"
          value={data.totalOwnedTitles.toLocaleString()}
          sub={`${data.usersWithTitles} members with equipped title`}
          accent
        />
        <StatCard
          icon={Gem}
          label="Relics Equipped"
          value={data.usersWithRelics.toLocaleString()}
          sub="Members with active relic"
          accent
        />
      </div>

      {/* Adoption breakdown */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-primary" />
                Cosmetics Adoption
              </CardTitle>
              <CardDescription>
                Percentage of economy members with each cosmetic type equipped
              </CardDescription>
            </div>
            <Button size="sm" variant="ghost" onClick={load} className="gap-1.5 text-muted-foreground">
              <RefreshCcw className="w-3.5 h-3.5" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <AdoptionBar icon={Palette} label="Skins"   count={data.usersWithSkins}  total={total} />
          <AdoptionBar icon={Type}    label="Titles"  count={data.usersWithTitles} total={total} />
          <AdoptionBar icon={Gem}     label="Relics"  count={data.usersWithRelics} total={total} />
          <AdoptionBar icon={Star}    label="Badges"  count={data.usersWithBadges} total={total} />
        </CardContent>
      </Card>

      {/* Most popular rank */}
      {data.mostPopularRank && (
        <Card className="border-border/50">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Crown className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Most Common Rank</p>
              <p className="font-semibold text-foreground text-lg">{data.mostPopularRank}</p>
              <p className="text-xs text-muted-foreground">The rank held by the most members in this guild</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({
  icon: Icon, label, value, sub, accent,
}: { icon: React.ElementType; label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <Card className="border-border/50">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon className={`w-4 h-4 ${accent ? "text-primary" : "text-muted-foreground"}`} />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

function AdoptionBar({
  icon: Icon, label, count, total,
}: { icon: React.ElementType; label: string; count: number; total: number }) {
  const p = pct(count, total);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Icon className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-foreground/80">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-xs">{count.toLocaleString()} members</span>
          <Badge variant="outline" className="text-xs px-1.5 font-mono">
            {p}%
          </Badge>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-muted/50 overflow-hidden">
        <div
          className="h-full rounded-full bg-primary/70 transition-all duration-700"
          style={{ width: `${p}%` }}
        />
      </div>
    </div>
  );
}
