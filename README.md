# AI-Powered Indian Stock Market Advisor

A free, self-hosted stock market advisor for NSE/BSE. Gives you **BUY / ADD MORE / HOLD / PARTIAL SELL / SELL / AVOID** signals based on technical analysis, news sentiment, and your portfolio rules.

> **You are always the final decision maker. This platform never places trades automatically.**

## What's Free — and What's Needed

| Component | Technology | Install needed? |
|---|---|---|
| Database | SQLite (file-based, built into Python) | No |
| Cache | In-memory (built into Python) | No |
| Market data | Yahoo Finance via `yfinance` | No API key |
| AI recommendations | Rule-based engine (RSI, MACD, Bollinger Bands) | No |
| Runtime | Python 3.11+ | Yes — one-time |
| Frontend build | Node.js 18+ | Yes — one-time (only needed to build UI) |
| News sentiment | VADER + optional NewsAPI (100 req/day free) | No |
| Alerts | Optional Telegram bot or Gmail | No |

> **No Docker, no PostgreSQL, no Redis required.**

---

## Quick Start (Windows)

### Step 1 — Install Python

Download and install Python 3.11+ from **https://www.python.org/downloads/**

> During install, check **"Add Python to PATH"**

Verify: open a new PowerShell window and run:
```powershell
python --version
```

### Step 2 — Install Node.js (one-time, for frontend build)

Download and install Node.js 18+ from **https://nodejs.org/**

Verify:
```powershell
node --version
```

> After the frontend is built once and committed, other machines **do not need Node.js**.

### Step 3 — Clone the repository

```powershell
git clone https://github.com/lalithvishnu04/Stock-Exchange.git
cd "Stock-Exchange"
```

### Step 4 — First-time setup (one command)

```powershell
.\setup.bat
```

This automatically:
- Creates a `.env` config file
- Creates a Python virtual environment
- Installs all Python packages
- Builds the React frontend

Takes ~3-5 minutes the first time.

### Step 5 — Run the dashboard

```powershell
.\run.bat
```

Open your browser at **http://localhost:8000**

> Every time you want to use the dashboard, just run `run.bat`. No other steps needed.

---

## First-Time Use

### Create your account
1. Go to **http://localhost:8000**
2. Click **Register** → enter username, email, password
3. Log in

### Add your Zerodha holdings
1. Go to the **Portfolio** page
2. Open your **Zerodha app** → Holdings tab
3. For each stock, click **"Add Stock"** and enter:
   - **Symbol** — e.g. `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`
   - **Exchange** — `NSE` (most stocks) or `BSE`
   - **Quantity** — number of shares you hold
   - **Avg Buy Price** — the "Avg. cost" shown in Zerodha
4. Repeat for all your stocks

> You only need to do this **once**. Prices auto-refresh from Yahoo Finance daily.

### Get AI recommendations
1. Go to **Recommendations** page
2. Click **"Analyse Now"** on any stock
3. The AI checks: RSI, MACD, Bollinger Bands, ADX, news sentiment, and your portfolio allocation rules
4. You get a signal with risk level: **LOW / MEDIUM / HIGH**

---

## Optional Extras (all free)

Edit the `.env` file in the project folder to enable these:

