# Kingdom Treasury Bot

## Overview

A production-grade Discord economy bot for the **Kingdom of Hell** private server. Fully immersive infernal banking system with dark fantasy tone and layered economic mechanics.

## Stack

- **Language**: Python 3.11
- **Discord**: discord.py (app_commands / slash commands)
- **Database**: SQLite via aiosqlite
- **Config**: python-dotenv

## Architecture

```
bot/
├── bot.py               # KingdomTreasuryBot — main bot class
├── database/            # SQLite wrapper (Database class)
├── services/            # Business logic layer
│   ├── economy_service.py       # grind (5-tier, perk-aware), tribute, transfer
│   ├── rank_service.py          # rank definitions, tax rates, costs, can_ascend_to()
│   ├── cooldown_service.py      # cooldown management
│   ├── transaction_service.py   # ledger / double-entry accounting
│   ├── treasury_service.py      # kingdom treasury balance
│   ├── audit_service.py         # leaderboard, transaction history
│   ├── cerberus_service.py      # risk_score audit system
│   ├── blackmarket_service.py   # rotating 4/8 item black market
│   └── investment_service.py    # safe/medium/risky time-locked investments
├── ui/                  # Discord Views
│   ├── market_view.py           # paginated rank market
│   ├── identity_view.py         # identity card action buttons
│   ├── ascend_confirm_view.py   # 2-button ascension confirmation
│   └── blackmarket_view.py      # paginated buy interface
├── cogs/                # Command groups
│   ├── economy.py       # /grind /tribute /transfer /vault /market /ascend
│   ├── profile.py       # /identity /wealth
│   ├── investment.py    # /invest /portfolio /collect /withdraw
│   └── blackmarket.py   # /blackmarket
└── utils/               # Embeds + formatting
main.py                  # Entry point
```

## Slash Commands

| Command | Description |
|---|---|
| `/identity [user]` | Premium Kingdom Identity Card — skin-aware, rank, title, wealth, stats |
| `/wealth` | Quick wallet balance with flavor quote |
| `/skins` | Browse all card skins and ownership status |
| `/equip-skin <skin_id>` | Equip an owned card skin |
| `/titles` | Browse all titles and ownership status |
| `/equip-title <title>` | Equip an owned title |
| `/grind` | Mine DevilCoins (5-tier outcome, perk-aware, Cerberus trigger) |
| `/tribute` | Daily realm tribute (24h cooldown, +200 DC bonus for 5+ grinds) |
| `/transfer @user amount` | Transfer DC with 2% treasury levy |
| `/vault` | View total Kingdom Treasury reserves |
| `/market` | Browse all purchasable ranks with pagination |
| `/ascend <rank>` | Purchase next rank with 45s confirmation; 10% treasury, 90% burned |
| `/blackmarket` | Browse 4 rotating forbidden items (6h rotation, risk-increasing) |
| `/invest safe/medium/risky amount` | Time-locked investments with variable returns |
| `/portfolio` | View active and matured investments |
| `/collect` | Claim all matured investments |
| `/withdraw` | Early withdrawal of all positions (20% penalty) |

## Economy

- **Currency**: DevilCoins (DC)
- **Default rank**: Forsaken (not purchasable)
- **Grind tiers**: 60% common (250-350) / 20% meager (100-200) / 10% failure (0) / 7% rich (400-600) / 3% jackpot (800-1200)
- **Tax system**: Rank-based rates from 12% (Forsaken) to 1% (Duke)
- **Transfer tax**: 2% to treasury
- **Shop tax**: 10% treasury, 90% burned
- **Cerberus**: risk_score 0–100; audit prob = risk × 0.3% (cap 50%); penalty 10–30% wallet
- **Black market**: 8-item pool, 4 rotate every 6h (deterministic seed); risk-increasing perks
- **Investments**: safe (1h, 5-10% guaranteed), medium (6h, 20-35%/75% win), risky (24h, 50-80%/50% win)
- **Transaction ledger**: Every action logged with accounts (user:{id}, treasury, kingdom_mint, void)

## Ranks & Costs (strict linear progression — no skipping)

**Public Kingdom Ranks (purchasable by players):**
Forsaken (default) → Vermin (1.5K) → Corrupted (6K) → Folklore (15K) → Mythology (35K) → Demonology (80K) → Eschatology (160K) → Archangel (400K) → Archdemon (1M) → Knight (2.5M) → Baron (5M) → Viscount (10M) → Count (20M) → Marquis (40M) → **Duke (80M, ceiling)**

**Chancellor = STAFF/MODERATOR ROLE ONLY — excluded from all public ascension logic.**
- Chancellor is NOT purchasable, NOT in /ascend, NOT in cooldown config, NOT in leaderboard hierarchy, NOT on dashboard rank pages.
- `PUBLIC_KINGDOM_RANKS` in `bot/services/rank_service.py` is the single source of truth.

