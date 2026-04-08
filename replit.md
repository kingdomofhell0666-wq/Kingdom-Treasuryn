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
| `/identity [user]` | Kingdom Identity Card — rank, wealth, risk score, stats |
| `/wealth` | Quick wallet balance with flavor quote |
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
- **Tax system**: Rank-based rates from 12% (Forsaken) to 0% (Chancellor)
- **Transfer tax**: 2% to treasury
- **Shop tax**: 10% treasury, 90% burned
- **Cerberus**: risk_score 0–100; audit prob = risk × 0.3% (cap 50%); penalty 10–30% wallet
- **Black market**: 8-item pool, 4 rotate every 6h (deterministic seed); risk-increasing perks
- **Investments**: safe (1h, 5-10% guaranteed), medium (6h, 20-35%/75% win), risky (24h, 50-80%/50% win)
- **Transaction ledger**: Every action logged with accounts (user:{id}, treasury, kingdom_mint, void)

## Ranks & Costs (strict linear progression — no skipping)

Forsaken (default) → Vermin (1.5K) → Corrupted (6K) → Mythology (15K) → Folklore (35K) → Eschatology (80K) → Demonology (160K) → Archangel (400K) → Archdemon (1M) → Knight (2.5M) → Baron (5M) → Viscount (10M) → Count (20M) → Marquis (40M) → Duke (80M) → Chancellor (200M, 0% tax)

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

## Setup

1. Add `DISCORD_BOT_TOKEN` as a secret in the Secrets panel
2. Start the **Kingdom Treasury Bot** workflow
3. The bot will sync slash commands on startup

## Database

- File: `kingdom_treasury.db` (auto-created on first run)
- Tables: `users`, `transactions`, `treasury`, `cooldowns`, `investments`, `user_perks`
- Safe migrations via try/except ALTER TABLE for schema evolution
