import { useGetMe, useLogout } from "@workspace/api-client-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { Spinner } from "@/components/ui/spinner";
import {
  Sidebar, SidebarContent, SidebarHeader, SidebarGroup, SidebarGroupLabel,
  SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton,
  SidebarFooter, SidebarProvider, SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  LogOut, Home, Settings, Coins, Map, Activity, Shield, Swords,
  Crown, Trophy, Flame, RotateCcw, Wifi, BookOpen, Hash,
} from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useGetMe({ query: { retry: false } });
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (isError) {
      setLocation("/");
    }
  }, [isError, setLocation]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}

const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [
      { href: "", icon: Activity, label: "Dashboard" },
      { href: "/bot-status", icon: Wifi, label: "Bot Status" },
    ],
  },
  {
    label: "Economy",
    items: [
      { href: "/economy", icon: Coins, label: "Economy" },
      { href: "/currency", icon: BookOpen, label: "Currency" },
      { href: "/treasury", icon: Flame, label: "Treasury" },
    ],
  },
  {
    label: "Commands",
    items: [
      { href: "/channels", icon: Hash, label: "Routing" },
      { href: "/commands", icon: Swords, label: "Permissions" },
    ],
  },
  {
    label: "Ranks & Roles",
    items: [
      { href: "/ranks", icon: Crown, label: "Ranks & Roles" },
      { href: "/ascension", icon: Flame, label: "Ascension" },
    ],
  },
  {
    label: "Automation",
    items: [
      { href: "/leaderboard", icon: Trophy, label: "Leaderboard" },
    ],
  },
  {
    label: "Server",
    items: [
      { href: "/settings", icon: Settings, label: "Settings" },
      { href: "/reset", icon: RotateCcw, label: "Reset" },
    ],
  },
];

export function AppLayout({ children, guildId }: { children: React.ReactNode; guildId?: string }) {
  const { data: user } = useGetMe();
  const logout = useLogout();
  const [, setLocation] = useLocation();

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSuccess: () => setLocation("/"),
    });
  };

  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden bg-background w-full">
        {guildId && (
          <Sidebar variant="inset" className="border-r border-border/50">
            <SidebarHeader className="p-4">
              <Link href="/guilds" className="flex items-center gap-2 text-primary font-bold text-lg hover:text-primary/80 transition-colors">
                <Shield className="w-6 h-6" />
                Kingdom Treasury
              </Link>
            </SidebarHeader>
            <SidebarContent>
              {NAV_SECTIONS.map((section) => (
                <SidebarGroup key={section.label}>
                  <SidebarGroupLabel className="text-xs uppercase tracking-widest text-muted-foreground/60 px-3 py-1">
                    {section.label}
                  </SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {section.items.map((item) => (
                        <SidebarMenuItem key={item.href}>
                          <SidebarMenuButton asChild tooltip={item.label}>
                            <Link href={`/guilds/${guildId}${item.href}`}>
                              <item.icon className="w-4 h-4" />
                              <span>{item.label}</span>
                            </Link>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              ))}
            </SidebarContent>
            <SidebarFooter className="p-4 border-t border-border/50">
              <div className="flex items-center gap-3 w-full">
                <div className="w-8 h-8 rounded-full bg-muted overflow-hidden flex-shrink-0 border border-border">
                  {user?.avatarUrl ? (
                    <img src={user.avatarUrl} alt={user.username} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs font-bold text-muted-foreground uppercase">
                      {user?.username?.charAt(0) || "U"}
                    </div>
                  )}
                </div>
                <div className="flex-1 truncate">
                  <p className="text-sm font-medium truncate">{user?.username}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  className="text-muted-foreground hover:text-foreground"
                  data-testid="button-logout"
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </SidebarFooter>
          </Sidebar>
        )}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          {guildId && (
            <header className="h-14 border-b border-border/50 flex items-center px-4 md:hidden bg-background">
              <SidebarTrigger />
            </header>
          )}
          <main className="flex-1 overflow-y-auto bg-background/95">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