## Perks (via Black Market)

| Perk Type | Effect |
|---|---|
| `tax_exempt` | Next N grinds exempt from tax |
| `tax_reduction` | Reduces effective tax rate by value% for N grinds |
| `grind_boost` | Forces rich/jackpot outcome on next grind |
| `grind_bonus` | Adds flat DC to next N grind earnings |
| `grind_ceiling` | Raises reward ceiling by +N DC for next M grinds |
| `audit_immunity` | Blocks next Cerberus audit |
| `risk_reduce` | Instantly reduces risk_score by N points |

## Dashboard (Admin Web Panel)

A production-grade admin dashboard at `/dashboard/` built with React + Vite + Discord OAuth2.

### Stack

- **Frontend**: React + Vite (static build served by Express)
- **Backend**: Express API server at port 8080
- **Database**: PostgreSQL (Drizzle ORM) — `guild_configs`, `dashboard_sessions`
- **Auth**: Discord OAuth2 via session cookies (connect-pg-simple)

### Architecture

```
artifacts/dashboard/          # React + Vite SPA (build output served by api-server)
artifacts/api-server/         # Express API server
  src/
    app.ts                    # Middleware + routes + static file serving for /dashboard/
    lib/discord.ts            # Discord OAuth2 + API helpers
    lib/session.ts            # express-session + PostgreSQL store
    routes/
      auth.ts                 # /api/auth/discord, /callback, /logout, /me
      guilds.ts               # /api/guilds, /api/guilds/:id, /config, /stats, /bot-status
lib/api-spec/openapi.yaml     # OpenAPI spec (source of truth)
lib/api-client-react/         # Generated React Query hooks (do not edit)
lib/api-zod/                  # Generated Zod schemas (do not edit)
lib/db/                       # Drizzle ORM + PostgreSQL
  src/schema/
    guild_configs.ts          # Per-guild bot configuration table
    dashboard_sessions.ts     # Session storage table
```

### Dashboard Pages

| Path | Description |
|---|---|
| `/dashboard/` | Login page with Discord OAuth2 |
| `/dashboard/guilds` | Guild selection — only shows guilds with bot + admin perms |
| `/dashboard/guilds/:id` | Dashboard overview — bot status, economy stats |
| `/dashboard/guilds/:id/economy` | Economy config — grind/tribute rewards, cooldowns, taxes |
| `/dashboard/guilds/:id/currency` | Currency name + icon with live preview |
| `/dashboard/guilds/:id/channels` | Command channel routing (per-channel per-command) |
| `/dashboard/guilds/:id/commands` | Role-based command permissions (allow/deny per role) |
| `/dashboard/guilds/:id/ranks` | Rank→Discord role mapping + per-rank ascension cooldowns |
| `/dashboard/guilds/:id/leaderboard` | Scheduled leaderboard posting (daily/weekly/monthly) |
| `/dashboard/guilds/:id/ascension` | Ascension announcement channel + message template |
| `/dashboard/guilds/:id/treasury` | Live treasury stats + wealth leaderboard (top 20) |
| `/dashboard/guilds/:id/bot-status` | Bot online status, uptime, heartbeat, active commands |
| `/dashboard/guilds/:id/settings` | General settings (timezone, etc.) |
| `/dashboard/guilds/:id/reset` | Two-confirm economy wipe (preserves config) |

### Building

The dashboard frontend is a static build served by Express:
```bash
# Build dashboard
cd artifacts/dashboard && PORT=5000 BASE_PATH=/dashboard/ pnpm run build
# API server serves it automatically from artifacts/dashboard/dist/public/
```

### Important Notes

- Dashboard workflow is FAILED (known port detection issue) — the static build is served from the API server instead
- Auth OAuth2 callback URL is auto-detected from `REPLIT_DOMAINS` env var
- Guild configs stored in PostgreSQL `guild_configs` table
- Bot stats read from `kingdom_treasury.db` SQLite via better-sqlite3

## Setup

1. Add `DISCORD_BOT_TOKEN` as a secret in the Secrets panel
2. Start the **Kingdom Treasury Bot** workflow
3. The bot will sync slash commands on startup

## Database

- **Bot DB**: `kingdom_treasury.db` (SQLite, auto-created on first run)
  - Tables: `users`, `transactions`, `treasury`, `cooldowns`, `investments`, `user_perks`
  - Safe migrations via try/except ALTER TABLE for schema evolution
- **Dashboard DB**: PostgreSQL (DATABASE_URL env var)
  - Tables: `guild_configs`, `dashboard_sessions`, `command_routing`, `command_permissions`, `rank_role_mapping`, `leaderboard_settings`, `ascension_announcement_settings`, `rank_cooldown_settings`
- **Bot heartbeat**: Bot writes `start_time` + `last_heartbeat` to SQLite `meta` table every 30s; API reads it for status checks
