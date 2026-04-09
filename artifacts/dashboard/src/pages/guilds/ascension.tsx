import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPatch } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Flame, Save } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

type AscensionSettings = {
  enabled: boolean;
  channelId: string | null;
  messageTemplate: string;
};

export default function AscensionPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-3xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Ascension Announcements</h1>
            <p className="text-muted-foreground">Celebrate rank ascensions with automated channel announcements.</p>
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
      setSettings(data);
    } finally { setLoading(false); }
  }, [guildId]);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await apiPatch<AscensionSettings>(`/api/guilds/${guildId}/ascension-announcements`, settings);
      setSettings(updated);
      toast({ title: "Saved", description: "Ascension announcement settings updated." });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally { setSaving(false); }
  };

  if (loading || !settings) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  const preview = (settings.messageTemplate || "")
    .replace("{user}", "@Darkblade")
    .replace("{rank}", "Baron");

  return (
    <Card className="bg-card border-border/60">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Flame className="w-5 h-5 text-primary" />
          Ascension Announcements
        </CardTitle>
        <CardDescription>
          Post a public message when a member ascends their rank. Supports <code className="text-primary">{"{user}"}</code> and <code className="text-primary">{"{rank}"}</code>.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-3">
          <Switch
            checked={settings.enabled}
            onCheckedChange={(v) => setSettings(s => s ? { ...s, enabled: v } : s)}
            id="ann-enabled"
          />
          <Label htmlFor="ann-enabled" className="text-sm cursor-pointer">Enable ascension announcements</Label>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Announcement Channel</Label>
          <Select value={settings.channelId ?? ""} onValueChange={(v) => setSettings(s => s ? { ...s, channelId: v || null } : s)}>
            <SelectTrigger>
              <SelectValue placeholder="Select channel…" />
            </SelectTrigger>
            <SelectContent>
              {textChannels.map(c => (
                <SelectItem key={c.id} value={c.id}>#{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Message Template</Label>
          <Textarea
            rows={3}
            value={settings.messageTemplate}
            onChange={(e) => setSettings(s => s ? { ...s, messageTemplate: e.target.value } : s)}
            placeholder="{user} has ascended to {rank} in the Kingdom of Hell! 🔥"
            className="resize-none text-sm"
          />
          <p className="text-xs text-muted-foreground">
            Variables: <code className="text-primary">{"{user}"}</code> → mention, <code className="text-primary">{"{rank}"}</code> → rank name
          </p>
        </div>

        {settings.messageTemplate && (
          <div className="rounded-md bg-muted/40 border border-border/50 p-3">
            <p className="text-xs text-muted-foreground mb-1">Preview:</p>
            <p className="text-sm text-foreground">{preview}</p>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={save} disabled={saving} className="gap-2">
          {saving ? <Spinner className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          Save Settings
        </Button>
      </CardFooter>
    </Card>
  );
}
