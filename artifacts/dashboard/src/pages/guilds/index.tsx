import { useGetGuilds } from "@workspace/api-client-react";
import { Link } from "wouter";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Shield, Users, AlertTriangle } from "lucide-react";
import { AppLayout, AuthGuard } from "@/components/layout";

export default function GuildsPage() {
  return (
    <AuthGuard>
      <AppLayout>
        <div className="p-8 max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2 font-serif text-foreground">Select a Realm</h1>
            <p className="text-muted-foreground">Choose a server to command your infernal economy.</p>
          </div>
          <GuildList />
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

function GuildList() {
  const { data: guilds, isLoading, isError } = useGetGuilds();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-[200px] bg-card rounded-xl border border-border animate-pulse"></div>
        ))}
      </div>
    );
  }

  if (isError || !guilds) {
    return (
      <div className="p-8 text-center bg-destructive/10 border border-destructive/20 rounded-xl text-destructive">
        <AlertTriangle className="w-8 h-8 mx-auto mb-4" />
        <p className="font-semibold">Failed to load guilds. Please try again later.</p>
      </div>
    );
  }

  const manageableGuilds = guilds.filter(g => g.botPresent && g.isAdmin);

  if (manageableGuilds.length === 0) {
    return (
      <div className="p-12 text-center bg-card border border-border rounded-xl shadow-lg">
        <Shield className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
        <h3 className="text-xl font-bold mb-2">No manageable servers found</h3>
        <p className="text-muted-foreground">The bot must be present and you must be an admin.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {manageableGuilds.map(guild => (
        <Link key={guild.id} href={`/guilds/${guild.id}`} className="block group">
          <Card className="h-full hover:border-primary/50 transition-all hover:shadow-[0_0_15px_rgba(220,38,38,0.15)] hover:-translate-y-1 bg-card/50 backdrop-blur">
            <CardHeader className="flex flex-row items-start gap-4 pb-4">
              <div className="w-16 h-16 rounded-xl bg-muted border border-border overflow-hidden flex-shrink-0 flex items-center justify-center">
                {guild.iconUrl ? (
                  <img src={guild.iconUrl} alt={guild.name} className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl font-bold text-muted-foreground">
                    {guild.name.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <CardTitle className="text-lg truncate group-hover:text-primary transition-colors">
                  {guild.name}
                </CardTitle>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant={guild.botPresent ? "default" : "destructive"} className={guild.botPresent ? "bg-primary/20 text-primary hover:bg-primary/30" : ""}>
                    {guild.botPresent ? "Active" : "Offline"}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-muted-foreground">
                <Users className="w-4 h-4 mr-2" />
                <span>{guild.memberCount?.toLocaleString() || 0} members</span>
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}