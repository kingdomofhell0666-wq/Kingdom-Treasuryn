import { useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { API_BASE } from "@/lib/api";

const FEATURES = [
  { icon: "⚙️", label: "Bot Config" },
  { icon: "📊", label: "Economy" },
  { icon: "👑", label: "Kingdom Ranks" },
  { icon: "🏪", label: "Market" },
];

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate("/guilds");
    }
  }, [isLoading, isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-white/20 border-t-white/70 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center px-4 py-12">

      {/* Card */}
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-[#c0392b] flex items-center justify-center text-white text-2xl font-black mb-4 shadow-lg shadow-[#c0392b]/20">
            K
          </div>
          <h1 className="text-[22px] font-bold text-white/90 tracking-tight">
            Kingdom Treasury
          </h1>
          <p className="text-[13px] text-white/45 mt-1.5 text-center leading-relaxed max-w-[260px]">
            Private admin dashboard for the Kingdom of Hell economy system.
          </p>
        </div>

        {/* Login card */}
        <div className="rounded-2xl border border-white/[0.08] bg-[#111113] p-6 space-y-5">

          {/* Discord login button */}
          <a
            href={`${API_BASE}/auth/discord`}
            className="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-xl bg-[#5865F2] hover:bg-[#4752c4] active:bg-[#3c45a5] transition-colors text-white font-semibold text-[14px]"
          >
            {/* Discord logo */}
            <svg width="20" height="20" viewBox="0 0 127.14 96.36" fill="currentColor">
              <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
            </svg>
            Sign in with Discord
          </a>

          <p className="text-[11px] text-white/30 text-center leading-relaxed">
            Only servers where you have Administrator or Manage Server permission will appear.
          </p>
        </div>

        {/* Feature preview pills */}
        <div className="mt-6 flex items-center justify-center gap-2 flex-wrap">
          {FEATURES.map((f) => (
            <span
              key={f.label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.07] text-[11px] text-white/40"
            >
              <span>{f.icon}</span>
              <span>{f.label}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Footer */}
      <p className="mt-10 text-[11px] text-white/20">
        Kingdom of Hell · Private Admin Dashboard
      </p>
    </div>
  );
}
