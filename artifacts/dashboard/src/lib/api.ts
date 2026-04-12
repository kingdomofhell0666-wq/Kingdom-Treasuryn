const API_BASE = "/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: "Unknown error" }));
    const err = new Error(body.error ?? `HTTP ${res.status}`);
    (err as any).status = res.status;
    throw err;
  }

  return res.json() as Promise<T>;
}

export interface DiscordUser {
  id: string;
  username: string;
  discriminator: string;
  avatar: string | null;
  avatarUrl: string;
}

export interface Guild {
  id: string;
  name: string;
  icon: string | null;
  iconUrl: string | null;
  memberCount?: number;
  botPresent: boolean;
  isAdmin: boolean;
}

export interface BotStatus {
  online: boolean;
  guildCount: number;
  uptimeSeconds: number;
  lastHeartbeat: string | null;
}

export interface GuildOverview {
  guild: Guild;
  botStatus: BotStatus;
}

export const api = {
  auth: {
    me: () => apiFetch<DiscordUser>("/auth/me"),
    logout: () =>
      apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" }),
    loginUrl: `${API_BASE}/auth/discord`,
  },
  guilds: {
    list: () => apiFetch<Guild[]>("/guilds"),
    botStatus: (guildId: string) =>
      apiFetch<BotStatus>(`/guilds/${guildId}/bot-status`),
  },
};
