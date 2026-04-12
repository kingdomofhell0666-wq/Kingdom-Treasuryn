import { useGetMe, useLogout, useGetGuild, getGetGuildQueryKey } from "@workspace/api-client-react";
import { useLocation, Link } from "wouter";
import { useEffect } from "react";
import { Spinner } from "@/components/ui/spinner";
import {
  Sidebar, SidebarContent, SidebarHeader, SidebarGroup, SidebarGroupLabel,
  SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton,
  SidebarFooter, SidebarProvider, SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  LogOut, Home, Settings, Coins, Map, Activity, Shield, Swords,
  Crown, Trophy, Flame, RotateCcw, Wifi, BookOpen, Hash, ChevronDown,
  Users, Package, ShoppingBag, IdCard, Zap, ChevronLeft, BarChart3,
  ShieldCheck, ArrowUpCircle, Vault, Route, Server,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

// ─── Auth Guard ─────────────────────────────────────────────────────────────

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useGetMe({ query: { retry: false } });
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (isError) setLocation("/");
  }, [isError, setLocation]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  if (!user) return null;
  return <>{children}</>;
}

// ─── Navigation config ───────────────────────────────────────────────────────

export const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [
      { href: "",             icon: Home,         label: "Dashboard" },
      { href: "/bot-status",  icon: Wifi,         label: "Bot Status" },
    ],
  },
  {
    label: "Economy",
    items: [
      { href: "/economy",    icon: Coins,        label: "Economy" },
      { href: "/currency",   icon: BookOpen,     label: "Currency" },
      { href: "/treasury",   icon: Vault,        label: "Treasury" },
    ],
  },
  {
    label: "Commands",
    items: [
      { href: "/channels",   icon: Route,        label: "Routing" },
      { href: "/commands",   icon: ShieldCheck,  label: "Permissions" },
    ],
  },
  {
    label: "Ranks & Roles",
    items: [
      { href: "/ranks",      icon: Crown,        label: "Ranks & Roles" },
      { href: "/ascension",  icon: ArrowUpCircle, label: "Ascension" },
    ],
  },
  {
    label: "Player Systems",
    items: [
      { href: "/market",     icon: ShoppingBag,  label: "Market" },
      { href: "/inventory",  icon: Package,      label: "Inventory" },
      { href: "/identity",   icon: IdCard,       label: "Identity" },
    ],
  },
  {
    label: "Automation",
    items: [
      { href: "/kingdom-ranks", icon: Trophy,    label: "Kingdom Ranks" },
      { href: "/leaderboard",   icon: BarChart3, label: "Leaderboard" },
      { href: "/automation",    icon: Zap,       label: "Automation" },
    ],
  },
  {
    label: "Server",
    items: [
      { href: "/settings",   icon: Settings,     label: "Settings" },
      { href: "/reset",      icon: RotateCcw,    label: "Reset" },
    ],
  },
];

// ─── App Layout ──────────────────────────────────────────────────────────────

