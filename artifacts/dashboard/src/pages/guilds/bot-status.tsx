import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";
import { Wifi, WifiOff, Server, Clock, Hash, RefreshCw } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

type BotStatus = {
  online: boolean;
  guildCount: number;
  uptimeSeconds: number;
  lastHeartbeat: string;
};

function fmtUptime(s: number) {
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  return [d && `${d}d`, h && `${h}h`, m && `${m}m`, (!d && !h && !m) && `${s}s`].filter(Boolean).join(" ");
}

export default function BotStatusPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-3xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Bot Status</h1>
            <p className="text-muted-foreground">Live status of the Kingdom Treasury bot.</p>
          </div>
          <BotStatusView guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function BotStatusView({ guildId }: { guildId: string }) {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<BotStatus>(`/api/guilds/${guildId}/bot-status`);
      setStatus(data);
    } finally { setLoading(false); }
  }, [guildId]);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  if (!status) return <p className="text-center text-muted-foreground">Unable to fetch bot status.</p>;

  const metrics = [
    { label: "Guild Count", value: `${status.guildCount} servers`, icon: Hash },
    { label: "Uptime", value: fmtUptime(status.uptimeSeconds), icon: Clock },
    { label: "Last Heartbeat", value: new Date(status.lastHeartbeat).toLocaleTimeString(), icon: Server },
  ];

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border/60">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {status.online ? (
                <div className="w-12 h-12 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                  <Wifi className="w-6 h-6 text-green-500" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-full bg-destructive/10 border border-destructive/30 flex items-center justify-center">
                  <WifiOff className="w-6 h-6 text-destructive" />
                </div>
              )}
              <div>
                <p className="font-bold text-lg">Kingdom Treasury</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={status.online ? "default" : "destructive"} className={status.online ? "bg-green-600 text-white" : ""}>
                    {status.online ? "Online" : "Offline"}
                  </Badge>
                  {status.online && <span className="text-xs text-muted-foreground">Watching every transaction in the Kingdom</span>}
                </div>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetch} className="gap-2">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {metrics.map(m => (
          <Card key={m.label} className="bg-card border-border/60">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <m.icon className="w-4 h-4 text-muted-foreground" />
                <p className="text-xs text-muted-foreground">{m.label}</p>
              </div>
              <p className="text-lg font-bold text-foreground">{m.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-card border-border/60">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">Active Commands</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {["grind","tribute","transfer","wealth","ascend","invest","portfolio","withdraw","treasury","market","blackmarket","identity"].map(cmd => (
              <Badge key={cmd} variant="outline" className="font-mono text-xs">/{cmd}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
