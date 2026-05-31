# 📈 Mock Trading Platform

[![Build Status](https://dev.azure.com/REPLACE_ORG/REPLACE_PROJECT/_apis/build/status/REPLACE_PIPELINE?branchName=main)](https://dev.azure.com/REPLACE_ORG/REPLACE_PROJECT/_build/latest?definitionId=REPLACE_ID&branchName=main)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Backend](https://img.shields.io/badge/backend-Flask-000000.svg)
![Frontend](https://img.shields.io/badge/frontend-React-61DAFB.svg)
![Bot](https://img.shields.io/badge/bot-interactions.py-5865F2.svg)

> A paper-trading platform that simulates buying and selling real stocks with live market data and **no real money**.
> **Philosophy: what happens in the real market happens in the sim** — taxes, dividends, splits, mergers, slippage and all.

The green **Build** badge above means the Azure Pipelines test suite is currently passing on `main`.

---

## What it is

An educational trading simulator with three components sharing a single backend:

- **Flask REST API** — the single source of truth. All trade execution, portfolio math, dividends, corporate actions, and taxes live here.
- **React website** — the public-facing frontend (hosted on Azure).
- **Discord bot** — runs on personal hardware and calls the Flask API over HTTPS.

Neither the website nor the bot contain business logic — they only make HTTP requests to Flask.

---

## Architecture

```
MarketData.app (live quotes)        FMP API (corporate actions)
         │                                    │
         ▼                                    ▼
                   Azure App Service
                   (Flask REST API)  ◄────►  Azure SQL Database
                      ╱          ╲
          Discord Bot              React Frontend
        (Pi / home hardware)      (Azure Static Web Apps)
```

| Layer | Tech |
|---|---|
| Backend | Python, Flask, SQLAlchemy, APScheduler |
| Database | Azure SQL Database (via `pyodbc`) |
| Auth | Google / Microsoft OAuth2 + pre-shared API keys |
| Frontend | React, Axios |
| Bot | Python, `interactions.py` (discord-py-interactions) |
| Hosting | Azure App Service (B1) + Azure Static Web Apps |

---

## Repository layout

```
backend/          Flask API — the single source of truth
  app/
    models/       SQLAlchemy tables (CQRS: holdings ledger + immutable transaction log)
    routes/       HTTP endpoints (auth, stocks, portfolio, orders, tax, user)
    services/     Business logic (trade, order, dividend, corporate actions, tax, stipend)
    scheduler/    APScheduler timed jobs (market open/close, taxes, stipends)
    utils/        Slippage model, market hours, fractional truncation, tax rates
  tests/          Pytest suite for the money-critical paths
frontend/         React app
bot/              Discord bot (interactions.py)
  commands/       Slash commands (/buy /sell /portfolio /price ...)
azure-pipelines.yml        Azure DevOps pipeline (test → deploy on push to main)
```

---

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in DB URL, API keys, OAuth secrets
python wsgi.py              # dev server on :8000
```

> **Note:** `pyodbc` needs the Microsoft ODBC Driver 18 at the OS level. On Azure App Service this is installed by `startup.sh`; locally, install it from Microsoft.

### Discord bot

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env        # DISCORD_BOT_TOKEN, FLASK_API_BASE_URL, BOT_API_KEY
python bot.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## Testing

The suite covers the financial logic where correctness matters most — order slippage, FIFO sell accounting, tax calculation with loss harvesting, fractional truncation, and market-hours rules.

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Tests run on an in-memory SQLite database (no external services needed) and execute automatically via **Azure Pipelines** on every push to `main` — the backend is deployed to Azure App Service only if they pass.

**What's covered:**

| Area | Examples |
|---|---|
| Slippage model | grace window, half-difference fills, stop/limit triggers |
| Trade execution | balance deduction, FIFO lot consumption, short vs long-term gains |
| Tax system | 22%/15% rates, dividend tax, loss harvesting, auto-liquidation |
| Portfolio | ACB, unrealized P&L, DRIP toggles |
| Market hours | open/close boundaries, weekends, holidays |
| Fractional shares | always truncates, never rounds up |

---

## Key design decisions

- **CQRS data model** — current holdings live in a small `holdings_ledger`; full history is an append-only `transactions` log. Portfolio reads stay fast as history grows.
- **`DECIMAL` everywhere** — no `FLOAT` for money, ever.
- **Slippage model** — limit/stop orders are checked hourly (not per-second), so a grace window + half-difference model approximates realistic fills. Disclosed in the ToS.
- **Scheduler runs in-process** — so the backend deploys with a **single** gunicorn worker; running multiple workers would duplicate every scheduled job.

---

## ⚠️ Disclaimer

This is a simulation for **educational and entertainment purposes only**. No real money, securities, or orders are involved. Tax figures use flat-rate approximations — consult a real professional for actual advice.
