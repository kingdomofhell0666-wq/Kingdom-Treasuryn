import { useLocation, useParams } from "wouter";
import {
  LayoutDashboard, Activity, Coins, CircleDollarSign, Landmark,
  Share2, Shield, Crown, TrendingUp, ShoppingBag, Package, IdCard,
  Trophy, Zap, Settings, AlertTriangle, LogOut, X, ChevronLeft,
} from "lucide-react";
import { NAV_SECTIONS, type NavItem } from "./nav-config";
import { useAuth } from "@/hooks/use-auth";
import { useGuild } from "@/context/guild-context";
import { API_BASE } from "@/lib/api";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  "layout-dashboard": LayoutDashboard,
  "activity":         Activity,
  "coins":            Coins,
  "circle-dollar-sign": CircleDollarSign,
  "landmark":         Landmark,
  "share-2":          Share2,
  "shield":           Shield,
  "crown":            Crown,
  "trending-up":      TrendingUp,
  "shopping-bag":     ShoppingBag,
  "package":          Package,
  "id-card":          IdCard,
  "trophy":           Trophy,
  "zap":              Zap,
  "settings":         Settings,
  "alert-triangle":   AlertTriangle,
};

function NavIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICON_MAP[name];
  if (!Icon) return <span className={className} />;
  return <Icon className={className} />;
}

function GuildIcon({ guild }: { guild: { name: string; iconUrl: string | null } | null }) {
  if (!guild) {
    return <div className="w-8 h-8 rounded-lg bg-muted animate-pulse" />;
  }
  if (guild.iconUrl) {
    return <img src={guild.iconUrl} alt={guild.name} className="w-8 h-8 rounded-lg object-cover flex-shrink-0" />;
  }
  const initials = guild.name.split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  return (
    <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-xs font-bold text-primary flex-shrink-0">
      {initials}
    </div>
  );
}

interface SidebarProps {
  open:    boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const { guildId } = useParams<{ guildId: string }>();
  const [location, navigate] = useLocation();
  const { guild } = useGuild();
  const { user } = useAuth();

  const base = `/guilds/${guildId}`;

  function isActive(item: NavItem) {
    const full = base + item.path;
    if (item.path === "") return location === base || location === base + "/";
    return location.startsWith(full);
  }

  function go(item: NavItem) {
    navigate(base + item.path);
    onClose();
  }

  async function logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    window.location.href = "/dashboard/";
  }

  const inner = (
    <div className="flex flex-col h-full">
      {/* Brand + server */}
      <div className="px-4 pt-5 pb-4 border-b border-white/10 space-y-3">
        {/* KT logo */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold select-none">
              K
            </div>
            <span className="text-sm font-semibold text-white/90 tracking-wide">Kingdom Treasury</span>
          </div>
          {/* Mobile close */}
          <button onClick={onClose} className="lg:hidden text-white/50 hover:text-white/90 transition-colors p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Selected server */}
        <button
          onClick={() => { navigate("/guilds"); onClose(); }}
          className="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-white/5 transition-colors group text-left"
        >
          <GuildIcon guild={guild} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white/90 truncate">
              {guild?.name ?? "Loading…"}
            </p>
            {guild?.memberCount != null && (
              <p className="text-xs text-white/40 truncate">
                {guild.memberCount.toLocaleString()} members
              </p>
            )}
          </div>
          <ChevronLeft className="w-3.5 h-3.5 text-white/30 group-hover:text-white/60 transition-colors rotate-180 flex-shrink-0" />
        </button>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-5 scrollbar-none">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/30 px-2 mb-1.5">
              {section.title}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item);
                return (
                  <button
                    key={item.path}
                    onClick={() => go(item)}
                    className={`
                      w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all
                      ${active
                        ? "bg-primary/15 text-primary font-medium"
                        : "text-white/55 hover:text-white/90 hover:bg-white/5"}
                    `}
                  >
                    <NavIcon
                      name={item.icon}
                      className={`w-4 h-4 flex-shrink-0 ${active ? "text-primary" : ""}`}
                    />
                    <span className="truncate">{item.label}</span>
                    {active && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 pb-4 pt-2 border-t border-white/10">
        <div className="flex items-center gap-2.5 px-2 py-2">
          {user?.avatarUrl ? (
            <img src={user.avatarUrl} alt={user.username} className="w-7 h-7 rounded-full flex-shrink-0" />
          ) : (
            <div className="w-7 h-7 rounded-full bg-white/10 flex-shrink-0" />
          )}
          <span className="text-sm text-white/60 truncate flex-1">{user?.username ?? "…"}</span>
          <button
            onClick={logout}
            title="Sign out"
            className="text-white/30 hover:text-white/80 transition-colors p-1 flex-shrink-0"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop fixed sidebar */}
      <aside className="hidden lg:flex flex-col w-56 flex-shrink-0 bg-[#0f0f10] border-r border-white/[0.07] min-h-screen sticky top-0">
        {inner}
      </aside>

      {/* Mobile overlay */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
          <aside className="relative z-50 w-64 bg-[#0f0f10] border-r border-white/[0.07] h-full flex flex-col">
            {inner}
          </aside>
        </div>
      )}
    </>
  );
}
