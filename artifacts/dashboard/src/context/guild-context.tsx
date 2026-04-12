import { createContext, useContext, useState, ReactNode } from "react";
import { Guild } from "@/lib/api";

interface GuildContextValue {
  activeGuild: Guild | null;
  setActiveGuild: (guild: Guild | null) => void;
}

const GuildContext = createContext<GuildContextValue | null>(null);

export function GuildProvider({ children }: { children: ReactNode }) {
  const [activeGuild, setActiveGuild] = useState<Guild | null>(null);

  return (
    <GuildContext.Provider value={{ activeGuild, setActiveGuild }}>
      {children}
    </GuildContext.Provider>
  );
}

export function useGuild() {
  const ctx = useContext(GuildContext);
  if (!ctx) throw new Error("useGuild must be used within GuildProvider");
  return ctx;
}
