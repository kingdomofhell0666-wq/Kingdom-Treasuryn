import { useGetMe } from "@workspace/api-client-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Shield, Sparkles } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

export default function Login() {
  const { data: user, isLoading } = useGetMe({
    query: { retry: false, retryOnMount: false }
  });
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (user && !isLoading) {
      setLocation("/guilds");
    }
  }, [user, isLoading, setLocation]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="w-8 h-8 text-primary" />
      </div>
    );
  }

  const handleLogin = () => {
    window.location.href = "/api/auth/discord";
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/10 rounded-full blur-[120px] pointer-events-none opacity-50"></div>
      
      <div className="max-w-md w-full space-y-8 text-center relative z-10">
        <div className="flex justify-center mb-8">
          <div className="w-24 h-24 bg-card border border-border/50 rounded-2xl flex items-center justify-center shadow-2xl shadow-primary/20 ring-1 ring-primary/20">
            <Shield className="w-12 h-12 text-primary drop-shadow-[0_0_15px_rgba(220,38,38,0.8)]" />
          </div>
        </div>
        
        <div className="space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground font-serif">
            Kingdom Treasury
          </h1>
          <p className="text-xl text-muted-foreground font-medium">
            Command your infernal economy.
          </p>
        </div>

        <div className="pt-8">
          <Button 
            size="lg" 
            onClick={handleLogin}
            className="w-full sm:w-auto px-8 h-14 text-lg font-bold bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_0_20px_rgba(220,38,38,0.4)] transition-all hover:shadow-[0_0_30px_rgba(220,38,38,0.6)] hover:scale-105"
            data-testid="button-login"
          >
            <Sparkles className="mr-2 w-5 h-5" />
            Login with Discord
          </Button>
        </div>

        <div className="pt-16 text-sm text-muted-foreground/60 flex flex-col items-center gap-2">
          <p>Secure admin dashboard for server owners.</p>
        </div>
      </div>
    </div>
  );
}