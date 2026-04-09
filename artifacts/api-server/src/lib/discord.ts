/**
 * Discord OAuth2 + API helpers for the dashboard backend.
 */
import axios from "axios";

const BASE = "https://discord.com/api/v10";

export const DISCORD_CLIENT_ID     = process.env["DISCORD_CLIENT_ID"]!;
export const DISCORD_CLIENT_SECRET = process.env["DISCORD_CLIENT_SECRET"]!;

function getRedirectUri(): string {
  const domains = process.env["REPLIT_DOMAINS"] ?? process.env["REPLIT_DEV_DOMAIN"] ?? "localhost:80";
  const primary = domains.split(",")[0]?.trim() ?? "localhost:80";
  const host = primary.includes("localhost") ? `http://${primary}` : `https://${primary}`;
  return `${host}/api/auth/discord/callback`;
}

export function buildOAuthUrl(state: string): string {
  const params = new URLSearchParams({
    client_id:     DISCORD_CLIENT_ID,
    redirect_uri:  getRedirectUri(),
    response_type: "code",
    scope:         "identify guilds",
    state,
  });
  return `https://discord.com/api/oauth2/authorize?${params.toString()}`;
}

export interface DiscordTokens {
  access_token:  string;
  refresh_token: string;
  expires_in:    number;
  token_type:    string;
  scope:         string;
}

export async function exchangeCode(code: string): Promise<DiscordTokens> {
  const res = await axios.post<DiscordTokens>(
    `${BASE}/oauth2/token`,
    new URLSearchParams({
      client_id:     DISCORD_CLIENT_ID,
      client_secret: DISCORD_CLIENT_SECRET,
      grant_type:    "authorization_code",
      code,
      redirect_uri:  getRedirectUri(),
    }),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
  );
  return res.data;
}

export interface DiscordUser {
  id:            string;
  username:      string;
  discriminator: string;
  avatar:        string | null;
  global_name?:  string | null;
}

export async function fetchMe(accessToken: string): Promise<DiscordUser> {
  const res = await axios.get<DiscordUser>(`${BASE}/users/@me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.data;
}

export interface DiscordGuild {
  id:          string;
  name:        string;
  icon:        string | null;
  owner:       boolean;
  permissions: string;
  features:    string[];
  approximate_member_count?: number;
}

export async function fetchUserGuilds(accessToken: string): Promise<DiscordGuild[]> {
  const res = await axios.get<DiscordGuild[]>(`${BASE}/users/@me/guilds?with_counts=true`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.data;
}

export async function fetchBotGuild(guildId: string): Promise<any | null> {
  const botToken = process.env["DISCORD_BOT_TOKEN"];
  if (!botToken) return null;
  try {
    const res = await axios.get(`${BASE}/guilds/${guildId}?with_counts=true`, {
      headers: { Authorization: `Bot ${botToken}` },
    });
    return res.data;
  } catch {
    return null;
  }
}

export async function fetchBotGuildIds(): Promise<Set<string>> {
  const botToken = process.env["DISCORD_BOT_TOKEN"];
  if (!botToken) return new Set();
  try {
    const res = await axios.get<DiscordGuild[]>(`${BASE}/users/@me/guilds`, {
      headers: { Authorization: `Bot ${botToken}` },
    });
    return new Set(res.data.map((g) => g.id));
  } catch {
    return new Set();
  }
}

export function avatarUrl(user: DiscordUser): string {
  if (!user.avatar) return `https://cdn.discordapp.com/embed/avatars/${Number(user.discriminator) % 5}.png`;
  return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=128`;
}

export function guildIconUrl(guild: { id: string; icon: string | null }): string | null {
  if (!guild.icon) return null;
  return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=128`;
}

/** Check if a user has ADMINISTRATOR permission (bit 3) or is owner */
export function hasAdminPermission(permissions: string, isOwner: boolean): boolean {
  if (isOwner) return true;
  const perms = BigInt(permissions);
  const ADMINISTRATOR = BigInt(0x8);
  return (perms & ADMINISTRATOR) === ADMINISTRATOR;
}
