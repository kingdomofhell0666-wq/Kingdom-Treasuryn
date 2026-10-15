import { Link, useRoute } from "wouter";
import { Crown, ChevronLeft, LogOut, ExternalLink } from "lucide-react";
import { NAV_ITEMS } from "./nav-config";
import { useAuth } from "@/hooks/use-auth";
import { useGuild } from "@/context/guild-context";
import { cn } from "@/lib/utils";

interface SidebarProps {
  guildId: string;
}

export function Sidebar({ guildId }: SidebarProps) {
  const { user, logout, isLoggingOut } = useAuth();
  const { activeGuild } = useGuild();

  return (
    <aside className="flex flex-col h-full w-64 bg-sidebar border-r border-sidebar-border">
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-sidebar-border">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary text-primary-foreground shrink-0">
          <Crown className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-sidebar-foreground truncate">Kingdom Treasury</p>
          <p className="text-xs text-muted-foreground truncate">Admin Dashboard</p>
        </div>
      </div>

      {/* Server selector breadcrumb */}
      {activeGuild && (
        <div className="px-3 py-3 border-b border-sidebar-border">
          <Link href="/guilds">
            <a className="flex items-center gap-2 px-2 py-1.5 rounded-md text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors text-xs group">
              <ChevronLeft className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">Switch Server</span>
            </a>
          </Link>
          <div className="flex items-center gap-2 px-2 mt-2">
            {activeGuild.iconUrl ? (
              <img
                src={activeGuild.iconUrl}
                alt={activeGuild.name}
                className="w-7 h-7 rounded-full shrink-0"
              />
            ) : (
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <span className="text-xs font-bold text-primary">
                  {activeGuild.name.charAt(0)}
                </span>
              </div>
            )}
            <span className="text-sm font-medium text-sidebar-foreground truncate">
              {activeGuild.name}
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const href = `/guilds/${guildId}/${item.path}`;
          const Icon = item.icon;
          const [isActive] = useRoute(`/guilds/:guildId/${item.path}`);

          return (
            <Link key={item.path} href={href}>
              <a
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </a>
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      {user && (
        <div className="px-3 py-3 border-t border-sidebar-border">
          <div className="flex items-center gap-3 px-2 py-2">
            <img
              src={user.avatarUrl}
              alt={user.username}
              className="w-8 h-8 rounded-full shrink-0"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {user.username}
              </p>
            </div>
            <button
              onClick={logout}
              disabled={isLoggingOut}
              className="p-1.5 rounded-md text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
