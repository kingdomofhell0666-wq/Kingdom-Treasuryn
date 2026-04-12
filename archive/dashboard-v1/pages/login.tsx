import { useGetMe } from "@workspace/api-client-react";
import { useLocation, useSearch } from "wouter";
import { useEffect } from "react";
import { Shield, LogIn, AlertCircle } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";

const ERROR_MESSAGES: Record<string, string> = {
  discord_denied:  "Discord sign-in was cancelled. Try again when you're ready.",
  missing_code:    "The authentication code was missing. Please try signing in again.",
  state_mismatch:  "Security check failed. Please try signing in again.",
  auth_failed:     "Authentication failed. Discord may be having issues — try again shortly.",
};

export default function Login() {
  const { data: user, isLoading } = useGetMe({
    query: { retry: false, retryOnMount: false },
  });
  const [, setLocation] = useLocation();
  const search = useSearch();

  const params   = new URLSearchParams(search);
  const errorKey = params.get("error") ?? "";
  const errorMsg = ERROR_MESSAGES[errorKey] ?? (errorKey ? "Something went wrong. Please try again." : null);

  useEffect(() => {
    if (user && !isLoading) setLocation("/guilds");
  }, [user, isLoading, setLocation]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col overflow-hidden">
      {/* Ambient glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-primary/8 rounded-full blur-[140px] opacity-60" />
      </div>

      {/* Top bar */}
      <header className="relative z-10 flex items-center px-6 py-4 border-b border-border/30">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-primary/15 border border-primary/30 rounded-lg flex items-center justify-center">
            <Shield className="w-4 h-4 text-primary" />
          </div>
          <span className="font-bold text-foreground tracking-tight">Kingdom Treasury</span>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-8">

          {/* Logo mark */}
          <div className="flex justify-center">
            <div className="w-20 h-20 bg-card border border-border/50 rounded-2xl flex items-center justify-center shadow-2xl shadow-primary/10 ring-1 ring-primary/15">
              <Shield className="w-10 h-10 text-primary drop-shadow-[0_0_12px_rgba(220,38,38,0.6)]" />
            </div>
          </div>

          {/* Heading */}
          <div className="text-center space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight font-serif">
              Kingdom Treasury
            </h1>
            <p className="text-muted-foreground text-base">
              The private admin dashboard for your Discord economy bot.
            </p>
          </div>

          {/* Error message */}
          {errorMsg && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>{errorMsg}</p>
            </div>
          )}

          {/* CTA */}
          <Button
            size="lg"
            onClick={() => { window.location.href = "/api/auth/discord"; }}
            className="w-full h-13 text-base font-semibold bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30 hover:scale-[1.02] active:scale-[0.98]"
            data-testid="button-login"
          >
            <LogIn className="mr-2.5 w-5 h-5" />
            Sign in with Discord
          </Button>

          {/* Footer note */}
          <p className="text-center text-xs text-muted-foreground/50 leading-relaxed">
            Secure login via Discord OAuth. Only server admins may access the dashboard.
          </p>
        </div>
      </main>
    </div>
  );
}
