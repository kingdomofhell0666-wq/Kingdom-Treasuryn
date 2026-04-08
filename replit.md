# Kingdom Treasury Bot

## Overview

A production-grade Discord economy bot for the **Kingdom of Hell** private server. Fully immersive infernal banking system with dark fantasy tone and real economic mechanics.

## Stack

- **Language**: Python 3.11
- **Discord**: discord.py (app_commands / slash commands)
- **Database**: SQLite via aiosqlite
- **Config**: python-dotenv

## Architecture

```
bot/
├── bot.py               # KingdomTreasuryBot — main bot class
├── models/              # Data models (User, Transaction, Treasury)
├── database/            # SQLite wrapper (Database class)
├── services/            # Business logic layer
│   ├── economy_service.py   # grind, tribute, transfer
│   ├── rank_service.py      # rank definitions, tax rates, costs
│   ├── cooldown_service.py  # cooldown management
│   ├── transaction_service.py # ledger / double-entry
│   ├── treasury_service.py  # kingdom treasury
│   └── audit_service.py     # leaderboard, history
├── ui/                  # Discord Views (market pagination)
├── cogs/                # Command groups
│   ├── economy.py       # /grind /tribute /transfer /market /ascend
│   └── profile.py       # /identity /wealth
└── utils/               # Embeds + formatting
main.py                  # Entry point
```

## Slash Commands

| Command | Description |
|---|---|
| `/identity [user]` | Kingdom Identity Card — rank, wealth, stats |
| `/wealth` | Quick wallet balance |
| `/grind` | Mine DevilCoins (30m cooldown) |
| `/tribute` | Daily realm tribute (24h cooldown, +200 DC bonus for 5+ grinds) |
| `/transfer @user amount` | Transfer DC with 2% treasury levy |
| `/market` | Browse purchasable ranks with pagination |
| `/ascend <rank>` | Purchase a rank; 10% to treasury, 90% burned |

## Economy

- **Currency**: DevilCoins (DC)
- **Default rank**: Forsaken (not purchasable)
- **Tax system**: Rank-based rates from 12% (Forsaken) to 1% (Duke)
- **Treasury**: Collects all taxes and fees; fully tracked
- **Transaction ledger**: Every action logged with accounts (user:{id}, treasury, kingdom_mint, void)

## Ranks & Costs

Forsaken (default) → Vermin (1.5K) → Corrupted (6K) → Mythology (15K) → Folklore (35K) → Eschatology (80K) → Demonology (160K) → Archangel (400K) → Archdemon (1M) → Knight (2.5M) → Baron (5M) → Viscount (10M) → Count (20M) → Marquis (40M) → Duke (80M)

## Setup

1. Add `DISCORD_BOT_TOKEN` as a secret in the Secrets panel
2. Start the **Kingdom Treasury Bot** workflow
3. The bot will sync slash commands on startup

## Database

- File: `kingdom_treasury.db` (auto-created on first run)
- Schema supports future: `owned_titles`, `equipped_title`, `owned_skins`, `equipped_skin`
