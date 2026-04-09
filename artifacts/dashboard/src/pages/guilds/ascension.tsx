import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPatch } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Flame, Save, AlertCircle } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

const ENDPOINT = (guildId: string) => `/api/guilds/${guildId}/ascension-announcements`;

const DEFAULT_SETTINGS = {
  enabled: false,
  channelId: null as string | null,
  messageTemplate: "{user} has ascended to {rank}.",
};

type AscensionSettings = typeof DEFAULT_SETTINGS;

const TEMPLATE_PRESETS = [
  { label: "Simple (default)",    value: "{user} has ascended to {rank}." },
  { label: "Kingdom of Hell",     value: "{user} has ascended to **{rank}** in the Kingdom of Hell. 🔥" },
  { label: "Risen",               value: "{user} has risen to the rank of **{rank}**. The Kingdom takes notice." },
  { label: "Advancement",         value: "{user} has advanced within the Kingdom and reached **{rank}**. Bow before them." },
  { label: "Dark coronation",     value: "🩸 The darkness welcomes {user} as **{rank}**. Another soul has found their place in hell." },
  { label: "Dramatic",           value: "⚔️ The throne room stirs. {user} has claimed the title of **{rank}**. None shall question it." },
];

type LoadState = "loading" | "ok" | "error";

export default function AscensionPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-3xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Ascension Announcements</h1>
            <p className="text-muted-foreground">
              When a member buys a rank with <strong>/ascend</strong>, the bot posts an announcement
              in your chosen channel — only that channel, nowhere else.
            </p>
          </div>
          <AscensionForm guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function AscensionForm({ guildId }: { guildId: string }) {
  const { toast } = useToast();
  const { data: guild } = useGetGuild(guildId);

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [settings, setSettings] = useState<AscensionSettings>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);

  const textChannels = (guild as { channels?: { id: string; name: string }[] })?.channels ?? [];
  const endpoint = ENDPOINT(guildId);

  const fetchSettings = useCallback(async () => {
    setLoadState("loading");
    setLoadError(null);
    try {
      const data = await apiGet<AscensionSettings>(endpoint);
      setSettings({
        enabled: data.enabled ?? DEFAULT_SETTINGS.enabled,
        channelId: data.channelId ?? DEFAULT_SETTINGS.channelId,
        messageTemplate: data.messageTemplate || DEFAULT_SETTINGS.messageTemplate,
      });
      setLoadState("ok");
    } catch (e: unknown) {
      const msg = (e as Error).message;
      console.error(`[AscensionPage] Failed to load settings from ${endpoint}:`, msg);
      setLoadError(msg);
      setSettings(DEFAULT_SETTINGS);
      setLoadState("error");
    }
  }, [endpoint]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const save = async () => {
    setSaving(true);
    try {
      const data = await apiPatch<AscensionSettings>(endpoint, settings);
      setSettings({
        enabled: data.enabled ?? DEFAULT_SETTINGS.enabled,
        channelId: data.channelId ?? DEFAULT_SETTINGS.channelId,
        messageTemplate: data.messageTemplate || DEFAULT_SETTINGS.messageTemplate,
      });
      setLoadState("ok");
      setLoadError(null);
      toast({ title: "Saved", description: "Ascension announcement settings updated." });
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
        <span className="text-sm">Loading announcement settings…</span>
      </div>
    );
  }

  const selectedChannel = textChannels.find(c => c.id === settings.channelId);
  const preview = settings.messageTemplate
    .replace("{user}", "@Darkblade")
    .replace("{rank}", "**Duke**");

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
            <Flame className="w-5 h-5 text-primary" />
            Announcement Settings
          </CardTitle>
          <CardDescription>
            Configure where and how the bot announces rank ascensions.
            The message will be posted in your chosen channel only.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-3">
            <Switch
              checked={settings.enabled}
              onCheckedChange={(v) => setSettings(s => ({ ...s, enabled: v }))}
              id="ann-enabled"
            />
            <Label htmlFor="ann-enabled" className="text-sm cursor-pointer">
              Enable ascension announcements
            </Label>
            {settings.enabled && settings.channelId && (
              <Badge className="text-xs bg-green-600/20 text-green-400 border border-green-600/30">
                Active
              </Badge>
            )}
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Announcement Channel</Label>
            <Select
              value={settings.channelId ?? ""}
              onValueChange={(v) => setSettings(s => ({ ...s, channelId: v || null }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a channel…" />
              </SelectTrigger>
              <SelectContent>
                {textChannels.length > 0
                  ? textChannels.map(c => <SelectItem key={c.id} value={c.id}>#{c.name}</SelectItem>)
                  : <SelectItem value="" disabled>No channels available (log in to Discord first)</SelectItem>
                }
              </SelectContent>
            </Select>
            {settings.channelId && !selectedChannel && (
              <p className="text-xs text-yellow-500">⚠ Channel not found — bot may not have access.</p>
            )}
            {selectedChannel && (
              <p className="text-xs text-muted-foreground">
                Announcements will appear in <strong>#{selectedChannel.name}</strong> only.
              </p>
            )}
          </div>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Message Preset</Label>
              <Select onValueChange={(v) => setSettings(s => ({ ...s, messageTemplate: v }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a preset, or write your own below…" />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_PRESETS.map(p => (
                    <SelectItem key={p.label} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Custom Message Template</Label>
              <Textarea
                rows={3}
                value={settings.messageTemplate}
                onChange={(e) => setSettings(s => ({ ...s, messageTemplate: e.target.value }))}
                placeholder="{user} has ascended to {rank}."
                className="resize-none text-sm font-mono"
              />
              <p className="text-xs text-muted-foreground">
                <code className="text-primary bg-primary/10 px-1 rounded">{"{user}"}</code> → Discord mention  ·  {" "}
                <code className="text-primary bg-primary/10 px-1 rounded">{"{rank}"}</code> → rank name
              </p>
            </div>
          </div>

          <div className="rounded-md bg-muted/30 border border-border/50 p-4 space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Preview</p>
            <div className="border-l-4 border-primary/60 bg-[#2b2d31] rounded-sm px-3 py-2">
              <p className="text-sm text-[#dcddde]"
                dangerouslySetInnerHTML={{ __html: preview.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") }}
              />
              <p className="text-[10px] text-[#72767d] mt-1">Kingdom Treasury  ·  Kingdom of Hell</p>
            </div>
            <p className="text-xs text-muted-foreground">
              This embed fires automatically when any member uses <strong>/ascend</strong> successfully.
            </p>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={save} disabled={saving} className="gap-2">
            {saving ? <Spinner className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            Save Settings
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
