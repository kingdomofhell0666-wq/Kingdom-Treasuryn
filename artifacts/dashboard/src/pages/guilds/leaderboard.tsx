import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPatch } from "@/lib/api";
import { useGetGuild, useGetGuildConfig } from "@workspace/api-client-react";
import { Trophy, Save, Eye, AlertCircle } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

const ENDPOINT = (guildId: string) => `/api/guilds/${guildId}/leaderboard`;

const DEFAULT_SETTINGS = {
  enabled: false,
  leaderboardType: "wealth",
  postFrequency: "weekly",
  postChannelId: null as string | null,
  postHour: 20,
  postMinute: 0,
  postDayOfWeek: 0 as number | null,
  postDayOfMonth: 1 as number | null,
  timezone: "UTC",
  lastPostedAt: null as string | null,
};

type LeaderboardSettings = typeof DEFAULT_SETTINGS;

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const MINUTES = [0, 15, 30, 45];
const DAYS_OF_WEEK = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
const TIMEZONES = [
  "UTC","America/New_York","America/Chicago","America/Denver","America/Los_Angeles",
  "Europe/London","Europe/Berlin","Europe/Paris","Asia/Tokyo","Asia/Singapore","Australia/Sydney",
];

const SAMPLE_ENTRIES = [
  { name: "Darkblade", balance: 4_200_000, rank: "Duke" },
  { name: "Infernal_Rex", balance: 2_800_000, rank: "Baron" },
  { name: "SoulHarvest", balance: 1_500_000, rank: "Knight" },
  { name: "VoidWalker", balance: 890_000, rank: "Archdemon" },
  { name: "CrimsonTide", balance: 450_000, rank: "Archangel" },
];

const MEDALS = ["🥇", "🥈", "🥉"];

const BOARD_META: Record<string, { emoji: string; label: string; color: string }> = {
  wealth:  { emoji: "💰", label: "Wealth",  color: "border-yellow-500" },
  grind:   { emoji: "⛏",  label: "Grind",   color: "border-red-700" },
  tribute: { emoji: "👑", label: "Tribute", color: "border-red-900" },
};

type LoadState = "loading" | "ok" | "error";

