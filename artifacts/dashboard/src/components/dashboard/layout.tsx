import { useState, type ReactNode } from "react";
import { GuildProvider } from "@/context/guild-context";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

interface DashboardLayoutProps {
  children:  ReactNode;
  pageTitle: string;
}

export function DashboardLayout({ children, pageTitle }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <GuildProvider>
      <div className="flex min-h-screen bg-[#0a0a0b]">
        <Sidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Topbar
            pageTitle={pageTitle}
            onMenuClick={() => setSidebarOpen(true)}
          />
          <main className="flex-1 px-4 sm:px-6 py-6 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </GuildProvider>
  );
}
