import "express-session";

declare module "express-session" {
  interface SessionData {
    // Discord identity
    discordId:       string;
    username:        string;
    globalName:      string | null;
    discriminator:   string;
    avatar:          string | null;
    avatarUrl:       string;
    // OAuth tokens
    accessToken:     string;
    refreshToken:    string;
    tokenExpiresAt:  number;
    // OAuth CSRF
    oauthState:      string;
    // Guild access cache (5-min TTL)
    authorizedGuildIds: string[];
    guildsLastChecked:  number; // unix ms
  }
}
