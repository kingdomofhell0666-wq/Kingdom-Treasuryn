import { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

interface DashboardLayoutProps {
  guildId: string;
  children: ReactNode;
}

export function DashboardLayout({ guildId, children }: DashboardLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar guildId={guildId} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
