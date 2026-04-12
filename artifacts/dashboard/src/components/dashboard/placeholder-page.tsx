import { type LucideIcon } from "lucide-react";

interface PlaceholderPageProps {
  icon:        LucideIcon;
  title:       string;
  description: string;
  badge?:      string;
}

export function PlaceholderPage({ icon: Icon, title, description, badge }: PlaceholderPageProps) {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
          {badge && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
              {badge}
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>

      <div className="rounded-xl border border-border bg-card p-10 flex flex-col items-center text-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
          <Icon className="w-6 h-6 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="font-semibold text-foreground text-sm">Coming in the next block</p>
          <p className="text-xs text-muted-foreground max-w-xs">
            This section is scaffolded and ready. Configuration controls will be wired up in Block 3.
          </p>
        </div>
      </div>
    </div>
  );
}
