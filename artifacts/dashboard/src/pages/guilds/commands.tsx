import { useState, useEffect, useCallback } from "react";
import { useParams } from "wouter";
import { AppLayout, AuthGuard } from "@/components/layout";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiGet, apiPut, apiDelete } from "@/lib/api";
import { useGetGuild } from "@workspace/api-client-react";
import { Swords, Save, Trash2, Plus, X } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ALL_COMMANDS = [
  "identity","grind","tribute","wealth","market",
  "ascend","invest","portfolio","withdraw",
  "transfer","treasury","blackmarket",
];

type Perms = {
  commandName: string;
  allowedRoles: string[];
  deniedRoles: string[];
  allowedChannels: string[];
  deniedChannels: string[];
};

type GuildRole = { id: string; name: string; color: number };

function hex(color: number) {
  return `#${color.toString(16).padStart(6, "0")}`;
}

export default function CommandsPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-8 max-w-5xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Command Permissions</h1>
            <p className="text-muted-foreground">Control which roles can use each command — and which are denied access.</p>
          </div>
          <CommandsManager guildId={guildId} />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function CommandsManager({ guildId }: { guildId: string }) {
  const { toast } = useToast();
  const { data: guild } = useGetGuild(guildId);
  const [perms, setPerms] = useState<Record<string, Perms>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const roles: GuildRole[] = (guild as { roles?: GuildRole[] })?.roles ?? [];

  const fetchPerms = useCallback(async () => {
    try {
      const data = await apiGet<Perms[]>(`/api/guilds/${guildId}/permissions`);
      const map: Record<string, Perms> = {};
      for (const p of data) map[p.commandName] = p;
      setPerms(map);
    } catch {
      /* empty — no permissions configured yet */
    } finally {
      setLoading(false);
    }
  }, [guildId]);

  useEffect(() => { fetchPerms(); }, [fetchPerms]);

  const getPerms = (cmd: string): Perms =>
    perms[cmd] ?? { commandName: cmd, allowedRoles: [], deniedRoles: [], allowedChannels: [], deniedChannels: [] };

  const toggleRole = (cmd: string, roleId: string, list: "allowedRoles" | "deniedRoles") => {
    const p = { ...getPerms(cmd) };
    const other = list === "allowedRoles" ? "deniedRoles" : "allowedRoles";
    p[list] = p[list].includes(roleId) ? p[list].filter(r => r !== roleId) : [...p[list], roleId];
    p[other] = p[other].filter(r => r !== roleId);
    setPerms(prev => ({ ...prev, [cmd]: p }));
  };

  const save = async (cmd: string) => {
    setSaving(cmd);
    try {
      await apiPut(`/api/guilds/${guildId}/permissions/${cmd}`, getPerms(cmd));
      toast({ title: "Saved", description: `Permissions for /${cmd} updated.` });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    } finally {
      setSaving(null);
    }
  };

  const clear = async (cmd: string) => {
    try {
      await apiDelete(`/api/guilds/${guildId}/permissions/${cmd}`);
      setPerms(prev => { const n = { ...prev }; delete n[cmd]; return n; });
      toast({ title: "Cleared", description: `All permission rules for /${cmd} removed.` });
    } catch (e: unknown) {
      toast({ title: "Error", description: (e as Error).message, variant: "destructive" });
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner className="w-8 h-8 text-primary" /></div>;

  return (
    <div className="space-y-4">
      {ALL_COMMANDS.map(cmd => {
        const p = getPerms(cmd);
        const hasAnyRule = p.allowedRoles.length > 0 || p.deniedRoles.length > 0;
        return (
          <Card key={cmd} className="bg-card border-border/60">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Swords className="w-4 h-4 text-primary" />
                    <span className="font-mono">/{cmd}</span>
                    {hasAnyRule && <Badge variant="secondary" className="text-xs">Custom rules</Badge>}
                  </CardTitle>
                </div>
                <div className="flex gap-2">
                  {hasAnyRule && (
                    <Button size="sm" variant="outline" onClick={() => clear(cmd)} className="text-destructive hover:text-destructive gap-1">
                      <Trash2 className="w-3 h-3" /> Clear
                    </Button>
                  )}
                  <Button size="sm" onClick={() => save(cmd)} disabled={saving === cmd} className="gap-1">
                    {saving === cmd ? <Spinner className="w-3 h-3" /> : <Save className="w-3 h-3" />}
                    Save
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <RoleSelector
                  label="✅ Allowed Roles"
                  description="Only these roles can use the command (empty = everyone)"
                  roles={roles}
                  selected={p.allowedRoles}
                  onToggle={(id) => toggleRole(cmd, id, "allowedRoles")}
                  variant="allow"
                />
                <RoleSelector
                  label="🚫 Denied Roles"
                  description="These roles are always blocked from the command"
                  roles={roles}
                  selected={p.deniedRoles}
                  onToggle={(id) => toggleRole(cmd, id, "deniedRoles")}
                  variant="deny"
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function RoleSelector({
  label, description, roles, selected, onToggle, variant,
}: {
  label: string;
  description: string;
  roles: GuildRole[];
  selected: string[];
  onToggle: (id: string) => void;
  variant: "allow" | "deny";
}) {
  const unselected = roles.filter(r => !selected.includes(r.id));
  const selectedRoles = roles.filter(r => selected.includes(r.id));

  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      {selectedRoles.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedRoles.map(r => (
            <Badge
              key={r.id}
              className="cursor-pointer gap-1 text-xs"
              style={{
                backgroundColor: r.color ? `${hex(r.color)}22` : undefined,
                borderColor: r.color ? hex(r.color) : undefined,
                color: r.color ? hex(r.color) : undefined,
              }}
              onClick={() => onToggle(r.id)}
            >
              {r.name} <X className="w-2.5 h-2.5" />
            </Badge>
          ))}
        </div>
      )}
      {unselected.length > 0 && (
        <Select onValueChange={(v) => onToggle(v)}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder={`Add ${variant === "allow" ? "allowed" : "denied"} role…`} />
          </SelectTrigger>
          <SelectContent>
            {unselected.map(r => (
              <SelectItem key={r.id} value={r.id} className="text-xs">
                <span className="flex items-center gap-2">
                  {r.color ? <span className="w-2 h-2 rounded-full inline-block" style={{ background: hex(r.color) }} /> : null}
                  {r.name}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
