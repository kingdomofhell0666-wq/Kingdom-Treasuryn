import { Menu } from "lucide-react";
import { useGuild } from "@/context/guild-context";

interface TopbarProps {
  pageTitle:    string;
  onMenuClick:  () => void;
}

function GuildBadge({ guild }: { guild: ReturnType<typeof useGuild>["guild"] }) {
  if (!guild) return null;
  return (
    <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border">
      {guild.iconUrl ? (
        <img src={guild.iconUrl} alt={guild.name} className="w-5 h-5 rounded-md object-cover" />
      ) : (
        <div className="w-5 h-5 rounded-md bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
          {guild.name[0]?.toUpperCase()}
        </div>
      )}
      <span className="text-xs font-medium text-foreground max-w-[140px] truncate">{guild.name}</span>
      {guild.botInstalled && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" title="Bot active" />
      )}
    </div>
  );
}

export function Topbar({ pageTitle, onMenuClick }: TopbarProps) {
  const { guild } = useGuild();

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur-sm flex items-center px-4 sm:px-6 gap-4 sticky top-0 z-30">
      {/* Mobile menu button */}
      <button
        onClick={onMenuClick}
        className="lg:hidden text-muted-foreground hover:text-foreground transition-colors p-1 -ml-1"
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      <h1 className="text-sm font-semibold text-foreground truncate flex-1">
        {pageTitle}
      </h1>

      {/* Guild badge */}
      <GuildBadge guild={guild} />
    </header>
  );
}
