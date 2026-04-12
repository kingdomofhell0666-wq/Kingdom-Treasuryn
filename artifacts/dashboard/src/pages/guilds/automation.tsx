import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { Link } from "wouter";
import { AppLayout, AuthGuard, PageHeader } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiGet } from "@/lib/api";
import {
  Zap, Calendar, Trophy, Crown, Clock, CheckCircle2, XCircle,
  ChevronRight, AlertCircle, RefreshCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type LeaderboardSettings = {
  enabled: boolean;
  postFrequency: string;
  postChannelId: string | null;
  postHour: number;
  postMinute: number;
  postDayOfWeek: number | null;
  timezone: string;
  lastPostedAt: string | null;
};

type AscensionSettings = {
  enabled: boolean;
  announceChannelId: string | null;
  mentionUser: boolean;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

function pad(n: number) { return String(n).padStart(2, "0"); }

function formatSchedule(s: LeaderboardSettings) {
  if (!s.enabled) return "Disabled";
  const freq = s.postFrequency === "weekly" ? "Weekly" : s.postFrequency === "monthly" ? "Monthly" : "Daily";
  const time = `${pad(s.postHour)}:${pad(s.postMinute)}`;
  if (s.postFrequency === "weekly" && s.postDayOfWeek != null) {
    return `${freq} on ${DAYS[s.postDayOfWeek]} at ${time} (${s.timezone})`;
  }
  return `${freq} at ${time} (${s.timezone})`;
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60)    return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)   return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AutomationPage() {
  const { guildId } = useParams() as { guildId: string };
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-4xl mx-auto space-y-8">
          <PageHeader
            title="Automation"
            description="Live automation status — leaderboard posts, ascension announcements, and scheduled economy events."
          />
          <AutomationView guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── AutomationView ───────────────────────────────────────────────────────────

function AutomationView({ guildId }: { guildId: string }) {
  const [leaderboard, setLeaderboard] = useState<LeaderboardSettings | null>(null);
  const [ascension,   setAscension]   = useState<AscensionSettings | null>(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [lb, asc] = await Promise.all([
        apiGet<LeaderboardSettings>(`/api/guilds/${guildId}/leaderboard`),
        apiGet<AscensionSettings>(`/api/guilds/${guildId}/ascension-announcements`),
      ]);
      setLeaderboard(lb);
      setAscension(asc);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load automation settings.");
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

  const automations = [
    {
      icon:    Trophy,
      title:   "Leaderboard Post",
      desc:    "Automatic weekly balance leaderboard posted to a channel.",
      enabled: leaderboard?.enabled ?? false,
      details: leaderboard ? formatSchedule(leaderboard) : "Not configured",
      sub:     leaderboard?.lastPostedAt
        ? `Last posted ${timeAgo(leaderboard.lastPostedAt)}`
        : "Never posted",
      channel: leaderboard?.postChannelId,
      link:    `/guilds/${guildId}/leaderboard`,
      linkLabel: "Configure",
    },
    {
      icon:    Crown,
      title:   "Ascension Announcements",
      desc:    "Post a public announcement when a member ascends to a new rank.",
      enabled: ascension?.enabled ?? false,
      details: ascension?.enabled ? "Active — posting announcements" : "Disabled",
      sub:     ascension?.mentionUser ? "Mentions user on announcement" : "No user mention",
      channel: ascension?.announceChannelId,
      link:    `/guilds/${guildId}/ascension`,
      linkLabel: "Configure",
    },
    {
      icon:    Calendar,
      title:   "Kingdom Ranks Reset",
      desc:    "Weekly stats (active seconds + DC earned) reset every Monday 00:00 UTC.",
      enabled: true,
      details: "Every Monday at 00:00 UTC (fixed schedule)",
      sub:     "Drives the weekly Kingdom Ranks leaderboard",
      channel: null,
      link:    `/guilds/${guildId}/kingdom-ranks`,
      linkLabel: "View Rankings",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Status row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatusCard
          icon={Zap}
          label="Automations Active"
          value={`${automations.filter((a) => a.enabled).length} / ${automations.length}`}
          ok={automations.some((a) => a.enabled)}
        />
        <StatusCard
          icon={Trophy}
          label="Leaderboard"
          value={leaderboard?.enabled ? "Enabled" : "Disabled"}
          ok={leaderboard?.enabled ?? false}
        />
        <StatusCard
          icon={Crown}
          label="Ascension Alerts"
          value={ascension?.enabled ? "Enabled" : "Disabled"}
          ok={ascension?.enabled ?? false}
        />
      </div>

      {/* Automation cards */}
      <div className="space-y-4">
        {automations.map((a) => (
          <AutomationCard key={a.title} item={a} guildId={guildId} />
        ))}
      </div>

      {/* Refresh */}
      <div className="flex justify-end">
        <Button size="sm" variant="ghost" onClick={load} className="gap-1.5 text-muted-foreground">
          <RefreshCcw className="w-3.5 h-3.5" />
          Refresh Status
        </Button>
      </div>
    </div>
  );
}

// ─── AutomationCard ───────────────────────────────────────────────────────────

function AutomationCard({ item, guildId }: {
  item: {
    icon: React.ElementType; title: string; desc: string;
    enabled: boolean; details: string; sub: string;
    channel: string | null; link: string; linkLabel: string;
  };
  guildId: string;
}) {
  const Icon = item.icon;
  return (
    <Card className="border-border/50">
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
            item.enabled ? "bg-primary/10" : "bg-muted/50",
          )}>
            <Icon className={cn("w-5 h-5", item.enabled ? "text-primary" : "text-muted-foreground")} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h3 className="font-semibold text-foreground">{item.title}</h3>
              {item.enabled
                ? <Badge className="text-xs bg-emerald-500/15 text-emerald-400 border-emerald-500/30">Active</Badge>
                : <Badge variant="outline" className="text-xs text-muted-foreground">Disabled</Badge>}
            </div>
            <p className="text-xs text-muted-foreground mb-2">{item.desc}</p>
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-foreground/70">
                <Clock className="w-3 h-3 text-muted-foreground" />
                {item.details}
              </div>
              <div className="text-xs text-muted-foreground">{item.sub}</div>
              {item.channel && (
                <div className="text-xs text-muted-foreground">
                  Channel ID: <code className="font-mono text-foreground/50">{item.channel}</code>
                </div>
              )}
            </div>
          </div>

          {/* Link */}
          <Link href={item.link}>
            <Button size="sm" variant="ghost" className="gap-1 text-muted-foreground hover:text-foreground shrink-0">
              {item.linkLabel}
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Status card ──────────────────────────────────────────────────────────────

function StatusCard({ icon: Icon, label, value, ok }: {
  icon: React.ElementType; label: string; value: string; ok: boolean;
}) {
  return (
    <Card className={cn("border-border/50", ok && "border-emerald-500/20 bg-emerald-500/5")}>
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon className={cn("w-4 h-4", ok ? "text-emerald-400" : "text-muted-foreground")} />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          {ok
            ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            : <XCircle      className="w-4 h-4 text-muted-foreground/40 shrink-0" />}
          <span className={cn("font-semibold", ok ? "text-emerald-400" : "text-foreground")}>{value}</span>
        </div>
      </CardContent>
    </Card>
  );
}
