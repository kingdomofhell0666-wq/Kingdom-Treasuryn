import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { useGetGuildStats, useGetGuildConfig } from "@workspace/api-client-react";
import { Flame, Crown, Medal } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";

type LeaderboardEntry = {
  discord_id: string;
  username: string;
  balance: number;
  rank: string;
  taxes_paid: number;
};

export default function TreasuryPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Treasury</h1>
            <p className="text-muted-foreground">Kingdom wealth overview and top earners.</p>
          </div>
          <TreasuryView guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function TreasuryView({ guildId }: { guildId: string }) {
  const { data: stats } = useGetGuildStats(guildId);
  const { data: config } = useGetGuildConfig(guildId);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const currency = config?.currencyName ?? "DevilCoins";
  const icon = config?.currencyIcon ?? "🪙";

  const fetchLb = useCallback(async () => {
    try {
      const data = await apiGet<{ entries: LeaderboardEntry[] }>(`/api/guilds/${guildId}/leaderboard/data`);
      setLeaderboard(data.entries);
    } finally { setLoading(false); }
  }, [guildId]);

  useEffect(() => { fetchLb(); }, [fetchLb]);

  const MEDALS = ["🥇","🥈","🥉"];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Treasury Balance", value: `${icon} ${(stats?.totalTreasuryBalance ?? 0).toLocaleString()}`, icon: Flame },
          { label: "Total Wallets", value: `${icon} ${(stats?.totalWalletBalance ?? 0).toLocaleString()}`, icon: Flame },
          { label: "Total Members", value: String(stats?.totalUsers ?? 0), icon: Crown },
          { label: "Taxes Collected", value: `${icon} ${(stats?.totalTaxesPaid ?? 0).toLocaleString()}`, icon: Medal },
        ].map(stat => (
          <Card key={stat.label} className="bg-card border-border/60">
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
              <p className="text-lg font-bold text-foreground">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-card border-border/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Crown className="w-5 h-5 text-yellow-500" />
            Wealth Leaderboard
          </CardTitle>
          <CardDescription>Top 20 souls by {currency} balance.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8"><Spinner className="w-6 h-6 text-primary" /></div>
          ) : leaderboard.length === 0 ? (
            <p className="text-center text-muted-foreground py-8 text-sm">No economy data yet.</p>
          ) : (
            <div className="space-y-1">
              {leaderboard.map((entry, i) => (
                <div key={entry.discord_id} className="flex items-center gap-3 py-2 px-3 rounded-md hover:bg-muted/30 transition-colors">
                  <span className="text-sm w-6 text-center shrink-0">
                    {i < 3 ? MEDALS[i] : <span className="text-muted-foreground font-mono">{i + 1}</span>}
                  </span>
                  <span className="flex-1 font-medium text-sm">{entry.username}</span>
                  <Badge variant="outline" className="text-xs shrink-0">{entry.rank}</Badge>
                  <span className="font-mono text-sm text-primary shrink-0">
                    {icon} {entry.balance.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
