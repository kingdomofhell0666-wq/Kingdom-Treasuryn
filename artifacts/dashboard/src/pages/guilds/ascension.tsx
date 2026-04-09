import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPatch } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Flame, Save } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

type AscensionSettings = {
  enabled: boolean;
  channelId: string | null;
  messageTemplate: string;
};

const TEMPLATE_PRESETS = [
  {
    label: "Ascension (default)",
    value: "{user} has ascended to **{rank}** in the Kingdom of Hell. 🔥",
  },
  {
    label: "Risen",
    value: "{user} has risen to the rank of **{rank}**. The Kingdom takes notice.",
  },
  {
    label: "Advancement",
    value: "{user} has advanced within the Kingdom and reached **{rank}**. Bow before them.",
  },
  {
    label: "Dark coronation",
    value: "🩸 The darkness welcomes {user} as **{rank}**. Another soul has found their place in hell.",
  },
  {
    label: "Dramatic",
    value: "⚔️ The throne room stirs. {user} has claimed the title of **{rank}**. None shall question it.",
  },
];

const DEFAULT_TEMPLATE = TEMPLATE_PRESETS[0].value;

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
              When a member buys a rank using <strong>/ascend</strong>, the bot posts an immersive announcement
              in your chosen channel. Configure where and how that message appears.
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
  const [settings, setSettings] = useState<AscensionSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const textChannels = (guild as { channels?: { id: string; name: string }[] })?.channels ?? [];

  const fetchSettings = useCallback(async () => {
    try {
      const data = await apiGet<AscensionSettings>(`/api/guilds/${guildId}/ascension-announcements`);
      setSettings({
        ...data,
        messageTemplate: data.messageTemplate || DEFAULT_TEMPLATE,
      });
    } finally { setLoading(false); }
  }, [guildId]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await apiPatch<AscensionSettings>(`/api/guilds/${guildId}/ascension-announcements`, settings);
      setSettings({ ...updated, messageTemplate: updated.messageTemplate || DEFAULT_TEMPLATE });
      toast({ title: "Saved", description: "Ascension announcement settings updated." });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally { setSaving(false); }
  };

  if (loading || !settings) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  const selectedChannel = textChannels.find(c => c.id === settings.channelId);
  const preview = (settings.messageTemplate || DEFAULT_TEMPLATE)
    .replace("{user}", "@Darkblade")
    .replace("{rank}", "**Duke**");

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Flame className="w-5 h-5 text-primary" />
            Announcement Settings
          </CardTitle>
          <CardDescription>
            When someone successfully buys a rank with <strong>/ascend</strong>, the bot automatically
            posts a message in the channel you choose — and only that channel.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-3">
            <Switch
              checked={settings.enabled}
              onCheckedChange={(v) => setSettings(s => s ? { ...s, enabled: v } : s)}
              id="ann-enabled"
            />
            <Label htmlFor="ann-enabled" className="text-sm cursor-pointer">
              Enable ascension announcements
            </Label>
            {settings.enabled && settings.channelId && (
              <Badge variant="secondary" className="text-xs bg-green-600/20 text-green-400 border-green-600/30">
                Active
              </Badge>
            )}
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Announcement Channel</Label>
            <Select
              value={settings.channelId ?? ""}
              onValueChange={(v) => setSettings(s => s ? { ...s, channelId: v || null } : s)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a channel…" />
              </SelectTrigger>
              <SelectContent>
                {textChannels.map(c => (
                  <SelectItem key={c.id} value={c.id}>#{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {settings.channelId && !selectedChannel && (
              <p className="text-xs text-yellow-500">Channel not found — bot may not have access.</p>
            )}
            {selectedChannel && (
              <p className="text-xs text-muted-foreground">
                Ascension messages will be posted in <strong>#{selectedChannel.name}</strong> only.
              </p>
            )}
          </div>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Message Preset</Label>
              <Select
                onValueChange={(v) => setSettings(s => s ? { ...s, messageTemplate: v } : s)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a preset (or write your own below)…" />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_PRESETS.map(p => (
                    <SelectItem key={p.label} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Message Template</Label>
              <Textarea
                rows={3}
                value={settings.messageTemplate}
                onChange={(e) => setSettings(s => s ? { ...s, messageTemplate: e.target.value } : s)}
                placeholder={DEFAULT_TEMPLATE}
                className="resize-none text-sm font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Variables: <code className="text-primary bg-primary/10 px-1 rounded">{"{user}"}</code> → Discord mention,{" "}
                <code className="text-primary bg-primary/10 px-1 rounded">{"{rank}"}</code> → rank name
              </p>
            </div>
          </div>

          <div className="rounded-md bg-muted/30 border border-border/50 p-4 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Message Preview</p>
            <div className="border-l-4 border-primary/60 bg-[#2b2d31] rounded-sm px-3 py-2">
              <p className="text-sm text-[#dcddde]">{preview}</p>
              <p className="text-[10px] text-[#72767d] mt-1">Kingdom Treasury  ·  Kingdom of Hell</p>
            </div>
            <p className="text-xs text-muted-foreground">
              This embed will appear in <strong>#{selectedChannel?.name || "your chosen channel"}</strong> whenever a member uses <strong>/ascend</strong> successfully.
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
