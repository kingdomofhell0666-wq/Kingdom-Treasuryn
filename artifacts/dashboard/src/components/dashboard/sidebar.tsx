import { useLocation, useParams } from "wouter";
import {
  LayoutDashboard, Activity, Coins, CircleDollarSign, Landmark,
  Share2, Shield, Crown, TrendingUp, ShoppingBag, Package, IdCard,
  Trophy, Zap, Settings, AlertTriangle, LogOut, X, ChevronRight,
} from "lucide-react";
import { NAV_SECTIONS, type NavItem } from "./nav-config";
import { useAuth } from "@/hooks/use-auth";
import { useGuild } from "@/context/guild-context";
import { API_BASE } from "@/lib/api";

// ── Icon registry ──────────────────────────────────────────────────────────

type IconComponent = React.ComponentType<{ className?: string; size?: number }>;

const ICONS: Record<string, IconComponent> = {
  "layout-dashboard":   LayoutDashboard,
  "activity":           Activity,
  "coins":              Coins,
  "circle-dollar-sign": CircleDollarSign,
  "landmark":           Landmark,
  "share-2":            Share2,
  "shield":             Shield,
  "crown":              Crown,
  "trending-up":        TrendingUp,
  "shopping-bag":       ShoppingBag,
  "package":            Package,
  "id-card":            IdCard,
  "trophy":             Trophy,
  "zap":                Zap,
  "settings":           Settings,
  "alert-triangle":     AlertTriangle,
};

function NavIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICONS[name];
  return Icon ? <Icon className={className} size={15} /> : <span className={className} />;
}

// ── Guild avatar ───────────────────────────────────────────────────────────

function GuildAvatar({ guild }: { guild: { name: string; iconUrl: string | null } | null }) {
  if (!guild) return <div className="w-8 h-8 rounded-lg bg-white/10 animate-pulse flex-shrink-0" />;

  if (guild.iconUrl) {
    return (
      <img
        src={guild.iconUrl}
        alt={guild.name}
        className="w-8 h-8 rounded-lg object-cover flex-shrink-0"
      />
    );
  }

  const initials = guild.name
    .split(/\s+/).filter(Boolean).slice(0, 2)
    .map((w) => w[0]).join("").toUpperCase();

  return (
    <div className="w-8 h-8 rounded-lg bg-[#c0392b]/20 border border-[#c0392b]/30 flex items-center justify-center text-xs font-bold text-[#c0392b] flex-shrink-0">
      {initials}
    </div>
  );
}

// ── User avatar ────────────────────────────────────────────────────────────

function UserAvatar({ avatarUrl, username }: { avatarUrl?: string; username?: string }) {
  if (avatarUrl) {
    return <img src={avatarUrl} alt={username ?? ""} className="w-7 h-7 rounded-full flex-shrink-0 object-cover" />;
  }
  return (
    <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-xs font-medium text-white/60 flex-shrink-0">
      {username?.[0]?.toUpperCase() ?? "?"}
    </div>
  );
}

// ── Props ──────────────────────────────────────────────────────────────────

interface SidebarProps {
  open:    boolean;
  onClose: () => void;
}

// ── Inner nav ─────────────────────────────────────────────────────────────

function SidebarInner({ onClose }: { onClose: () => void }) {
  const { guildId } = useParams<{ guildId: string }>();
  const [location, navigate] = useLocation();
  const { guild } = useGuild();
  const { user } = useAuth();

  const base = `/guilds/${guildId}`;

  function isActive(item: NavItem): boolean {
    const full = base + item.path;
    if (item.path === "") return location === base || location === `${base}/`;
    return location.startsWith(full);
  }

  function go(path: string) {
    navigate(path);
    onClose();
  }

  async function logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    window.location.href = "/dashboard/";
  }

  return (
    <div className="flex flex-col h-full bg-[#0f0f10] overflow-hidden">

      {/* ── Brand header ── */}
      <div className="px-4 pt-5 pb-4 border-b border-white/[0.07] space-y-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-[#c0392b] flex items-center justify-center text-white text-xs font-black select-none flex-shrink-0">
              K
            </div>
            <span className="text-[13px] font-semibold text-white/85 tracking-wide">
              Kingdom Treasury
            </span>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-white/40 hover:text-white/80 transition-colors p-1 -mr-1"
          >
            <X size={15} />
          </button>
        </div>

        {/* Server switcher */}
        <button
          onClick={() => go("/guilds")}
          className="w-full flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-white/5 transition-colors group"
        >
          <GuildAvatar guild={guild} />
          <div className="flex-1 min-w-0 text-left">
            <p className="text-[13px] font-medium text-white/85 truncate leading-tight">
              {guild?.name ?? "Loading…"}
            </p>
            {guild?.memberCount != null && (
              <p className="text-[11px] text-white/35 mt-0.5">
                {guild.memberCount.toLocaleString()} members
              </p>
            )}
          </div>
          <ChevronRight size={13} className="text-white/25 group-hover:text-white/50 transition-colors flex-shrink-0" />
        </button>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-5 scrollbar-none">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-white/25 px-2 mb-1.5">
              {section.title}
            </p>
            <div className="space-y-px">
              {section.items.map((item) => {
                const active = isActive(item);
                return (
                  <button
                    key={item.path}
                    onClick={() => go(base + item.path)}
                    className={[
                      "w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-[7px] text-[13px] transition-all duration-100 group",
                      active
                        ? "bg-[#c0392b]/12 text-[#e74c3c] font-medium"
                        : "text-white/50 hover:text-white/85 hover:bg-white/[0.05]",
                    ].join(" ")}
                  >
                    <NavIcon
                      name={item.icon}
                      className={`flex-shrink-0 ${active ? "text-[#e74c3c]" : "text-white/35 group-hover:text-white/60 transition-colors"}`}
                    />
                    <span className="truncate">{item.label}</span>
                    {active && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#c0392b] flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* ── User footer ── */}
      <div className="flex-shrink-0 px-3 pb-4 pt-2 border-t border-white/[0.07]">
        <div className="flex items-center gap-2.5 px-2 py-1.5">
          <UserAvatar avatarUrl={user?.avatarUrl} username={user?.username} />
          <span className="text-[13px] text-white/55 truncate flex-1 leading-none">
            {user?.globalName ?? user?.username ?? "…"}
          </span>
          <button
            onClick={logout}
            title="Sign out"
            className="text-white/25 hover:text-white/70 transition-colors p-1 flex-shrink-0"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>

    </div>
  );
}

// ── Sidebar (desktop + mobile) ─────────────────────────────────────────────

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop: fixed left sidebar */}
      <aside className="hidden lg:block w-56 flex-shrink-0 h-screen sticky top-0 border-r border-white/[0.07]">
        <SidebarInner onClose={onClose} />
      </aside>

      {/* Mobile: overlay drawer */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <aside className="relative z-10 w-64 h-full border-r border-white/[0.07] flex-shrink-0">
            <SidebarInner onClose={onClose} />
          </aside>
        </div>
      )}
    </>
  );
}
