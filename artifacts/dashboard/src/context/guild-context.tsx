import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useParams } from "wouter";
import { API_BASE } from "@/lib/api";

export interface Guild {
  id:           string;
  name:         string;
  icon:         string | null;
  iconUrl:      string | null;
  memberCount:  number | null;
  botInstalled: boolean;
}

interface GuildContextValue {
  guild:     Guild | null;
  isLoading: boolean;
  error:     string | null;
}

const GuildContext = createContext<GuildContextValue>({
  guild: null, isLoading: true, error: null,
});

export function GuildProvider({ children }: { children: ReactNode }) {
  const { guildId } = useParams<{ guildId: string }>();
  const [guild, setGuild]       = useState<Guild | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    if (!guildId) return;
    setLoading(true);
    fetch(`${API_BASE}/guilds`, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json() as Promise<{ guilds: Guild[] }>;
      })
      .then(({ guilds }) => {
        const found = guilds.find((g) => g.id === guildId) ?? null;
        setGuild(found);
        setLoading(false);
      })
      .catch(() => {
        setError("Could not load server data.");
        setLoading(false);
      });
  }, [guildId]);

  return (
    <GuildContext.Provider value={{ guild, isLoading, error }}>
      {children}
    </GuildContext.Provider>
  );
}

export function useGuild() {
  return useContext(GuildContext);
}
