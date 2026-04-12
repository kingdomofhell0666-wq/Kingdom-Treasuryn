import { useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { API_BASE } from "@/lib/api";

const DISCORD_BLURPLE = "#5865F2";

function LoginButton({ href }: { href: string }) {
  return (
    <a
      href={href}
      className="inline-flex items-center gap-3 px-6 py-3 rounded-lg font-semibold text-white text-base transition-opacity hover:opacity-90 active:opacity-75"
      style={{ backgroundColor: DISCORD_BLURPLE }}
    >
      <DiscordIcon />
      Sign in with Discord
    </a>
  );
}

function DiscordIcon() {
  return (
    <svg width="22" height="16" viewBox="0 0 24 18" fill="currentColor">
      <path d="M20.317 1.492a19.82 19.82 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 1.492a.07.07 0 0 0-.032.027C.533 6.147-.32 10.671.099 15.138a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.029zM8.02 12.278c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.095 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate("/guilds");
    }
  }, [isAuthenticated, isLoading, navigate]);

  const loginUrl = `${API_BASE}/auth/discord`;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-muted-foreground border-t-foreground rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top bar */}
      <header className="border-b border-border px-6 py-4 flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold select-none">
          K
        </div>
        <span className="text-sm font-semibold text-foreground tracking-wide">
          Kingdom Treasury
        </span>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-sm flex flex-col items-center text-center gap-8">

          {/* Logo / icon */}
          <div className="w-16 h-16 rounded-2xl bg-card border border-border flex items-center justify-center text-3xl select-none shadow-lg">
            👑
          </div>

          {/* Headline */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              Kingdom Treasury
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Admin dashboard for managing your Kingdom of Hell Discord economy.
              Sign in to access your realm's control panel.
            </p>
          </div>

          {/* Login button */}
          <div className="flex flex-col items-center gap-3 w-full">
            <LoginButton href={loginUrl} />
            <p className="text-xs text-muted-foreground">
              Only servers where you have Administrator or Manage Server permission will be shown.
            </p>
          </div>

          {/* Features row */}
          <div className="grid grid-cols-3 gap-4 w-full pt-2">
            {[
              { icon: "⚙️", label: "Bot Config" },
              { icon: "📊", label: "Economy" },
              { icon: "🏆", label: "Kingdom Ranks" },
            ].map(({ icon, label }) => (
              <div
                key={label}
                className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-card border border-border"
              >
                <span className="text-lg">{icon}</span>
                <span className="text-xs text-muted-foreground font-medium">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-6 py-4 text-center">
        <p className="text-xs text-muted-foreground">
          Kingdom of Hell · Private Admin Dashboard
        </p>
      </footer>
    </div>
  );
}
