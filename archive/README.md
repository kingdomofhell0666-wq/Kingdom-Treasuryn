# Archive — Kingdom Treasury Dashboard v1

Archived on 2026-04-12 during full dashboard reset.

## dashboard-v1/

Old React dashboard source (v1 implementation).

| Path | Description |
|------|-------------|
| `pages/guilds/` | All 19 guild-scoped pages (bot-status, kingdom-ranks, market, inventory, etc.) |
| `pages/login.tsx` | Discord OAuth login page |
| `pages/not-found.tsx` | 404 page |
| `components/layout.tsx` | Sidebar layout, PageHeader, PlaceholderPage components |
| `hooks/` | use-mobile, use-toast hooks |
| `lib/api.ts` | apiGet() helper with guild context |
| `App.tsx` | Full router with 20+ routes |

## api-v1/routes/

Old Express API routes that served the v1 dashboard.

| File | Description |
|------|-------------|
| `config.ts` | Guild config editor endpoints (roles, channels, thresholds) + bot-status |
| `data.ts` | Kingdom ranks leaderboard, market summary, inventory summary, rank registry |
| `guilds.ts` | Guild list, member list, economy data endpoints |
| `index.ts` | Old route registrar (all 5 routers) |

## What was preserved (NOT archived)

- `bot/` — entire Discord bot runtime
- `kingdom_treasury.db` — all economy, inventory, rank data
- `artifacts/api-server/src/routes/auth.ts` — Discord OAuth flow
- `artifacts/api-server/src/routes/health.ts` — health check endpoint
- `artifacts/api-server/src/lib/` — discord client, session, logger
- `artifacts/dashboard/src/components/ui/` — all shadcn components
- `lib/db/` — database schema definitions