export default function LeaderboardPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-3xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Leaderboard</h1>
            <p className="text-muted-foreground">
              Schedule automatic leaderboard posts to a specific channel.
              Rankings use the same balance order as <strong>/identity</strong>.
            </p>
          </div>
          <LeaderboardForm guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function LeaderboardForm({ guildId }: { guildId: string }) {
  const { toast } = useToast();
  const { data: guild } = useGetGuild(guildId);
  const { data: config } = useGetGuildConfig(guildId);

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [settings, setSettings] = useState<LeaderboardSettings>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const textChannels = (guild as { channels?: { id: string; name: string }[] })?.channels ?? [];
  const currencyName = config?.currencyName ?? "DevilCoins";
  const currencyIcon = config?.currencyIcon ?? "🪙";
  const endpoint = ENDPOINT(guildId);

  const fetchSettings = useCallback(async () => {
    setLoadState("loading");
    setLoadError(null);
    try {
      const data = await apiGet<LeaderboardSettings>(endpoint);
      setSettings({ ...DEFAULT_SETTINGS, ...data });
      setLoadState("ok");
    } catch (e: unknown) {
      const msg = (e as Error).message;
      console.error(`[LeaderboardPage] Failed to load settings from ${endpoint}:`, msg);
      setLoadError(msg);
      // Use fallback defaults so the form renders even if the API fails
      setSettings(DEFAULT_SETTINGS);
      setLoadState("error");
    }
  }, [endpoint]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const save = async () => {
    setSaving(true);
    try {
      const data = await apiPatch<LeaderboardSettings>(endpoint, settings);
      setSettings({ ...DEFAULT_SETTINGS, ...data });
      setLoadState("ok");
      setLoadError(null);
      toast({ title: "Saved", description: "Leaderboard schedule updated." });
    } catch (e: unknown) {
      toast({ title: "Save failed", description: (e as Error).message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  if (loadState === "loading") {
    return (
      <div className="flex items-center justify-center py-16 gap-3 text-muted-foreground">
        <Spinner className="w-6 h-6 text-primary" />
        <span className="text-sm">Loading leaderboard settings…</span>
      </div>
    );
  }

  const selectedChannel = textChannels.find(c => c.id === settings.postChannelId);

  return (
    <div className="space-y-6">
      {loadState === "error" && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Could not load saved settings</strong> — showing defaults.{" "}
            <span className="font-mono text-xs break-all">{loadError}</span>
            <Button variant="link" size="sm" className="ml-2 h-auto p-0 text-xs" onClick={fetchSettings}>
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Card className="bg-card border-border/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Trophy className="w-5 h-5 text-yellow-500" />
            Leaderboard Schedule
          </CardTitle>
          <CardDescription>
            The bot posts the top players to your chosen channel on the schedule below.
            Only that channel receives the post — no other channels are affected.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-3">
            <Switch
              checked={settings.enabled}
              onCheckedChange={(v) => setSettings(s => ({ ...s, enabled: v }))}
              id="lb-enabled"
            />
            <Label htmlFor="lb-enabled" className="text-sm cursor-pointer">
              Enable automatic leaderboard posting
            </Label>
            {settings.enabled && settings.postChannelId && (
              <Badge className="text-xs bg-green-600/20 text-green-400 border border-green-600/30">
                Active
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Board Type</Label>
              <Select value={settings.leaderboardType} onValueChange={(v) => setSettings(s => ({ ...s, leaderboardType: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="wealth">💰 Wealth (Balance)</SelectItem>
                  <SelectItem value="grind">⛏ Grind (Times mined)</SelectItem>
                  <SelectItem value="tribute">👑 Tribute (Daily collected)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Same ranking as <strong>/identity</strong></p>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Post Channel</Label>
              <Select
                value={settings.postChannelId ?? ""}
                onValueChange={(v) => setSettings(s => ({ ...s, postChannelId: v || null }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a channel…" />
                </SelectTrigger>
                <SelectContent>
                  {textChannels.length > 0
                    ? textChannels.map(c => <SelectItem key={c.id} value={c.id}>#{c.name}</SelectItem>)
                    : <SelectItem value="" disabled>No channels available</SelectItem>
                  }
                </SelectContent>
              </Select>
              {settings.postChannelId && !selectedChannel && (
                <p className="text-xs text-yellow-500">⚠ Channel not found — bot may not have access.</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Posting Frequency</Label>
              <Select value={settings.postFrequency} onValueChange={(v) => setSettings(s => ({ ...s, postFrequency: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Every day</SelectItem>
                  <SelectItem value="weekly">Every week</SelectItem>
                  <SelectItem value="monthly">Every month</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Timezone</Label>
              <Select value={settings.timezone} onValueChange={(v) => setSettings(s => ({ ...s, timezone: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TIMEZONES.map(tz => <SelectItem key={tz} value={tz}>{tz}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Post Time — Hour</Label>
              <Select value={String(settings.postHour)} onValueChange={(v) => setSettings(s => ({ ...s, postHour: Number(v) }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {HOURS.map(h => <SelectItem key={h} value={String(h)}>{String(h).padStart(2, "0")}:00</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Post Time — Minute</Label>
              <Select value={String(settings.postMinute)} onValueChange={(v) => setSettings(s => ({ ...s, postMinute: Number(v) }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {MINUTES.map(m => <SelectItem key={m} value={String(m)}>:{String(m).padStart(2, "0")}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {settings.postFrequency === "weekly" && (
              <div className="space-y-1.5 md:col-span-2">
                <Label className="text-xs font-medium">Day of Week</Label>
                <Select
                  value={String(settings.postDayOfWeek ?? 0)}
                  onValueChange={(v) => setSettings(s => ({ ...s, postDayOfWeek: Number(v) }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {DAYS_OF_WEEK.map((d, i) => <SelectItem key={i} value={String(i)}>{d}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            )}

            {settings.postFrequency === "monthly" && (
              <div className="space-y-1.5 md:col-span-2">
                <Label className="text-xs font-medium">Day of Month</Label>
                <Select
                  value={String(settings.postDayOfMonth ?? 1)}
                  onValueChange={(v) => setSettings(s => ({ ...s, postDayOfMonth: Number(v) }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                      <SelectItem key={d} value={String(d)}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {settings.lastPostedAt && (
            <p className="text-xs text-muted-foreground border-t border-border/40 pt-3">
              Last posted: {new Date(settings.lastPostedAt).toLocaleString()}
            </p>
          )}
        </CardContent>
        <CardFooter className="flex flex-wrap gap-3">
          <Button onClick={save} disabled={saving} className="gap-2">
            {saving ? <Spinner className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            Save Schedule
          </Button>
          <Button variant="outline" onClick={() => setShowPreview(v => !v)} className="gap-2">
            <Eye className="w-4 h-4" />
            {showPreview ? "Hide Preview" : "Preview Message"}
          </Button>
        </CardFooter>
      </Card>

      {showPreview && (
        <Card className="bg-card border-border/60">
          <CardHeader>
            <CardTitle className="text-sm">Discord Message Preview</CardTitle>
            <CardDescription>Sample embed showing how this will appear in Discord.</CardDescription>
          </CardHeader>
          <CardContent>
            <LeaderboardPreview
              settings={settings}
              currencyName={currencyName}
              currencyIcon={currencyIcon}
              channelName={selectedChannel?.name ?? "leaderboard"}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function LeaderboardPreview({
  settings, currencyName, currencyIcon, channelName,
}: {
  settings: LeaderboardSettings;
  currencyName: string;
  currencyIcon: string;
  channelName: string;
}) {
  const meta = BOARD_META[settings.leaderboardType] ?? BOARD_META.wealth;
  const freq = { daily: "Daily", weekly: "Weekly", monthly: "Monthly" }[settings.postFrequency] ?? "";
  const dateStr = new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Posting to <strong className="text-foreground">#{channelName}</strong>
      </p>
      <div className={`rounded-md border-l-4 bg-[#2b2d31] p-4 ${meta.color} max-w-md`}>
        <div className="space-y-3">
          <div>
            <p className="text-white font-semibold text-sm">
              {meta.emoji}  {freq} {meta.label} Leaderboard
            </p>
            <p className="text-[#b9bbbe] text-[10px] mt-0.5">Kingdom of Hell  ·  Kingdom Treasury</p>
          </div>
          <div className="space-y-2">
            {SAMPLE_ENTRIES.map((e, i) => (
              <div key={e.name} className="text-xs text-[#dcddde] leading-snug">
                <span>
                  {i < 3 ? MEDALS[i] : `#${i + 1}`}{" "}
                  <span className="font-bold">{e.name}</span>
                  {"  ·  "}{currencyIcon}{" "}
                  <code className="bg-[#1e1f22] px-1 rounded text-[10px]">{e.balance.toLocaleString()}</code>
                  {" "}{currencyName}
                </span>
                <br />
                <span className="text-[#8d9096] ml-4">Kingdom rank — {e.rank}</span>
              </div>
            ))}
          </div>
          <p className="text-[#72767d] text-[10px] border-t border-[#3d3f45] pt-2">
            Ranked by {meta.label.toLowerCase()}  ·  {dateStr}
          </p>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        Ranking order is identical to <strong>/identity</strong> — balance descending.
      </p>
    </div>
  );
}
