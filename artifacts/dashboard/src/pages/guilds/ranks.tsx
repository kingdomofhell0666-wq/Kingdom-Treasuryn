import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPut, apiDelete } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Crown, Save, Trash2, Clock } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

// Canonical public Kingdom ranks — the only ranks players can ascend through.
// Excludes Forsaken (starting state) and Chancellor (staff/moderator role).
const PUBLIC_KINGDOM_RANKS = [
  "Vermin","Corrupted","Folklore","Mythology","Demonology",
  "Eschatology","Archangel","Archdemon",
  "Knight","Baron","Viscount","Count","Marquis","Duke",
];

type RankRole = { rankName: string; roleId: string; removePrevious: boolean };
type Cooldown = { rankName: string; cooldownSeconds: number };
type GuildRole = { id: string; name: string; color: number };

function hex(color: number) { return `#${color.toString(16).padStart(6, "0")}`; }
function fmtCooldown(s: number) {
  if (!s) return "No cooldown";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return [h && `${h}h`, m && `${m}m`, (!h && !m) && `${s}s`].filter(Boolean).join(" ");
}

export default function RanksPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-5xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Ranks & Roles</h1>
            <p className="text-muted-foreground">Map Kingdom ranks to Discord roles and configure ascension cooldowns.</p>
          </div>
          <RanksManager guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function RanksManager({ guildId }: { guildId: string }) {
  const { toast } = useToast();
  const { data: guild } = useGetGuild(guildId);
  const [rankRoles, setRankRoles] = useState<Record<string, RankRole>>({});
  const [cooldowns, setCooldowns] = useState<Record<string, number>>({});
  const [cooldownInputs, setCooldownInputs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const roles: GuildRole[] = (guild as { roles?: GuildRole[] })?.roles ?? [];

  const fetch = useCallback(async () => {
    try {
      const [rrData, cdData] = await Promise.all([
        apiGet<RankRole[]>(`/api/guilds/${guildId}/rank-roles`),
        apiGet<Cooldown[]>(`/api/guilds/${guildId}/rank-cooldowns`),
      ]);
      const rrMap: Record<string, RankRole> = {};
      for (const r of rrData) rrMap[r.rankName] = r;
      setRankRoles(rrMap);

      const cdMap: Record<string, number> = {};
      const cdInputMap: Record<string, string> = {};
      for (const c of cdData) {
        cdMap[c.rankName] = c.cooldownSeconds;
        cdInputMap[c.rankName] = String(c.cooldownSeconds / 3600);
      }
      setCooldowns(cdMap);
      setCooldownInputs(cdInputMap);
    } finally {
      setLoading(false);
    }
  }, [guildId]);

  useEffect(() => { fetch(); }, [fetch]);

  const saveRankRole = async (rank: string) => {
    const rr = rankRoles[rank];
    if (!rr?.roleId) return;
    setSaving(`rr-${rank}`);
    try {
      await apiPut(`/api/guilds/${guildId}/rank-roles/${encodeURIComponent(rank)}`, {
        roleId: rr.roleId,
        removePrevious: rr.removePrevious ?? true,
      });
      toast({ title: "Saved", description: `Role mapping for ${rank} updated.` });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally { setSaving(null); }
  };

  const clearRankRole = async (rank: string) => {
    try {
      await apiDelete(`/api/guilds/${guildId}/rank-roles/${encodeURIComponent(rank)}`);
      setRankRoles(prev => { const n = { ...prev }; delete n[rank]; return n; });
      toast({ title: "Cleared", description: `Role mapping for ${rank} removed.` });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    }
  };

  const saveCooldown = async (rank: string) => {
    const hours = parseFloat(cooldownInputs[rank] || "0");
    const secs = Math.max(0, Math.round(hours * 3600));
    setSaving(`cd-${rank}`);
    try {
      await apiPut(`/api/guilds/${guildId}/rank-cooldowns/${encodeURIComponent(rank)}`, { cooldownSeconds: secs });
      setCooldowns(prev => ({ ...prev, [rank]: secs }));
      toast({ title: "Saved", description: `Cooldown for ${rank} set to ${fmtCooldown(secs)}.` });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally { setSaving(null); }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  return (
    <div className="space-y-3">
      {PUBLIC_KINGDOM_RANKS.map(rank => {
        const rr = rankRoles[rank];
        const cd = cooldowns[rank] ?? 0;
        const role = roles.find(r => r.id === rr?.roleId);
        return (
          <Card key={rank} className="bg-card border-border/60">
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Crown className="w-4 h-4 text-primary" />
                    <span className="font-semibold">{rank}</span>
                    {role && (
                      <Badge style={{ background: role.color ? `${hex(role.color)}22` : undefined, borderColor: role.color ? hex(role.color) : undefined, color: role.color ? hex(role.color) : undefined }}>
                        @{role.name}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={rr?.roleId ?? ""}
                      onValueChange={(v) => setRankRoles(prev => ({ ...prev, [rank]: { rankName: rank, roleId: v, removePrevious: prev[rank]?.removePrevious ?? true } }))}
                    >
                      <SelectTrigger className="h-8 text-xs flex-1">
                        <SelectValue placeholder="Select Discord role…" />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map(r => (
                          <SelectItem key={r.id} value={r.id} className="text-xs">
                            <span className="flex items-center gap-2">
                              {r.color ? <span className="w-2 h-2 rounded-full inline-block" style={{ background: hex(r.color) }} /> : null}
                              {r.name}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {rr?.roleId && (
                      <Button size="sm" onClick={() => saveRankRole(rank)} disabled={saving === `rr-${rank}`} className="gap-1 shrink-0">
                        {saving === `rr-${rank}` ? <Spinner className="w-3 h-3" /> : <Save className="w-3 h-3" />}
                        Save
                      </Button>
                    )}
                    {rr?.roleId && (
                      <Button size="sm" variant="outline" onClick={() => clearRankRole(rank)} className="text-destructive hover:text-destructive shrink-0">
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                  {rr?.roleId && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Switch
                        checked={rr.removePrevious ?? true}
                        onCheckedChange={(v) => setRankRoles(prev => ({ ...prev, [rank]: { ...prev[rank], removePrevious: v } }))}
                        id={`rp-${rank}`}
                      />
                      <Label htmlFor={`rp-${rank}`} className="text-xs cursor-pointer">Remove previous rank roles on ascend</Label>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    Ascension Cooldown
                    {cd > 0 && <Badge variant="outline" className="text-xs">{fmtCooldown(cd)}</Badge>}
                  </div>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      min="0"
                      step="0.5"
                      placeholder="Hours (0 = none)"
                      className="h-8 text-xs"
                      value={cooldownInputs[rank] ?? ""}
                      onChange={(e) => setCooldownInputs(prev => ({ ...prev, [rank]: e.target.value }))}
                    />
                    <Button size="sm" onClick={() => saveCooldown(rank)} disabled={saving === `cd-${rank}`} className="gap-1 shrink-0">
                      {saving === `cd-${rank}` ? <Spinner className="w-3 h-3" /> : <Save className="w-3 h-3" />}
                      Set
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