- **News sentiment** — Get a free key at [newsapi.org](https://newsapi.org) → set `NEWS_API_KEY=`
- **Telegram alerts** — Message `@BotFather` on Telegram → `/newbot` → set `TELEGRAM_BOT_TOKEN=` and `TELEGRAM_CHAT_ID=`
- **Email alerts** — Gmail → Security → App Passwords → set `SMTP_USERNAME=` and `SMTP_PASSWORD=`
- **GPT-4o AI** — Set `OPENAI_API_KEY=` to use OpenAI instead of the rule-based engine (paid, optional)

---

## Portfolio Rules (auto-enforced)

| Rule | Limit |
|---|---|
| Max allocation per stock | 10% of portfolio |
| Max allocation per sector | 25% of portfolio |
| Risk label | Always shown (LOW / MEDIUM / HIGH) |

If a stock exceeds 10% or a sector exceeds 25%, the AI automatically downgrades BUY → HOLD.

---

## Daily Schedule (IST)

| Time | Action |
|---|---|
| 8:00 AM | Pre-market analysis for all holdings |
| Every 30 min | Intraday check (stop-loss breach alert at -7%) |
| 4:00 PM | Post-market analysis |
| 5:00 PM | Daily report generated |
| Friday 5:00 PM | Weekly report generated |

---

## Stop and Restart

Press `Ctrl+C` in the terminal to stop.

To restart anytime:
```powershell
.\run.bat
```

Your portfolio data is stored in `backend/stock_advisor.db` (SQLite file) and persists across restarts.

---

## Project Structure

```
Stock-Exchange/
├── backend/                  # FastAPI (Python)
│   ├── app/
│   │   ├── models/           # SQLAlchemy DB models (SQLite)
│   │   ├── routers/          # API endpoints
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # AI engine, market data, scheduler
│   └── requirements.txt
├── frontend/                 # React 18 + TypeScript + MUI
│   ├── src/                  # Source files
│   └── dist/                 # Built files (served by backend)
├── setup.bat                 # First-time setup (Windows)
├── run.bat                   # Start the dashboard (Windows)
└── .env.example              # Copied to .env by setup.bat
```

---

## Troubleshooting

**`setup.bat` fails at pip install**
→ Make sure Python is in PATH. Try: `python -m pip install --upgrade pip` then run `setup.bat` again.

**Browser shows "Unable to connect"**
→ Make sure `run.bat` is still running. Check the terminal for errors.

**Stock symbol not found**
→ Use the exact NSE symbol — check at [nseindia.com](https://www.nseindia.com). For BSE stocks select `BSE` as exchange.

**Prices show 0 or N/A**
→ Click **"Refresh Prices"** on the Portfolio page. Yahoo Finance occasionally has a delay on weekends.

**Frontend not loading (blank page)**
→ The frontend was not built. Run `setup.bat` again (requires Node.js). Or open **http://localhost:8000/api/docs** to use the raw API.


A free, self-hosted stock market advisor for NSE/BSE. Gives you **BUY / ADD MORE / HOLD / PARTIAL SELL / SELL / AVOID** signals based on technical analysis, news sentiment, and your portfolio rules.

> **You are always the final decision maker. This platform never places trades automatically.**

## What's Free

| Component | How |
|---|---|
| Market data (live prices) | Yahoo Finance via `yfinance` — no API key |
| PostgreSQL database | Docker container — no install needed |
| Redis cache | Docker container — no install needed |
| AI recommendations | Rule-based engine (RSI, MACD, Bollinger Bands, ADX) |
| News sentiment | VADER + optional NewsAPI (100 req/day free tier) |
| Alerts | Optional Telegram bot (free) or Gmail (free) |

---

## Prerequisites

- **Windows 10/11** (or Linux/Mac — same steps)
- **Docker Desktop** — [download here](https://www.docker.com/products/docker-desktop/)
- **Git** — [download here](https://git-scm.com/downloads)
- That's it. No Python, Node.js, or PostgreSQL install needed.

---

## Setup Steps

### 1. Clone the repository

```powershell
git clone https://github.com/lalithvishnu04/Stock-Exchange.git
cd "Stock-Exchange"
```

### 2. Create your `.env` file

```powershell
Copy-Item .env.example .env
```

The `.env` file is pre-filled with working defaults. You can run the app immediately without changing anything.

**Optional extras (all free):**

- **News sentiment** — Get a free key at [newsapi.org](https://newsapi.org) → paste into `NEWS_API_KEY=`
- **Telegram alerts** — Message `@BotFather` on Telegram → `/newbot` → copy token → paste into `TELEGRAM_BOT_TOKEN=`. Then message `@userinfobot` → copy your chat ID → paste into `TELEGRAM_CHAT_ID=`
- **Email alerts** — Gmail → Security → 2-Step Verification → App Passwords → generate → paste into `SMTP_USERNAME=` and `SMTP_PASSWORD=`
- **GPT-4o AI** — Add your `OPENAI_API_KEY=` to use OpenAI instead of the rule-based engine (optional, paid)

### 3. Start Docker Desktop

Open Docker Desktop and wait until it shows **"Engine running"** in the bottom-left.

### 4. Build and start the platform

```powershell
docker compose up --build
```

> First run takes ~5 minutes (downloads images and installs dependencies).
> Subsequent starts take ~30 seconds.

Wait until you see this line in the logs:
```
backend  | INFO:     Application startup complete.
```

### 5. Open the dashboard

Go to **http://localhost:3000** in your browser.

---

## First-Time Use

### Create your account
1. Click **Register**
2. Enter username, email, and password
3. Log in

### Add your Zerodha holdings
1. Go to the **Portfolio** page
2. Open your **Zerodha app** → Holdings tab
3. For each stock, click **"Add Stock"** and enter:
   - **Symbol** — e.g. `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`
   - **Exchange** — `NSE` (most stocks) or `BSE`
   - **Quantity** — number of shares you hold
   - **Avg Buy Price** — the "Avg. cost" shown in Zerodha
4. Repeat for all your stocks

> You only need to do this **once**. Prices refresh automatically from Yahoo Finance every day.

### Get AI recommendations
1. Go to **Recommendations** page
2. Click **"Analyse Now"** on any stock
3. The AI checks: RSI, MACD, Bollinger Bands, ADX, news sentiment, and your portfolio allocation rules
4. You get a signal with risk level: **LOW / MEDIUM / HIGH**

### Refresh prices manually
On the Portfolio page, click **"Refresh Prices"** anytime to pull the latest prices from Yahoo Finance.

---

## Portfolio Rules (auto-enforced)

| Rule | Limit |
|---|---|
| Max allocation per stock | 10% of portfolio |
| Max allocation per sector | 25% of portfolio |
| Risk label | Always shown (LOW / MEDIUM / HIGH) |

If a stock already exceeds 10% or a sector exceeds 25%, the AI automatically downgrades BUY → HOLD.

---

## Daily Schedule (IST)

| Time | Action |
|---|---|
| 8:00 AM | Pre-market analysis for all holdings |
| Every 30 min | Intraday check (stop-loss breach alert at -7%) |
| 4:00 PM | Post-market analysis |
| 5:00 PM | Daily report generated |
| Friday 5:00 PM | Weekly report generated |

---

## Stop / Restart

```powershell
# Stop the platform
docker compose down

# Start again next time (fast, no rebuild)
docker compose up
```

Your portfolio data and reports are saved in a Docker volume and persist across restarts.

---

## Project Structure

```
Stock-Exchange/
├── backend/                  # FastAPI (Python)
│   ├── app/
│   │   ├── models/           # SQLAlchemy DB models
│   │   ├── routers/          # API endpoints
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # AI engine, market data, scheduler
│   └── requirements.txt
├── frontend/                 # React 18 + TypeScript + MUI
│   └── src/
│       ├── pages/            # Dashboard, Portfolio, Recommendations, Reports, Settings
│       ├── components/       # Reusable UI components
│       ├── api/              # Axios API client
│       └── store/            # Zustand auth state
├── nginx/                    # Reverse proxy config
├── docker-compose.yml        # Runs everything together
└── .env.example              # Copy to .env before starting
```

---

## Troubleshooting

**Docker not found**
→ Install Docker Desktop and make sure it's running before `docker compose up`.

**Port already in use**
→ Change `3000:80` to `3001:80` (frontend) or `8001:8000` (backend) in `docker-compose.yml`.

**Stock symbol not found**
→ Use the exact NSE symbol — check at [nseindia.com](https://www.nseindia.com). For BSE stocks select `BSE` as exchange.

**Prices show 0 or N/A**
→ Click **"Refresh Prices"** on the Portfolio page. Yahoo Finance occasionally has a delay on weekends.

**Forgot password**
→ Currently no password reset UI. Use a new account or connect to the database:
```powershell
docker compose exec postgres psql -U stockuser -d stock_advisor
```