export function AppLayout({
  children,
  guildId,
}: {
  children: React.ReactNode;
  guildId?: string;
}) {
  const { data: user } = useGetMe();
  const { data: guild } = useGetGuild(guildId ?? "", {
    query: { enabled: !!guildId, queryKey: getGetGuildQueryKey(guildId ?? "") },
  });
  const logout = useLogout();
  const [location, setLocation] = useLocation();

  const handleLogout = () => {
    logout.mutate(undefined, { onSuccess: () => setLocation("/") });
  };

  // Determine active page label for topbar breadcrumb
  const activePage = (() => {
    if (!guildId) return null;
    for (const section of NAV_SECTIONS) {
      for (const item of section.items) {
        const fullHref = `/guilds/${guildId}${item.href}`;
        if (item.href === "") {
          if (location === `/guilds/${guildId}` || location === `/guilds/${guildId}/`) return item.label;
        } else if (location.startsWith(fullHref)) {
          return item.label;
        }
      }
    }
    return "Dashboard";
  })();

  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden bg-background w-full">
        {/* ── Sidebar ── */}
        {guildId && (
          <Sidebar variant="inset" className="border-r border-border/40 bg-sidebar">
            {/* Brand header */}
            <SidebarHeader className="px-4 pt-4 pb-3 border-b border-border/30">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-7 h-7 bg-primary/15 border border-primary/30 rounded-md flex items-center justify-center flex-shrink-0">
                  <Shield className="w-3.5 h-3.5 text-primary" />
                </div>
                <span className="font-bold text-sm tracking-tight text-foreground">Kingdom Treasury</span>
              </div>

              {/* Server switcher */}
              <Link
                href="/guilds"
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg bg-muted/40 hover:bg-muted/70 transition-colors group"
              >
                <div className="w-8 h-8 rounded-md bg-muted border border-border/60 overflow-hidden flex-shrink-0 flex items-center justify-center font-bold text-xs text-muted-foreground">
                  {guild?.iconUrl ? (
                    <img src={guild.iconUrl} alt={guild.name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="uppercase">{guild?.name?.charAt(0) || "K"}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate leading-tight">
                    {guild?.name || "Loading…"}
                  </p>
                  <p className="text-[10px] text-muted-foreground/60 leading-tight mt-0.5">Switch server</p>
                </div>
                <ChevronLeft className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors flex-shrink-0" />
              </Link>
            </SidebarHeader>

            {/* Navigation */}
            <SidebarContent className="px-2 py-2 overflow-y-auto scrollbar-thin">
              {NAV_SECTIONS.map((section) => (
                <SidebarGroup key={section.label} className="mb-0.5">
                  <SidebarGroupLabel className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50 px-2 py-1.5 mb-0.5">
                    {section.label}
                  </SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {section.items.map((item) => {
                        const fullHref = `/guilds/${guildId}${item.href}`;
                        const isActive =
                          item.href === ""
                            ? location === `/guilds/${guildId}` || location === `/guilds/${guildId}/`
                            : location.startsWith(fullHref);

                        return (
                          <SidebarMenuItem key={item.href}>
                            <SidebarMenuButton
                              asChild
                              tooltip={item.label}
                              className={cn(
                                "rounded-md transition-all duration-150 text-[13px] h-8",
                                isActive
                                  ? "bg-primary/15 text-primary font-semibold"
                                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                              )}
                            >
                              <Link href={fullHref}>
                                <item.icon
                                  className={cn(
                                    "w-4 h-4 flex-shrink-0",
                                    isActive ? "text-primary" : "text-muted-foreground"
                                  )}
                                />
                                <span>{item.label}</span>
                                {isActive && (
                                  <span className="ml-auto w-1 h-4 rounded-full bg-primary opacity-80" />
                                )}
                              </Link>
                            </SidebarMenuButton>
                          </SidebarMenuItem>
                        );
                      })}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              ))}
            </SidebarContent>

            {/* User footer */}
            <SidebarFooter className="px-3 py-3 border-t border-border/30">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-muted border border-border overflow-hidden flex-shrink-0">
                  {user?.avatarUrl ? (
                    <img src={user.avatarUrl} alt={user.username} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[10px] font-bold text-muted-foreground uppercase">
                      {user?.username?.charAt(0) || "U"}
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate">{user?.username}</p>
                  <p className="text-[10px] text-muted-foreground/60 truncate">Administrator</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  className="h-7 w-7 text-muted-foreground hover:text-foreground flex-shrink-0"
                  data-testid="button-logout"
                  title="Sign out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </Button>
              </div>
            </SidebarFooter>
          </Sidebar>
        )}

        {/* ── Main area ── */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Topbar — always visible */}
          {guildId && (
            <header className="h-13 border-b border-border/40 flex items-center gap-3 px-4 bg-background flex-shrink-0">
              {/* Mobile sidebar trigger */}
              <SidebarTrigger className="text-muted-foreground hover:text-foreground flex-shrink-0" />

              {/* Breadcrumb */}
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className="text-xs text-muted-foreground/50 hidden sm:block">
                  {guild?.name && (
                    <span className="truncate max-w-[120px] inline-block align-bottom">{guild.name}</span>
                  )}
                </span>
                {guild?.name && (
                  <span className="text-xs text-muted-foreground/30 hidden sm:block">/</span>
                )}
                <span className="text-sm font-semibold text-foreground truncate">{activePage}</span>
              </div>

              {/* Right: member count */}
              {guild?.memberCount != null && (
                <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground/60 flex-shrink-0">
                  <Users className="w-3.5 h-3.5" />
                  <span>{guild.memberCount.toLocaleString()} members</span>
                </div>
              )}
            </header>
          )}

          {/* Content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}

// ─── Page header helper ───────────────────────────────────────────────────────

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight font-serif text-foreground">{title}</h1>
        {description && (
          <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

// ─── Placeholder page helper ──────────────────────────────────────────────────

export function PlaceholderPage({
  guildId,
  icon: Icon,
  title,
  description,
  badge,
}: {
  guildId: string;
  icon: React.ElementType;
  title: string;
  description: string;
  badge?: string;
}) {
  return (
    <AuthGuard>
      <AppLayout guildId={guildId}>
        <div className="p-6 sm:p-8 max-w-3xl mx-auto">
          <PageHeader title={title} description={description} />
          <div className="flex flex-col items-center justify-center gap-5 py-16 text-center rounded-2xl border border-border/40 border-dashed bg-card/30">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Icon className="w-7 h-7 text-primary/70" />
            </div>
            <div className="space-y-2 max-w-sm">
              <p className="font-semibold text-foreground">
                {badge ?? "Coming in a future block"}
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed">
                This section is scaffolded and ready for configuration logic. Full implementation arrives in Block 3+.
              </p>
            </div>
          </div>
        </div>
      </AppLayout>
    </AuthGuard>
  );
}

// ─── Guilds selection layout ──────────────────────────────────────────────────

export function GuildsLayout({ children }: { children: React.ReactNode }) {
  const { data: user } = useGetMe();
  const logout = useLogout();
  const [, setLocation] = useLocation();

  const handleLogout = () => {
    logout.mutate(undefined, { onSuccess: () => setLocation("/") });
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-30 border-b border-border/40 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link href="/guilds" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 bg-primary/15 border border-primary/30 rounded-md flex items-center justify-center group-hover:bg-primary/20 transition-colors">
              <Shield className="w-3.5 h-3.5 text-primary" />
            </div>
            <span className="font-bold text-sm tracking-tight text-foreground">Kingdom Treasury</span>
          </Link>

          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted/50 transition-colors text-sm">
                  <div className="w-7 h-7 rounded-full bg-muted border border-border overflow-hidden flex-shrink-0">
                    {user.avatarUrl ? (
                      <img src={user.avatarUrl} alt={user.username} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[10px] font-bold text-muted-foreground uppercase">
                        {user.username?.charAt(0) || "U"}
                      </div>
                    )}
                  </div>
                  <span className="hidden sm:block text-foreground font-medium max-w-[140px] truncate">{user.username}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="text-muted-foreground focus:text-foreground cursor-pointer"
                  data-testid="button-logout"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </header>

      <main className="flex-1">{children}</main>
    </div>
  );
}
