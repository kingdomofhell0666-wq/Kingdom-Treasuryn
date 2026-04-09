import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPatch } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Trophy, Save } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

type LeaderboardSettings = {
  enabled: boolean;
  leaderboardType: string;
  postFrequency: string;
  postChannelId: string | null;
  postHour: number;
  postMinute: number;
  postDayOfWeek: number | null;
  postDayOfMonth: number | null;
  timezone: string;
  lastPostedAt: string | null;
};

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const MINUTES = [0, 15, 30, 45];
const DAYS_OF_WEEK = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
const TIMEZONES = ["UTC","America/New_York","America/Chicago","America/Denver","America/Los_Angeles","Europe/London","Europe/Berlin","Asia/Tokyo","Australia/Sydney"];

export default function LeaderboardPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-3xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Leaderboard</h1>
            <p className="text-muted-foreground">Schedule automatic leaderboard announcements in your server.</p>
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
  const [settings, setSettings] = useState<LeaderboardSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const textChannels = (guild as { channels?: { id: string; name: string }[] })?.channels ?? [];

  const fetchSettings = useCallback(async () => {
    try {
      const data = await apiGet<LeaderboardSettings>(`/api/guilds/${guildId}/leaderboard`);
      setSettings(data);
    } finally { setLoading(false); }
  }, [guildId]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await apiPatch<LeaderboardSettings>(`/api/guilds/${guildId}/leaderboard`, settings);
      setSettings(updated);
      toast({ title: "Saved", description: "Leaderboard schedule updated." });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally { setSaving(false); }
  };

  if (loading || !settings) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  return (
    <Card className="bg-card border-border/60">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Trophy className="w-5 h-5 text-yellow-500" />
          Leaderboard Schedule
        </CardTitle>
        <CardDescription>Post the top players to a channel on a recurring schedule.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-3">
          <Switch
            checked={settings.enabled}
            onCheckedChange={(v) => setSettings(s => s ? { ...s, enabled: v } : s)}
            id="lb-enabled"
          />
          <Label htmlFor="lb-enabled" className="text-sm cursor-pointer">Enable automatic leaderboard posting</Label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Board Type</Label>
            <Select value={settings.leaderboardType} onValueChange={(v) => setSettings(s => s ? { ...s, leaderboardType: v } : s)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="wealth">Wealth (Balance)</SelectItem>
                <SelectItem value="grind">Grind (Times mined)</SelectItem>
                <SelectItem value="tribute">Tribute (Times collected)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Post Frequency</Label>
            <Select value={settings.postFrequency} onValueChange={(v) => setSettings(s => s ? { ...s, postFrequency: v } : s)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Post Channel</Label>
            <Select value={settings.postChannelId ?? ""} onValueChange={(v) => setSettings(s => s ? { ...s, postChannelId: v || null } : s)}>
              <SelectTrigger><SelectValue placeholder="Select channel…" /></SelectTrigger>
              <SelectContent>
                {textChannels.map(c => <SelectItem key={c.id} value={c.id}>#{c.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Timezone</Label>
            <Select value={settings.timezone} onValueChange={(v) => setSettings(s => s ? { ...s, timezone: v } : s)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {TIMEZONES.map(tz => <SelectItem key={tz} value={tz}>{tz}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Post Hour (local)</Label>
            <Select value={String(settings.postHour)} onValueChange={(v) => setSettings(s => s ? { ...s, postHour: Number(v) } : s)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {HOURS.map(h => <SelectItem key={h} value={String(h)}>{String(h).padStart(2,"0")}:00</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Post Minute</Label>
            <Select value={String(settings.postMinute)} onValueChange={(v) => setSettings(s => s ? { ...s, postMinute: Number(v) } : s)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {MINUTES.map(m => <SelectItem key={m} value={String(m)}>:{String(m).padStart(2,"0")}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          {settings.postFrequency === "weekly" && (
            <div className="space-y-1.5">
              <Label className="text-xs">Day of Week</Label>
              <Select value={String(settings.postDayOfWeek ?? 0)} onValueChange={(v) => setSettings(s => s ? { ...s, postDayOfWeek: Number(v) } : s)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {DAYS_OF_WEEK.map((d, i) => <SelectItem key={i} value={String(i)}>{d}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}

          {settings.postFrequency === "monthly" && (
            <div className="space-y-1.5">
              <Label className="text-xs">Day of Month</Label>
              <Select value={String(settings.postDayOfMonth ?? 1)} onValueChange={(v) => setSettings(s => s ? { ...s, postDayOfMonth: Number(v) } : s)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 28 }, (_, i) => i + 1).map(d => <SelectItem key={d} value={String(d)}>{d}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {settings.lastPostedAt && (
          <p className="text-xs text-muted-foreground">
            Last posted: {new Date(settings.lastPostedAt).toLocaleString()}
          </p>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={save} disabled={saving} className="gap-2">
          {saving ? <Spinner className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          Save Schedule
        </Button>
      </CardFooter>
    </Card>
  );
}
