import axios from "axios";
import { logger } from "./logger";

const DISCORD_API = "https://discord.com/api/v10";

export function getRedirectUri(): string {
  if (process.env["DISCORD_REDIRECT_URI"]) {
    return process.env["DISCORD_REDIRECT_URI"];
  }
  const dev = process.env["REPLIT_DEV_DOMAIN"];
  if (dev) {
    return `https://${dev}/api/auth/discord/callback`;
  }
  return "http://localhost:8080/api/auth/discord/callback";
}

export interface DiscordUser {
  id:            string;
  username:      string;
  discriminator: string;
  avatar:        string | null;
  global_name:   string | null;
}

export interface DiscordGuild {
  id:                       string;
  name:                     string;
  icon:                     string | null;
  permissions:              string;
  approximate_member_count?: number;
}

export interface TokenResponse {
  access_token:  string;
  refresh_token: string;
  expires_in:    number;
  token_type:    string;
  scope:         string;
}

export async function exchangeCode(code: string): Promise<TokenResponse> {
  const params = new URLSearchParams({
    client_id:     process.env["DISCORD_CLIENT_ID"] ?? "",
    client_secret: process.env["DISCORD_CLIENT_SECRET"] ?? "",
    grant_type:    "authorization_code",
    code,
    redirect_uri:  getRedirectUri(),
  });

  const res = await axios.post<TokenResponse>(
    `${DISCORD_API}/oauth2/token`,
    params.toString(),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
  );
  return res.data;
}

export async function fetchDiscordUser(accessToken: string): Promise<DiscordUser> {
  const res = await axios.get<DiscordUser>(`${DISCORD_API}/users/@me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.data;
}

export async function fetchDiscordGuilds(accessToken: string): Promise<DiscordGuild[]> {
  try {
    const res = await axios.get<DiscordGuild[]>(
      `${DISCORD_API}/users/@me/guilds?with_counts=true`,
      { headers: { Authorization: `Bearer ${accessToken}` } },
    );
    return res.data;
  } catch (err) {
    logger.warn({ err }, "Failed to fetch guilds with counts, retrying without");
    const res = await axios.get<DiscordGuild[]>(`${DISCORD_API}/users/@me/guilds`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return res.data;
  }
}

/** True if the user has Administrator (0x8) or Manage Guild (0x20). */
export function hasManagePermission(permissions: string): boolean {
  const p = BigInt(permissions);
  return (p & 0x8n) === 0x8n || (p & 0x20n) === 0x20n;
}

export function guildIconUrl(id: string, icon: string | null): string | null {
  if (!icon) return null;
  const ext = icon.startsWith("a_") ? "gif" : "png";
  return `https://cdn.discordapp.com/icons/${id}/${icon}.${ext}?size=128`;
}

export function avatarUrl(userId: string, avatar: string | null, discriminator: string): string {
  if (avatar) {
    const ext = avatar.startsWith("a_") ? "gif" : "png";
    return `https://cdn.discordapp.com/avatars/${userId}/${avatar}.${ext}?size=64`;
  }
  const idx = discriminator === "0"
    ? Number(BigInt(userId) >> 22n) % 6
    : parseInt(discriminator) % 5;
  return `https://cdn.discordapp.com/embed/avatars/${idx}.png`;
}
