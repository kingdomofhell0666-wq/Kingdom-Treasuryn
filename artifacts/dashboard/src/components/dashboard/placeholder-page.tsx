import type { LucideIcon } from "lucide-react";

interface PlaceholderPageProps {
  icon:        LucideIcon;
  title:       string;
  description: string;
  badge?:      string;
  badgeColor?: "default" | "red";
}

export function PlaceholderPage({
  icon: Icon, title, description, badge, badgeColor = "default",
}: PlaceholderPageProps) {
  return (
    <div className="max-w-2xl space-y-5">

      {/* Page header */}
      <div>
        <div className="flex items-center gap-2.5 mb-1">
          <h2 className="text-lg font-bold text-white/90">{title}</h2>
          {badge && (
            <span
              className={[
                "text-[10px] font-semibold px-2 py-0.5 rounded-full border",
                badgeColor === "red"
                  ? "bg-red-950/50 text-red-400 border-red-800/50"
                  : "bg-white/[0.05] text-white/40 border-white/10",
              ].join(" ")}
            >
              {badge}
            </span>
          )}
        </div>
        <p className="text-[13px] text-white/45 leading-relaxed">{description}</p>
      </div>

      {/* Placeholder card */}
      <div className="rounded-xl border border-white/[0.07] bg-[#111113] p-10 flex flex-col items-center text-center gap-4">
        <div className="w-11 h-11 rounded-xl bg-white/[0.05] border border-white/[0.07] flex items-center justify-center">
          <Icon className="text-white/25" size={20} />
        </div>
        <div className="space-y-1.5">
          <p className="text-[13px] font-semibold text-white/70">
            Coming in Phase 3
          </p>
          <p className="text-[12px] text-white/35 max-w-xs leading-relaxed">
            This section is scaffolded and ready. Configuration controls will be
            wired up in the next build phase.
          </p>
        </div>
      </div>
    </div>
  );
}
