import { Menu } from "lucide-react";
import { useGuild } from "@/context/guild-context";

interface TopbarProps {
  pageTitle:   string;
  onMenuClick: () => void;
}

function BotDot({ installed }: { installed: boolean }) {
  return (
    <span
      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${installed ? "bg-emerald-400" : "bg-white/20"}`}
      title={installed ? "Bot active" : "Bot not installed"}
    />
  );
}

export function Topbar({ pageTitle, onMenuClick }: TopbarProps) {
  const { guild } = useGuild();

  return (
    <header className="h-13 min-h-[52px] border-b border-white/[0.07] bg-[#0a0a0b]/95 backdrop-blur-sm flex items-center px-4 sm:px-5 gap-3 sticky top-0 z-30 flex-shrink-0">

      {/* Mobile menu button */}
      <button
        onClick={onMenuClick}
        className="lg:hidden text-white/40 hover:text-white/80 transition-colors p-1 -ml-1 flex-shrink-0"
        aria-label="Open navigation menu"
      >
        <Menu size={18} />
      </button>

      {/* Page title */}
      <h1 className="text-[13px] font-semibold text-white/80 truncate flex-1">
        {pageTitle}
      </h1>

      {/* Guild badge (desktop) */}
      {guild && (
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.07] flex-shrink-0">
          {guild.iconUrl ? (
            <img
              src={guild.iconUrl}
              alt={guild.name}
              className="w-4 h-4 rounded object-cover"
            />
          ) : (
            <div className="w-4 h-4 rounded bg-[#c0392b]/20 flex items-center justify-center text-[9px] font-bold text-[#c0392b]">
              {guild.name[0]?.toUpperCase()}
            </div>
          )}
          <span className="text-[12px] font-medium text-white/70 max-w-[160px] truncate">
            {guild.name}
          </span>
          <BotDot installed={guild.botInstalled} />
        </div>
      )}
    </header>
  );
}
