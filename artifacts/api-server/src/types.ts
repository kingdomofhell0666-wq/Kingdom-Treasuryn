import "express-session";

declare module "express-session" {
  interface SessionData {
    discordId:      string;
    username:       string;
    globalName:     string | null;
    discriminator:  string;
    avatar:         string | null;
    avatarUrl:      string;
    accessToken:    string;
    refreshToken:   string;
    tokenExpiresAt: number;
    oauthState:     string;
  }
}
