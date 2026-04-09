/**
 * Discord OAuth2 + API helpers for the dashboard backend.
 *
 * ── RATE-LIMIT PROTECTION ──────────────────────────────────────────────────
 * Discord aggressively rate-limits /users/@me/guilds (OAuth2 token endpoint).
 * When the dashboard opens a guild page it fires 5–10 concurrent requests;
 * each one used to call Discord independently → 429 storm.
 *
 * We fix this with two layers:
 *  1. In-flight deduplication: all concurrent callers sharing the same token
 *     await the same single Promise instead of each starting their own request.
 *  2. TTL cache (5 min): after the first successful response, subsequent calls
 *     within 5 minutes return the cached result without hitting Discord at all.
 *  3. Stale-on-429 fallback: if Discord still returns 429 we serve the last
 *     known-good cached value (or stale data) rather than blowing up.
 * ────────────────────────────────────────────────────────────────────────────
 */
import axios from "axios";

const BASE = "https://discord.com/api/v10";

export const DISCORD_CLIENT_ID     = process.env["DISCORD_CLIENT_ID"]!;
export const DISCORD_CLIENT_SECRET = process.env["DISCORD_CLIENT_SECRET"]!;

// ── OAuth redirect URI ────────────────────────────────────────────────────────

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

// ── Token exchange ────────────────────────────────────────────────────────────

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

// ── /users/@me ────────────────────────────────────────────────────────────────

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

// ── /users/@me/guilds — cached + deduplicated ─────────────────────────────────

export interface DiscordGuild {
  id:          string;
  name:        string;
  icon:        string | null;
  owner:       boolean;
  permissions: string;
  features:    string[];
  approximate_member_count?: number;
}

const USER_GUILDS_TTL_MS = 5 * 60 * 1000; // 5 minutes

interface CacheEntry<T> {
  data:      T;
  expiresAt: number;
}

/** TTL cache: access_token → { data, expiresAt } */
const userGuildsCache = new Map<string, CacheEntry<DiscordGuild[]>>();
/** In-flight dedup: access_token → pending Promise */
const userGuildsInFlight = new Map<string, Promise<DiscordGuild[]>>();

export async function fetchUserGuilds(accessToken: string): Promise<DiscordGuild[]> {
  // 1. Fresh cache hit → return immediately
  const cached = userGuildsCache.get(accessToken);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.data;
  }

  // 2. Already fetching for this token → share the same promise
  const inFlight = userGuildsInFlight.get(accessToken);
  if (inFlight) return inFlight;

  // 3. Start a new request
  const request = axios
    .get<DiscordGuild[]>(`${BASE}/users/@me/guilds?with_counts=true`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    .then((res) => {
      userGuildsCache.set(accessToken, {
        data:      res.data,
        expiresAt: Date.now() + USER_GUILDS_TTL_MS,
      });
      return res.data;
    })
    .catch((err) => {
      // 429 or other Discord error → try stale cache before giving up
      const stale = userGuildsCache.get(accessToken);
      if (stale) {
        console.warn(
          `[discord] fetchUserGuilds: Discord returned ${err?.response?.status ?? err.message}. Serving stale cache.`
        );
        return stale.data;
      }
      throw err;
    })
    .finally(() => {
      userGuildsInFlight.delete(accessToken);
    });

  userGuildsInFlight.set(accessToken, request);
  return request;
}

/** Evict a specific token from cache (call on logout/token refresh) */
export function evictUserGuildsCache(accessToken: string): void {
  userGuildsCache.delete(accessToken);
  userGuildsInFlight.delete(accessToken);
}

// ── Bot guild helpers — cached ────────────────────────────────────────────────

const BOT_GUILD_TTL_MS    = 2 * 60 * 1000;  // 2 minutes
const BOT_GUILD_IDS_TTL_MS = 2 * 60 * 1000;

const botGuildCache    = new Map<string, CacheEntry<unknown>>();
const botGuildIdsCache = { entry: null as CacheEntry<Set<string>> | null };
const botGuildIdsInFlight = { promise: null as Promise<Set<string>> | null };

export async function fetchBotGuild(guildId: string): Promise<unknown | null> {
  const botToken = process.env["DISCORD_BOT_TOKEN"];
  if (!botToken) return null;

  const cached = botGuildCache.get(guildId);
  if (cached && cached.expiresAt > Date.now()) return cached.data;

  try {
    const res = await axios.get(`${BASE}/guilds/${guildId}?with_counts=true`, {
      headers: { Authorization: `Bot ${botToken}` },
    });
    botGuildCache.set(guildId, { data: res.data, expiresAt: Date.now() + BOT_GUILD_TTL_MS });
    return res.data;
  } catch {
    return botGuildCache.get(guildId)?.data ?? null;
  }
}

export async function fetchBotGuildIds(): Promise<Set<string>> {
  const botToken = process.env["DISCORD_BOT_TOKEN"];
  if (!botToken) return new Set();

  const cached = botGuildIdsCache.entry;
  if (cached && cached.expiresAt > Date.now()) return cached.data;

  if (botGuildIdsInFlight.promise) return botGuildIdsInFlight.promise;

  const request = axios
    .get<DiscordGuild[]>(`${BASE}/users/@me/guilds`, {
      headers: { Authorization: `Bot ${botToken}` },
    })
    .then((res) => {
      const ids = new Set(res.data.map((g) => g.id));
      botGuildIdsCache.entry = { data: ids, expiresAt: Date.now() + BOT_GUILD_IDS_TTL_MS };
      return ids;
    })
    .catch(() => {
      return botGuildIdsCache.entry?.data ?? new Set<string>();
    })
    .finally(() => {
      botGuildIdsInFlight.promise = null;
    });

  botGuildIdsInFlight.promise = request;
  return request;
}

// ── Permission helpers ────────────────────────────────────────────────────────

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

// ── Shared assertGuildAdmin ───────────────────────────────────────────────────
// Single implementation used by both guilds.ts and config.ts.
// Uses the cached fetchUserGuilds so it never causes additional Discord calls.

export async function assertGuildAdmin(
  req: import("express").Request,
  res: import("express").Response,
  guildId: string,
): Promise<boolean> {
  const accessToken = req.session.accessToken!;
  let userGuilds: DiscordGuild[];
  try {
    userGuilds = await fetchUserGuilds(accessToken);
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status;
    if (status === 429) {
      res.status(503).json({ error: "Discord API rate limit reached — please wait a moment and try again." });
    } else {
      res.status(502).json({ error: "Failed to reach Discord API." });
    }
    return false;
  }

  const guild = userGuilds.find((g) => g.id === guildId);
  if (!guild) {
    res.status(403).json({ error: "You are not a member of this guild." });
    return false;
  }
  if (!hasAdminPermission(guild.permissions, guild.owner)) {
    res.status(403).json({ error: "Administrator permission required." });
    return false;
  }
  return true;
}
