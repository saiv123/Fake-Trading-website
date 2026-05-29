# Mock Trading Platform — Technical Specification

> **Version:** 1.0  
> **Status:** Pre-build reference document  
> **Philosophy:** What happens in the real market happens in the sim.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Glossary — Trading & Technical Terms](#2-glossary--trading--technical-terms)
3. [Architecture & Tech Stack](#3-architecture--tech-stack)
4. [Shared Foundation — Database](#4-shared-foundation--database)
5. [Shared Foundation — Stock Data Strategy](#5-shared-foundation--stock-data-strategy)
6. [Flask / Backend](#6-flask--backend)
   - [Difficulty System](#61-difficulty-system)
   - [Authentication & Security](#62-authentication--security)
   - [Trade Execution Logic](#63-trade-execution-logic)
   - [Order Execution & Slippage Model](#64-order-execution--slippage-model)
   - [Corporate Actions System](#65-corporate-actions-system)
   - [DRIP — Dividend Reinvestment](#66-drip--dividend-reinvestment)
   - [Tax System](#67-tax-system)
   - [Monthly Stipend System](#68-monthly-stipend-system)
   - [Fractional Shares](#69-fractional-shares)
   - [Flask API Endpoints](#610-flask-api-endpoints)
   - [Scheduled Jobs](#611-scheduled-jobs)
   - [Environment Variables — Flask](#612-environment-variables--flask)
7. [Discord Bot](#7-discord-bot)
   - [Communication Pattern](#71-communication-pattern)
   - [Account Linking Flow](#72-account-linking-flow)
   - [Slash Commands](#73-slash-commands)
   - [Environment Variables — Bot](#74-environment-variables--bot)
8. [React Frontend](#8-react-frontend)
   - [Pages & Components](#81-pages--components)
   - [API Integration](#82-api-integration)
9. [Project Folder Structure](#9-project-folder-structure)
10. [Terms of Service Disclosures](#10-terms-of-service-disclosures)
11. [V1 Scope vs Future Features](#11-v1-scope-vs-future-features)

---

## 1. Project Overview

A paper trading platform where users simulate buying and selling stocks using real live market data with no real money. The platform is educational — users learn how markets, taxes, dividends, and corporate actions work in a realistic but consequence-free environment.

**Three components, one backend:**

- **Flask REST API** — core backend, all business logic lives here
- **React website** — public-facing frontend, hosted on Azure
- **Discord bot** — runs on personal hardware, calls the Flask API remotely

> **Key design principle:** The Flask API is the single source of truth. Neither the Discord bot nor the React frontend contain trade execution, portfolio calculation, dividend processing, or DB logic. They only make HTTP requests to Flask endpoints.

---

## 2. Glossary — Trading & Technical Terms

A reference for anyone unfamiliar with stock market or database terminology used throughout this document.

---

### Stock Market Terms

**Ask (Ask Price)**
The lowest price a seller is currently willing to accept for a stock. When you buy at market price, you're paying the ask. Think of it as the "store price" on the shelf.

**Average Cost Basis (ACB)**
The blended average price you paid per share across all your purchases of a stock. If you bought 10 shares at $100 and 10 more at $120, your ACB is $110. Used to calculate unrealized P&L on the portfolio page. Not used for tax calculations — taxes use the actual lot price (see: Tax Lot).

**Bid (Bid Price)**
The highest price a buyer is currently willing to pay for a stock. When you sell at market price, you receive the bid. The gap between bid and ask is called the **spread**.

**Capital Gains**
The profit made when you sell a stock for more than you paid for it. If you bought at $100 and sold at $150, you have a $50 capital gain. Capital gains are taxable.
- **Short-term:** Held less than 1 year — taxed at your ordinary income rate (22% in this sim)
- **Long-term:** Held 1 year or more — taxed at a lower preferential rate (15% in this sim)

**Capital Loss**
The opposite of a capital gain — when you sell for less than you paid. Losses can offset gains to reduce your tax bill (see: Loss Harvesting).

**Corporate Action**
Any event initiated by a company that materially affects its stock. Examples: stock splits, dividends, mergers, acquisitions, spinoffs, delistings, ticker changes.

**Cost Basis**
What you originally paid for a specific lot of shares, used to calculate gain or loss when you sell. Different from ACB — cost basis is per-lot, ACB is a blended average across all lots.

**Day Range**
The high and low price a stock traded at during the current trading day.

**Delisting**
When a stock is removed from a stock exchange. Can happen due to bankruptcy, failure to meet exchange requirements, or voluntary withdrawal. After delisting, the stock may become worthless or very difficult to trade.

**Dividend**
A cash or stock payment made by a company to its shareholders, typically from profits. Paid on a regular schedule (quarterly for most US companies).
- **Cash dividend:** You receive cash per share held
- **Stock dividend:** You receive additional shares instead of cash
- **Special dividend:** A one-time irregular payout, not part of the regular schedule
- **Ex-dividend date:** You must own the stock *before* this date to receive the dividend
- **Pay date:** The date the dividend is actually paid out

**DRIP (Dividend Reinvestment Program)**
Instead of receiving dividend cash, DRIP automatically uses it to buy more shares of the same stock. Compounds your position over time without you having to manually reinvest.

**ETF (Exchange-Traded Fund)**
A fund that holds a basket of stocks and trades on an exchange like a regular stock. For example, VTI holds thousands of US stocks, so buying one share of VTI gives you exposure to the whole US market.

**FIFO (First In, First Out)**
The method used to determine which shares are sold first when you sell a stock. The oldest shares you bought are sold before newer ones. This affects which cost basis is used and therefore your tax liability.

**Limit Order**
An order to buy or sell a stock only at a specific price or better.
- **Limit buy:** Only execute if the price drops to or below your limit
- **Limit sell:** Only execute if the price rises to or above your limit
Unlike a market order, a limit order is not guaranteed to fill.

**Margin Trading**
Borrowing money from a broker to buy more stock than your cash balance allows. Amplifies both gains and losses. **Not implemented in this platform** — all trading is cash-only.

**Market Order**
An order to buy or sell immediately at the current market price. Guaranteed to fill (during market hours) but the exact price may vary slightly from what you see.

**Merger / Acquisition**
When one company buys another. Shareholders of the acquired company typically receive either cash per share (cash acquisition) or shares of the acquiring company (stock acquisition). The acquired company's stock usually stops trading.

**P&L (Profit and Loss)**
- **Unrealized P&L:** The gain or loss on positions you still hold, based on current price vs your cost basis. "Unrealized" because you haven't sold yet — it's on paper only.
- **Realized P&L:** The actual gain or loss locked in when you sell. This is what gets taxed.

**Paper Trading / Mock Trading**
Simulated trading with fake money using real market prices. Used for learning and practice without financial risk. This entire platform is a paper trading sim.

**Reverse Split**
When a company reduces its share count and increases the price proportionally. Example: 1-for-3 reverse split means every 3 shares become 1 share, but the price triples. Total value stays the same. Companies often do this to avoid being delisted for having a stock price that's too low.

**Slippage**
The difference between the price you expected to pay/receive and the price you actually got. Happens because markets move between when you place an order and when it fills. In this sim, slippage is simulated via the grace window + half-difference model to account for hourly (not per-second) price checking.

**Spinoff**
When a company splits off a division into a separate publicly traded company. Existing shareholders typically receive shares in the new company.

**Stop Order (Stop-Loss)**
An order to automatically sell if a stock's price drops to a specified level. Used to limit losses on a position. Example: you own AAPL at $200, you set a stop at $180 — if it drops to $180 your shares sell automatically.

**Stock Split**
When a company increases its share count and decreases the price proportionally. Example: 4-for-1 split means every 1 share becomes 4 shares, but the price quarters. Total value stays the same. Companies do this to make shares more affordable.

**Stop-Limit Order**
A combination of a stop and a limit order. When the price hits the stop price, a limit order is placed. The trade only executes if it can fill at the limit price or better.

**Tax Lot**
A record of a specific purchase of shares — how many shares, at what price, on what date. Every time you buy a stock (even the same stock), a new tax lot is created. When you sell, FIFO determines which lots are consumed first, and each lot's cost basis is used to calculate the gain or loss.

**Ticker (Ticker Symbol)**
The unique abbreviation used to identify a stock on an exchange. Examples: AAPL (Apple), NVDA (NVIDIA), MSFT (Microsoft).

**52-Week Range**
The highest and lowest price a stock has traded at over the past 52 weeks (one year). Gives context for whether the current price is near its high or low.

**ADR (American Depositary Receipt)**
A way to invest in foreign companies through US exchanges. For example, Toyota is a Japanese company but trades on the NYSE as TM. Buying TM is equivalent to owning Toyota shares without trading on a foreign exchange.

---

### Technical / Database Terms

**ACB** → See Average Cost Basis above.

**CQRS (Command Query Responsibility Segregation)**
A database design pattern where you separate the data structure you write to from the data structure you read from. In this platform: trades are written to the Transaction History (append-only log), but portfolio reads come from the Holdings Ledger (current state table). This keeps reads fast even as history grows large.

**Composite Index**
A database index on multiple columns together. Example: an index on `(user_id, ticker)` makes queries filtering by both user and ticker very fast, without scanning the whole table.

**DECIMAL vs FLOAT**
Two ways databases store numbers with decimal points. `FLOAT` is approximate — it can introduce tiny rounding errors (e.g. $99.9999999 instead of $100.00). `DECIMAL` is exact. For financial values, always use `DECIMAL`. This is a hard rule throughout the codebase.

**FK (Foreign Key)**
A column in one table that references the primary key of another table. Creates a link between tables. Example: `holdings_ledger.user_id` is a FK referencing `users.id` — it ensures every holding belongs to a real user.

**httpOnly Cookie**
A browser cookie that JavaScript cannot access. Used to store JWT tokens securely — malicious scripts on the page can't steal them the way they could if tokens were stored in localStorage.

**JWT (JSON Web Token)**
A compact, signed token used for authentication. When you log in, the server issues a JWT. You send it with every request to prove who you are. Has an expiry time — this platform uses a 15-minute access token and a 7-day refresh token.

**ORM (Object Relational Mapper)**
A library that lets you interact with a database using Python classes and objects instead of raw SQL. SQLAlchemy is the ORM used here. You define a `User` class in Python, and SQLAlchemy handles the SQL underneath.

**PK (Primary Key)**
A column (or set of columns) that uniquely identifies each row in a table. Every table has one. Examples: `users.id`, `stocks.ticker`.

**Refresh Token**
A long-lived token (7 days) used to get a new short-lived access token (15 min) without requiring the user to log in again. Stored in an httpOnly cookie.

**SQLAlchemy Transaction**
A database operation that groups multiple SQL statements together — either all succeed or all fail (roll back). Critical for keeping the Holdings Ledger and Transaction History in sync. If writing to one table succeeds but the other fails, a transaction ensures the first write is also rolled back.

**TOTP (Time-Based One-Time Password)**
The technology behind authenticator apps (Google Authenticator, Authy). Generates a 6-digit code that changes every 30 seconds. Used for MFA (Multi-Factor Authentication). Planned for V2.

---

## 3. Architecture & Tech Stack

### System Diagram

```
MarketData.app (live quotes)       FMP API (corporate actions)
         ↓                                    ↓
                   Azure App Service
                   (Flask REST API)  ←——→  Azure MySQL Flexible Server
                      ↙        ↘
          Discord Bot             React Frontend
          (Pi / home hw)         (Azure Static Web Apps)
```

### Backend
| Component | Choice | Notes |
|---|---|---|
| Language | Python | |
| Framework | Flask | |
| Database | Azure Database for MySQL Flexible Server | MariaDB-compatible, identical SQL syntax |
| ORM | SQLAlchemy | Full model definitions, transaction wrapping |
| Hosting | Azure App Service B1 (~$13/mo) | B1 required — free F1 tier sleeps and breaks scheduled jobs |
| Scheduler | APScheduler | All timed/recurring jobs |
| Price API | MarketData.app | Single endpoint, full quote snapshot per ticker |
| Corporate Actions API | Financial Modeling Prep (FMP) | Dividends, splits, M&A, market calendar |

### Frontend
| Component | Choice |
|---|---|
| Framework | React |
| Hosting | Azure Static Web Apps or served via Flask |
| HTTP Client | Axios or Fetch API |

### Discord Bot
| Component | Choice |
|---|---|
| Language | Python |
| Library | discord.py |
| Hosting | Personal hardware (Raspberry Pi / home server) |
| Communication | HTTPS to Flask public Azure URL |

### Infrastructure & Cost
- **Azure App Service B1:** ~$13/month
- **Azure MySQL Flexible Server (Burstable B1ms):** ~$12–15/month
- **Total:** ~$25–30/month
- **Effective cost: $0** — developer has $200/month Azure credits via Microsoft employee benefit

---

## 4. Shared Foundation — Database

> **Rule:** Use `DECIMAL` for all financial values. Never use `FLOAT`.

### Why Two Tables (CQRS Pattern)

The platform separates current state (holdings) from historical record (transactions). This is called **CQRS — Command Query Responsibility Segregation**:

- **Holdings Ledger** — always small (~20 rows per user). Portfolio reads are instant regardless of trading history length.
- **Transaction History** — append-only log. Only queried when user requests history or taxes are calculated.

**Query cost at scale** (1,000 users × 500 transactions = 500,000 rows):

```sql
-- ❌ ONE TABLE — scans all history on every portfolio load
SELECT ticker, SUM(CASE WHEN type='BUY' THEN qty ELSE -qty END)
FROM transactions WHERE user_id = 42;

-- ✅ TWO TABLES — holdings ledger is always small and fast
SELECT ticker, SUM(qty_remaining)
FROM holdings_ledger WHERE user_id = 42;
```

### Atomicity Rule

Every operation touching both tables **must** be wrapped in a SQLAlchemy database transaction. If either step fails, both roll back. Violating this causes silent data corruption.

```python
try:
    db.session.begin()
    update_holdings_ledger(...)
    insert_transaction_history(...)
    db.session.commit()
except Exception:
    db.session.rollback()
    raise
```

---

### Table: Users

```sql
CREATE TABLE users (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    email             VARCHAR(255) UNIQUE NOT NULL,
    password_hash     VARCHAR(255),                          -- nullable for OAuth-only users
    display_name      VARCHAR(100) NOT NULL,
    google_id         VARCHAR(255),
    microsoft_id      VARCHAR(255),
    discord_id        VARCHAR(255),                          -- set after account linking
    mfa_enabled       BOOLEAN DEFAULT FALSE,                 -- V2
    mfa_secret        VARCHAR(255),                          -- V2, encrypted at rest
    difficulty        ENUM('beginner','intermediate','hard','expert') NOT NULL,
    starting_balance  DECIMAL(15,2) NOT NULL,                -- immutable after creation
    balance           DECIMAL(15,2) NOT NULL,                -- current paper cash
    state             VARCHAR(2) NOT NULL,                   -- US state for tax calculation
    last_active_at    DATETIME,                              -- updated on every auth'd request
    drip_all          BOOLEAN DEFAULT FALSE,                 -- UI state only
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME ON UPDATE CURRENT_TIMESTAMP
);
```

> `starting_balance` and `difficulty` are immutable. Any PUT request attempting to modify them returns HTTP 403.

---

### Table: Stocks (Price Cache)

```sql
CREATE TABLE stocks (
    ticker            VARCHAR(10) PRIMARY KEY,
    company_name      VARCHAR(255),
    last_price        DECIMAL(15,4),
    day_open          DECIMAL(15,4),
    day_high          DECIMAL(15,4),
    day_low           DECIMAL(15,4),
    after_hours_price DECIMAL(15,4),                        -- displayed only, not tradeable
    bid               DECIMAL(15,4),
    ask               DECIMAL(15,4),
    change_amount     DECIMAL(15,4),
    change_percent    DECIMAL(8,4),
    week_52_high      DECIMAL(15,4),
    week_52_low       DECIMAL(15,4),
    volume            BIGINT,
    last_updated      DATETIME,
    is_active         BOOLEAN DEFAULT TRUE                   -- false for delisted/renamed tickers
);
```

---

### Table: Holdings Ledger (Current State)

One row per tax lot. Every BUY creates a new row. SELLs reduce `qty_remaining` FIFO. Rows at zero are deleted.

```sql
CREATE TABLE holdings_ledger (
    lot_id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    ticker          VARCHAR(10) NOT NULL,
    qty_remaining   DECIMAL(15,2) NOT NULL,
    cost_per_share  DECIMAL(15,4) NOT NULL,
    purchased_at    DATETIME NOT NULL,
    drip_enabled    BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id),
    INDEX idx_user_ticker (user_id, ticker),
    INDEX idx_user_ticker_date (user_id, ticker, purchased_at)
);
```

**Key queries:**
```sql
-- Portfolio summary (ACB = average cost basis)
SELECT ticker,
       SUM(qty_remaining) AS total_shares,
       SUM(qty_remaining * cost_per_share) / SUM(qty_remaining) AS acb
FROM holdings_ledger
WHERE user_id = ? AND qty_remaining > 0
GROUP BY ticker;

-- FIFO sell — oldest lots first
SELECT * FROM holdings_ledger
WHERE user_id = ? AND ticker = ? AND qty_remaining > 0
ORDER BY purchased_at ASC;
```

---

### Table: Transaction History (Immutable Log)

Append-only. Rows are NEVER updated or deleted. `short_term_gain` and `long_term_gain` are calculated at sell time and stored permanently.

```sql
CREATE TABLE transactions (
    tx_id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    ticker           VARCHAR(10),                            -- NOT a FK — preserved after delisting
    type             ENUM(
                       'BUY','SELL',
                       'DIVIDEND_CASH','DIVIDEND_STOCK','DRIP',
                       'SPLIT','CORPORATE_ACTION_CASHOUT',
                       'STIPEND','TAX_PAYMENT'
                     ) NOT NULL,
    quantity         DECIMAL(15,2),
    price_per_share  DECIMAL(15,4),
    total_value      DECIMAL(15,2) NOT NULL,                 -- positive = credit, negative = debit
    short_term_gain  DECIMAL(15,2),                          -- SELL rows only
    long_term_gain   DECIMAL(15,2),                          -- SELL rows only
    term             ENUM('SHORT','LONG','MIXED'),
    lot_details      JSON,                                   -- SELL: breakdown of lots consumed
    notes            VARCHAR(500),
    executed_at      DATETIME NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id),
    INDEX idx_user_date (user_id, executed_at),
    INDEX idx_user_type_date (user_id, type, executed_at)
);
```

---

### Table: Orders

```sql
CREATE TABLE orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    ticker      VARCHAR(10) NOT NULL,
    order_type  ENUM('MARKET','LIMIT','STOP','STOP_LIMIT') NOT NULL,
    direction   ENUM('BUY','SELL') NOT NULL,
    quantity    DECIMAL(15,2) NOT NULL,
    limit_price DECIMAL(15,4),
    stop_price  DECIMAL(15,4),
    status      ENUM('PENDING','FILLED','EXPIRED','CANCELLED') DEFAULT 'PENDING',
    fill_price  DECIMAL(15,4),
    placed_at   DATETIME NOT NULL,
    expires_at  DATETIME NOT NULL,                           -- 6hrs from placement OR market close
    filled_at   DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id),
    INDEX idx_pending (status, ticker)
);
```

---

### Table: Corporate Actions Log

```sql
CREATE TABLE corporate_actions_log (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    ticker         VARCHAR(10) NOT NULL,
    action_type    ENUM(
                     'DIVIDEND_CASH','DIVIDEND_STOCK',
                     'SPLIT_FORWARD','SPLIT_REVERSE',
                     'MERGER','ACQUISITION','SPINOFF',
                     'TICKER_CHANGE','DELISTING'
                   ) NOT NULL,
    effective_date DATE NOT NULL,
    details        JSON NOT NULL,
    processed_at   DATETIME,                                 -- null until applied
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ticker (ticker),
    INDEX idx_date (effective_date),
    INDEX idx_unprocessed (processed_at, effective_date)
);
```

---

### Table: Watchlist (V2 — schema defined now)

```sql
CREATE TABLE watchlist (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT NOT NULL,
    ticker   VARCHAR(10) NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_watchlist (user_id, ticker)
);
```

---

## 5. Shared Foundation — Stock Data Strategy

### Two External APIs

**MarketData.app** — live price quotes
- Endpoint: `GET /v1/stocks/quotes/{ticker}/?52week=true`
- Single call returns: price, bid, ask, day high/low, open, change, change%, volume, 52-week high/low
- After-hours price via extended hours endpoint — stored in `after_hours_price`, displayed only

**Financial Modeling Prep (FMP)** — corporate actions & calendar
- Dividend calendar, split calendar, M&A announcements, ticker changes, market holidays
- Called once daily at 9:00 AM ET — one call covers the entire market, not per-ticker

### When MarketData.app Is Called

| Trigger | Action |
|---|---|
| 9:30 AM ET (market open, trading days) | Fetch prices for all tickers in stocks table |
| 4:00 PM ET (market close, trading days) | Final EOD snapshot + after-hours price |
| On-demand (user views stale stock) | Fetch single ticker, update DB, return |
| Hourly order check | Fetch prices for tickers with PENDING orders only |
| **Never** | On every page load, portfolio view, or trade execution |

### Staleness Definition

- **During market hours:** stale if `last_updated` > 15 minutes ago
- **Outside market hours:** stale if `last_updated` is before the most recent market close
- **After-hours price:** informational only, never used in order execution

### Market Coverage (V1)

| | Detail |
|---|---|
| ✅ In scope | All US-listed securities — NYSE, NASDAQ, large/mid/small/micro cap, OTC |
| ✅ In scope | US-listed ETFs tracking international/emerging markets (VWO, EEM, VXUS) |
| ✅ In scope | ADRs — foreign companies on US exchanges (TM, ASML, TSM) |
| ❌ Out of scope | Direct foreign exchange trading (Tokyo, London, etc.) |

---

## 6. Flask / Backend

### 8.1 Difficulty System

Starting balance is chosen at registration and is **permanent**.

| Difficulty | Starting Balance | Description |
|---|---|---|
| Beginner | $100,000 | Stress-free. Mirrors real paper trading platforms. |
| Intermediate | $25,000 | Mirrors the FINRA PDT minimum — a real-world threshold. |
| Hard | $10,000 | Meaningful constraints. Every allocation matters. |
| Expert | $1,000 | Every trade counts. Very limited diversification. |

**Registration flow:**
1. User completes basic info (email, password, display name, state)
2. User selects difficulty tier
3. Server maps difficulty → `starting_balance`, sets both fields, creates account

**API enforcement:** Any PUT attempting to modify `difficulty` or `starting_balance` returns HTTP 403.

---

### 8.2 Authentication & Security

**Email/Password**
- Passwords hashed with bcrypt (minimum cost factor 12)
- JWT access token (15 min) + refresh token (7 day)
- Tokens stored in httpOnly, SameSite=Strict cookies — never localStorage

**OAuth2 (Google & Microsoft)**
- Use Authlib or Flask-Dance
- First OAuth login → create user record
- Subsequent OAuth login → match by provider ID
- If OAuth email matches existing account → link providers automatically
- Difficulty selection still required on first OAuth registration

**Internal API Key**
- All `/api/internal/` routes require `X-Internal-Key` header
- Stored in `.env` on Flask and Discord bot — never hardcoded or committed

**MFA (V2)**
- TOTP via pyotp
- `mfa_secret` encrypted at rest
- Stub endpoints: `POST /api/auth/mfa/setup`, `POST /api/auth/mfa/verify`

---

### 7.3 Trade Execution Logic

#### Full BUY Flow

1. Validate market open / queue if after-hours
2. Validate `balance >= quantity × price`
3. Fetch price (refresh if stale)
4. Apply slippage model if limit order
5. Deduct cost from `users.balance`
6. Insert new lot into `holdings_ledger`
7. Insert `BUY` row into `transactions`
8. Mark order `FILLED`
9. Return portfolio snapshot

#### Full SELL Flow (FIFO)

1. Validate market open / queue if after-hours
2. Validate sufficient quantity held
3. Fetch price (refresh if stale)
4. Apply slippage model if stop/limit order
5. Consume oldest lots first (FIFO by `purchased_at`)
6. Per lot: calculate gain/loss, determine term (≥1 year = long-term)
7. Update/delete `holdings_ledger` rows
8. Add proceeds to `users.balance`
9. Insert `SELL` row with `short_term_gain`, `long_term_gain`, `term`, `lot_details` JSON
10. Mark order `FILLED`
11. Return portfolio snapshot

**Average cost basis formula:**
```
new_acb = ((old_qty × old_acb) + (new_qty × fill_price)) / (old_qty + new_qty)
```

---

### 7.4 Order Execution & Slippage Model

#### Trading Hours
- **Market hours:** 9:30 AM – 4:00 PM ET, Monday–Friday, excluding holidays
- **After-hours prices:** Displayed only. Not used for execution.
- **No pre-market or after-hours execution**

#### Order Types

| Type | Description |
|---|---|
| Market | Execute immediately at current DB price |
| Limit (Buy) | Execute when price ≤ limit price |
| Limit (Sell) | Execute when price ≥ limit price |
| Stop | Sell when price ≤ stop price |
| Stop-Limit | Trigger at stop price, fill only if within limit price |

#### Order Duration
- Maximum: **6 hours from placement OR market close**, whichever comes first
- No GTC orders
- Market close expires all remaining PENDING orders

#### After-Hours Queuing
Orders placed outside market hours queue as PENDING and execute as market orders at next day's open. The 6-hour timer starts at market open, not placement time.

#### Slippage Model

Limit/stop orders are checked **hourly** (9:30, 10:30 ... 3:30 PM ET). Because prices aren't monitored per-second, a grace window and slippage model is applied:

**BUY limit order** (limit = L, market price = P):

| Condition | Execution |
|---|---|
| `P ≤ L` | Execute at P (ideal) |
| `P > L` and `P - L ≤ $1.00` | Execute at P (grace window) |
| `P > L` and `P - L > $1.00` | Execute at `L + ((P - L) / 2)` (slippage) |

**SELL stop order** (stop = S, market price = P):

| Condition | Execution |
|---|---|
| `P ≥ S` | Do nothing (not triggered) |
| `P < S` and `S - P ≤ $1.00` | Execute at P (grace window) |
| `P < S` and `S - P > $1.00` | Execute at `S - ((S - P) / 2)` (slippage) |

> Disclosed in ToS. Users should understand limit orders are not guaranteed fills at exact prices.

---

### 6.5 Corporate Actions System

FMP is fetched daily at **9:00 AM ET**. The processor job at **9:25 AM ET** applies today's actions to all affected holdings before market open.

| Action | Policy |
|---|---|
| Cash Dividend | Credit `amount_per_share × qty` to balance. If DRIP enabled, reinvest as shares. |
| Stock Dividend | Add shares directly. DRIP toggle does not apply. |
| Special Dividend | Same as cash dividend. DRIP applies. |
| Forward Split | Multiply `qty_remaining` by ratio. Divide `cost_per_share` by ratio. |
| Reverse Split | Divide `qty_remaining` by ratio (truncate). Multiply `cost_per_share` by ratio. |
| Ticker Change | Update `ticker` in `holdings_ledger`. Add new ticker to `stocks`. Mark old inactive. History rows preserve old ticker. |
| Merger / Acquisition (stock deal) | Close position at user's **cost basis**. Credit balance. |
| Merger / Acquisition (cash deal) | Close position at **acquisition price per share**. Credit balance. |
| Spinoff | Close position at user's **cost basis**. Credit balance. |
| Bankruptcy / Delisting | Position zeroed. **No cash returned.** |

> Bankruptcy/delisting zeroing is intentional. Users should monitor positions. Disclosed in ToS.

When a corporate action affects a user's holdings, create a notification surfaced in the UI. Send Discord DM if account is linked.

---

### 6.6 DRIP — Dividend Reinvestment

DRIP automatically reinvests cash dividends as additional shares rather than crediting cash.

**Configuration:**
- Per-position toggle (`drip_enabled` on `holdings_ledger`), defaults to `false`
- "Enable DRIP for all positions" bulk button flips all current holdings — new positions always default to `false`

**DRIP execution (on dividend pay date):**
1. Calculate dividend cash = `dividend_per_share × qty_remaining`
2. Fetch current price from DB
3. DRIP shares = `dividend_cash / price` → truncate to 2dp
4. Add shares to `qty_remaining`
5. Credit any truncated remainder cash to balance
6. Insert `DRIP` transaction
7. Recalculate ACB using weighted average formula

---

### 6.7 Tax System

#### Overview
Taxes are calculated on the US calendar year (Jan 1 – Dec 31) and settled automatically on **April 15th** of the following year.

#### Federal Tax Rates (assumed $80k median income)

| Type | Rate |
|---|---|
| Short-term gains (held < 1 year) | 22% |
| Long-term gains (held ≥ 1 year) | 15% |
| Qualified dividends | 15% |

#### State Tax Rates
Flat rate approximation per state stored in `/backend/app/utils/state_tax_rates.py`. Full bracket tables are a V2 refinement. User selects state at registration (no default pre-selected).

#### Tax Year
- Tax year = January 1 – December 31
- April 15th is the payment deadline for the prior year
- Settlement job on April 15th 2026 covers Jan 1 – Dec 31 2025
- New users registered mid-year: same query, DB naturally returns fewer rows. No special casing.

```sql
-- Same query every year, every user
SELECT * FROM transactions
WHERE user_id = ?
AND type IN ('SELL', 'DIVIDEND_CASH', 'DRIP')
AND executed_at BETWEEN '{tax_year}-01-01' AND '{tax_year}-12-31';
-- tax_year = YEAR(NOW()) - 1
```

#### Loss Harvesting
1. Short-term losses offset short-term gains first
2. Long-term losses offset long-term gains first
3. Remainder from either crosses over to offset the other type
4. If total losses exceed total gains — no tax owed, excess discarded (no carry-forward)

#### Annual Settlement Job (April 15th, 10:00 AM ET)
1. Gather all SELL, DIVIDEND_CASH, DRIP rows for Jan 1 – Dec 31 prior year
2. Sum `short_term_gain` and `long_term_gain` (gains positive, losses negative)
3. Apply loss harvesting
4. Calculate federal tax on net short-term (22%) and net long-term + dividends (15%)
5. Calculate state tax: `total_net_gains × STATE_TAX_RATES[user.state]`
6. If `balance >= tax_owed` → deduct directly
7. If `balance < tax_owed` → auto-liquidate (FIFO across all tickers) until covered
8. Insert `TAX_PAYMENT` transaction
9. Notify via dashboard + Discord DM if linked

#### Running YTD Estimate
Displayed on dashboard throughout the year. Updated every time a SELL or dividend transaction is inserted. Derived directly from `transactions` table — no separate storage.

#### April Tax Warning Banner
Appears April 1st, dismissed after April 15th settlement:
```
📅 Tax settlement approaching: Your estimated 2024 tax bill is $1,314.65.
   Auto-deduction occurs April 15th. Ensure your cash balance covers this
   or positions will be auto-liquidated to cover the shortfall.
```

---

### 6.8 Monthly Stipend System

| Rule | Detail |
|---|---|
| Amount | $250 flat — all difficulty tiers |
| Schedule | Last calendar day of each month, 6:00 PM ET |
| Inactivity cutoff | Skipped if `last_active_at` > 32 days ago |
| Activity tracking | `last_active_at` updated on every authenticated request and Discord bot command |
| No catch-up | Missed stipends not retroactively paid |
| Transaction record | Type `STIPEND`, `total_value = +250.00` |

---

### 6.9 Fractional Shares

Supported to 2 decimal places (e.g. `0.12` shares).

**Truncation policy:** Always truncate (floor) to 2dp — never round up. Remainders are discarded. Disclosed in ToS.

**Where fractions arise:**

| Scenario | How |
|---|---|
| DRIP | `dividend_cash / price` → truncated |
| Reverse split | `qty / ratio` → truncated |
| Dollar-amount buy | `dollars / price` → truncated |
| Forward split | Typically whole numbers, truncation applied if not |

**DB enforcement:** All `quantity` fields use `DECIMAL(15,2)`. Hourly audit job scans `holdings_ledger` for any `qty_remaining` with >2dp; truncates and logs any found.

---

### 6.10 Flask API Endpoints

#### Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | Body: `{ email, password, display_name, state, difficulty }` |
| POST | `/api/auth/login` | Returns JWT cookies |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/google` | OAuth2 redirect |
| GET | `/api/auth/google/callback` | |
| GET | `/api/auth/microsoft` | OAuth2 redirect |
| GET | `/api/auth/microsoft/callback` | |
| POST | `/api/auth/logout` | Clears cookies |

#### User
| Method | Path | Notes |
|---|---|---|
| GET | `/api/user/me` | Profile, balance, difficulty, state |
| PUT | `/api/user/me` | `display_name` only — 403 on difficulty/balance |
| GET | `/api/user/notifications` | Corporate action notifications |
| GET | `/api/user/stipend/status` | Next stipend date and active status |

#### Stocks
| Method | Path | Notes |
|---|---|---|
| GET | `/api/stocks/{ticker}` | Quote from DB, refreshes if stale. Includes `after_hours_price`. |
| GET | `/api/stocks/search?q=` | Search by company name or ticker |

#### Portfolio
| Method | Path | Notes |
|---|---|---|
| GET | `/api/portfolio` | Holdings with ACB, P&L, DRIP status per position |
| GET | `/api/portfolio/history` | Paginated transaction history |
| POST | `/api/portfolio/drip/enable-all` | Bulk enable DRIP for all current holdings |
| PATCH | `/api/portfolio/{ticker}/drip` | Toggle DRIP. Body: `{ drip_enabled: bool }` |

#### Orders
| Method | Path | Notes |
|---|---|---|
| POST | `/api/orders` | Body: `{ ticker, direction, order_type, quantity, limit_price?, stop_price? }` |
| GET | `/api/orders` | Pending and recent orders |
| DELETE | `/api/orders/{id}` | Cancel pending order |

#### Tax
| Method | Path | Notes |
|---|---|---|
| GET | `/api/tax/estimate` | YTD breakdown: short-term, long-term, dividends, federal + state |
| GET | `/api/tax/history` | Prior year settlement records |

#### Internal (X-Internal-Key required)
| Method | Path | Notes |
|---|---|---|
| POST | `/api/internal/refresh-prices` | Trigger price refresh |
| POST | `/api/internal/process-corporate-actions` | Run today's corporate actions |
| POST | `/api/internal/check-orders` | Run hourly order check |
| POST | `/api/internal/market-open` | Full market open job |
| POST | `/api/internal/market-close` | Full market close job |
| POST | `/api/internal/pay-stipends` | Monthly stipend job |
| POST | `/api/internal/settle-taxes` | Annual tax settlement |
| POST | `/api/internal/activate-tax-banner` | April 1st banner activation |
| POST | `/api/internal/discord/link-token` | Generate Discord link token |

---

### 6.11 Scheduled Jobs

| Job | Schedule | Condition | Action |
|---|---|---|---|
| FMP Corporate Actions Fetch | 9:00 AM ET, daily | Always | Fetch next 7 days of corporate actions |
| Corporate Actions Processor | 9:25 AM ET, daily | Trading day only | Apply today's actions to all holdings |
| Market Open Price Refresh | 9:30 AM ET, Mon–Fri | Trading day only | Fetch all ticker prices; process queued overnight orders |
| Hourly Order Check | 9:30–3:30 PM ET, hourly | Trading day only | Check PENDING orders; apply slippage model |
| Market Close Price Refresh | 4:00 PM ET, Mon–Fri | Trading day only | EOD snapshot; after-hours price; expire PENDING orders |
| Fractional Share Audit | Every hour | Always | Scan holdings for qty > 2dp; truncate and log |
| Monthly Stipend | Last day of month, 6:00 PM ET | User active ≤ 32 days | Credit $250; insert STIPEND transaction |
| Market Holiday Calendar Refresh | 1st of each month | Always | Re-fetch FMP market calendar |
| Tax Warning Banner | April 1st, 12:00 AM ET | Always | Activate banner for users with outstanding liability |
| Annual Tax Settlement | April 15th, 10:00 AM ET | Always | Calculate and settle prior year taxes |

---

### 6.12 Environment Variables — Flask

```env
FLASK_ENV=production
SECRET_KEY=
DATABASE_URL=mysql+pymysql://user:pass@host/dbname
MARKETDATA_API_TOKEN=
FMP_API_KEY=
INTERNAL_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
```

---

## 7. Discord Bot

### 8.1 Communication Pattern

The bot runs on personal hardware (Raspberry Pi / home server) and communicates with the Flask API over HTTPS to the Azure public URL. It uses the `X-Internal-Key` header for all internal routes. User-specific actions require the Discord account to be linked to a platform account first.

All business logic stays in Flask. The bot is purely a client — it formats requests, sends them, and renders the responses as Discord embeds.

---

### 8.2 Account Linking Flow

1. User runs `/link` in Discord
2. Bot calls `POST /api/internal/discord/link-token` with the user's Discord ID
3. Flask generates a short-lived one-time token (15 min expiry) tied to that Discord ID
4. Bot replies with: `https://<yourapp>.azurewebsites.net/link?token=xxx`
5. User visits link and logs into their platform account on the website
6. Flask stores `discord_id` on the user record
7. All future bot commands resolve Discord ID → platform user automatically

---

### 7.3 Slash Commands

| Command | Description |
|---|---|
| `/price {ticker}` | Stock quote embed — price, bid/ask, day range, 52wk, after-hours if available |
| `/buy {ticker} {quantity} {order_type}` | Place buy order |
| `/sell {ticker} {quantity} {order_type}` | Place sell order |
| `/orders` | List pending orders |
| `/cancel {order_id}` | Cancel a pending order |
| `/portfolio` | Holdings and unrealized P&L embed |
| `/balance` | Current cash balance and difficulty tier |
| `/history` | Recent transactions |
| `/drip {ticker} {on\|off}` | Toggle DRIP for a specific position |
| `/link` | Link Discord account to platform account |

---

### 7.4 Environment Variables — Bot

```env
DISCORD_BOT_TOKEN=
FLASK_API_BASE_URL=https://<yourapp>.azurewebsites.net
INTERNAL_API_KEY=
```

---

## 8. React Frontend

### 8.1 Pages & Components

| Page | Key Components | API Calls |
|---|---|---|
| Registration | Difficulty tier selector, state dropdown, OAuth buttons | `POST /api/auth/register` |
| Login | Email/password form, OAuth buttons | `POST /api/auth/login` |
| Dashboard | Balance card, YTD tax estimate, April banner, recent activity | `GET /api/user/me`, `GET /api/tax/estimate` |
| Stock Search | Search bar, results list | `GET /api/stocks/search?q=` |
| Stock Detail | Quote card (price, bid/ask, day range, 52wk, after-hours), buy/sell order form | `GET /api/stocks/{ticker}`, `POST /api/orders` |
| Portfolio | Holdings table (ACB, current price, unrealized P&L, DRIP toggle), bulk DRIP button | `GET /api/portfolio`, `PATCH /api/portfolio/{ticker}/drip` |
| Orders | Pending orders list, cancel button | `GET /api/orders`, `DELETE /api/orders/{id}` |
| Transaction History | Paginated table with all transaction types | `GET /api/portfolio/history` |
| Tax | YTD estimate breakdown, prior year settlement history | `GET /api/tax/estimate`, `GET /api/tax/history` |
| Notifications | Corporate action alerts | `GET /api/user/notifications` |
| Discord Link | One-time token link page | Internal token resolution |

---

### 8.2 API Integration

All API calls go through a centralized Axios client that:
- Attaches JWT access token cookie automatically (httpOnly, handled by browser)
- Handles 401 responses by calling `POST /api/auth/refresh` and retrying
- On failed refresh, redirects to `/login`

```js
// src/api/client.js
import axios from 'axios';

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,  // sends httpOnly JWT cookies automatically
});

client.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401) {
      await axios.post('/api/auth/refresh', {}, { withCredentials: true });
      return client(err.config);  // retry original request
    }
    return Promise.reject(err);
  }
);

export default client;
```

---

## 9. Project Folder Structure

```
/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── holdings_ledger.py
│   │   │   ├── transaction.py
│   │   │   ├── order.py
│   │   │   └── corporate_action.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── stocks.py
│   │   │   ├── portfolio.py
│   │   │   ├── orders.py
│   │   │   ├── tax.py
│   │   │   └── internal.py
│   │   ├── services/
│   │   │   ├── trade_service.py
│   │   │   ├── order_service.py
│   │   │   ├── dividend_service.py
│   │   │   ├── corporate_action_service.py
│   │   │   ├── tax_service.py
│   │   │   └── stipend_service.py
│   │   ├── scheduler/
│   │   │   └── jobs.py
│   │   └── utils/
│   │       ├── market_hours.py
│   │       ├── slippage.py
│   │       ├── fractional.py
│   │       └── state_tax_rates.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   │       └── client.js
│   └── .env.example
└── bot/
    ├── commands/
    ├── api_client.py
    ├── .env.example
    └── requirements.txt
```

---

## 10. Terms of Service Disclosures

The following must be explicitly disclosed:

1. **Fractional share truncation:** Quantities truncated (not rounded) to 2dp. Remainders from splits, DRIP, and reverse splits are not compensated.
2. **Order slippage:** Limit and stop orders checked hourly, not in real time. Fills are not guaranteed at exact prices. Grace window + half-difference slippage model applies.
3. **Price data delay:** Prices may be delayed. Refreshed at open, close, on-demand, and hourly for pending orders — not continuously.
4. **Corporate actions:** Mergers, acquisitions, spinoffs → positions closed at cost basis. Delistings and bankruptcies → positions zeroed, no compensation.
5. **Tax approximation:** Flat-rate state approximations used. $80k median income assumed for federal brackets. Consult a real tax professional for actual advice.
6. **Auto-liquidation:** Insufficient cash on April 15th results in automatic FIFO liquidation to cover the tax bill. Emergency sales may generate additional taxable gains.
7. **Stipend forfeiture:** Stipends forfeited if inactive (no web login or Discord interaction) for 32+ days. Not retroactively paid.
8. **Simulation disclaimer:** No real money, securities, or orders. Educational and entertainment purposes only.

---

## 11. V1 Scope vs Future Features

### V1 — Must Have

- Registration with difficulty selection, state, email/password + Google/Microsoft OAuth
- Stock search and quote display with after-hours price
- All order types: market, limit, stop, stop-limit with 6-hour max and slippage model
- Portfolio view: holdings, ACB, unrealized P&L, DRIP toggle per position
- Transaction history
- Dividend processing: cash, stock, special dividends, DRIP
- Stock split processing: forward and reverse
- Ticker change handling
- Merger/acquisition/spinoff → cost basis cashout
- Delisting/bankruptcy → position zeroed
- Corporate action notifications (UI + Discord DM)
- Tax system: YTD estimate, April 15th settlement, loss harvesting, auto-liquidation
- Monthly $250 stipend with 32-day inactivity cutoff
- April 1st tax warning banner
- Discord bot with all core commands and account linking
- All scheduled jobs and market holiday awareness

### V2 — Future

- MFA/2FA via TOTP
- Watchlist with price alerts via Discord DM
- Daily P&L history snapshots and portfolio value chart
- Leaderboard grouped by difficulty tier
- Stock news feed
- Margin / loan system (requires separate design session)
- Options paper trading
- Pre-market and after-hours order execution (requires paid API tier)
- International exchange support (requires supplementary API)
- Full bracket-table state tax rates (replacing flat approximations)