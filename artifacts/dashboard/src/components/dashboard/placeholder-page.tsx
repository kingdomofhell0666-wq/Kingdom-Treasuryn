import { LucideIcon, Construction } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
}

export function PlaceholderPage({ title, description, icon: Icon }: PlaceholderPageProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
        {Icon ? (
          <Icon className="w-8 h-8 text-primary" />
        ) : (
          <Construction className="w-8 h-8 text-primary" />
        )}
      </div>
      <h2 className="text-xl font-semibold text-foreground mb-2">{title}</h2>
      <p className="text-sm text-muted-foreground max-w-xs">
        {description ?? "This section is coming soon. Check back later."}
      </p>
    </div>
  );
}
