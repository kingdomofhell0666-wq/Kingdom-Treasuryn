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
  Package, RefreshCcw, AlertCircle, Palette, Type, Gem, Star, Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type InvUser = {
  discordId: string;
  username: string;
  rank: string;
  balance: number;
  equippedSkin: string | null;
  equippedTitle: string | null;
  equippedRelic: string | null;
  badgeCount: number;
  ownedSkins: number;
  ownedTitles: number;
};

type InvData = {
  guildId: string;
  totalWithCosmetics: number;
  users: InvUser[];
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtNumber(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function rankColor(rank: string) {
  if (["Duke", "Marquis"].includes(rank))                                 return "text-yellow-400";
  if (["Knight","Baron","Viscount","Count"].includes(rank))               return "text-amber-400";
  if (["Archdemon","Archangel","Eschatology","Demonology"].includes(rank)) return "text-rose-400";
  return "text-muted-foreground";
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-5xl mx-auto space-y-8">
          <PageHeader
            title="Inventory"
            description="Browse cosmetic items owned and equipped by your server members."
          />
          <InventoryView guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── InventoryView ────────────────────────────────────────────────────────────

function InventoryView({ guildId }: { guildId: string }) {
  const [data, setData]       = useState<InvData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await apiGet<InvData>(`/api/guilds/${guildId}/inventory-summary`);
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load inventory data.");
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

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SumCard icon={Users}   label="Members With Cosmetics" value={data.totalWithCosmetics.toLocaleString()} sub="With any cosmetic item equipped" />
        <SumCard icon={Palette} label="Showing"                value={`${data.users.length} members`}           sub="Top holders by wallet balance" />
        <SumCard icon={Package} label="Item Types Tracked"     value="4"                                        sub="Skins · Titles · Relics · Badges" />
      </div>

      {/* Member table */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5 text-primary" />
                Member Inventories
              </CardTitle>
              <CardDescription>
                Top {data.users.length} members by wallet balance who have cosmetics equipped
              </CardDescription>
            </div>
            <Button size="sm" variant="ghost" onClick={load} className="gap-1.5 text-muted-foreground">
              <RefreshCcw className="w-3.5 h-3.5" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {data.users.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <Package className="w-10 h-10 mx-auto mb-3 opacity-20" />
              <p className="font-medium">No cosmetics equipped yet.</p>
              <p className="text-sm mt-1">Members who equip skins, titles, relics, or badges will appear here.</p>
            </div>
          ) : (
            <>
              {/* Header row */}
              <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-2 px-6 py-2 text-xs font-medium text-muted-foreground border-b border-border/40 bg-muted/10">
                <span>Member</span>
                <span className="text-center">Skin</span>
                <span className="text-center">Title</span>
                <span className="text-center">Relic</span>
                <span className="text-center">Badges</span>
                <span className="text-right">Wallet</span>
              </div>
              <div className="divide-y divide-border/30">
                {data.users.map((u) => (
                  <InventoryRow key={u.discordId} user={u} />
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Row ──────────────────────────────────────────────────────────────────────

function InventoryRow({ user }: { user: InvUser }) {
  function CosmPill({ value, icon: Icon }: { value: string | null; icon: React.ElementType }) {
    if (!value) return <span className="text-muted-foreground/40 text-xs">—</span>;
    return (
      <Badge variant="outline" className="text-xs gap-1 max-w-[90px] truncate">
        <Icon className="w-2.5 h-2.5 shrink-0" />
        <span className="truncate">{value}</span>
      </Badge>
    );
  }

  return (
    <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-2 px-6 py-3.5 items-center hover:bg-muted/20 transition-colors text-sm">
      {/* Member */}
      <div className="min-w-0">
        <p className="font-semibold text-foreground truncate">{user.username}</p>
        <p className={cn("text-xs font-medium", rankColor(user.rank))}>{user.rank}</p>
      </div>
      {/* Skin */}
      <div className="flex justify-center">
        <CosmPill value={user.equippedSkin} icon={Palette} />
      </div>
      {/* Title */}
      <div className="flex justify-center">
        <CosmPill value={user.equippedTitle} icon={Type} />
      </div>
      {/* Relic */}
      <div className="flex justify-center">
        <CosmPill value={user.equippedRelic} icon={Gem} />
      </div>
      {/* Badges */}
      <div className="flex justify-center">
        {user.badgeCount > 0 ? (
          <Badge variant="outline" className="text-xs gap-1">
            <Star className="w-2.5 h-2.5" />
            {user.badgeCount}
          </Badge>
        ) : (
          <span className="text-muted-foreground/40 text-xs">—</span>
        )}
      </div>
      {/* Wallet */}
      <div className="text-right text-muted-foreground font-mono text-xs">
        {fmtNumber(user.balance)} DC
      </div>
    </div>
  );
}

// ─── Summary card ─────────────────────────────────────────────────────────────

function SumCard({ icon: Icon, label, value, sub }: {
  icon: React.ElementType; label: string; value: string; sub?: string;
}) {
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
