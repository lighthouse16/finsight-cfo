# FinSight CFO Backend

FastAPI-based backend for source-fresh market data.

## Prerequisites

- Python 3.11+

## Setup

```powershell
cd D:\projects\finsight-cfo\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Environment

Copy the example file:

```powershell
copy .env.example .env
```

Key settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HKMA_BASE_URL` | `https://api.hkma.gov.hk/public` | HKMA public API endpoint |
| `MARKET_WATCH_USE_FIXTURES` | `false` | Use local fixture data instead of upstream |
| `HTTP_TIMEOUT_SECONDS` | `10` | HTTP client timeout for upstream requests |
| `RATES_TTL_SECONDS` | `21600` | Cache TTL for rates response |
| `LIQUIDITY_TTL_SECONDS` | `21600` | Cache TTL for liquidity response |

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## Fixture Mode

To run without making upstream HKMA calls, set the environment variable before starting:

```powershell
$env:MARKET_WATCH_USE_FIXTURES="true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Alternatively, set `MARKET_WATCH_USE_FIXTURES=true` in `backend/.env`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/market-watch/rates-liquidity` | Rates & liquidity data |
| GET | `/api/market-watch/fx-gba` | FX & GBA data (fixture-backed, provider pending) |
| GET | `/api/market-watch/sector-benchmarks` | Sector Benchmarks data (fixture-backed, production provider pending) |
| GET | `/api/market-watch/commodities` | Commodities data (fixture-backed, production provider pending) |
| GET | `/api/market-watch/stress-signals` | Stress Signals data (fixture-backed, production engine pending) |




### Test

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/market-watch/rates-liquidity"
```

Expected health response:
```json
{ "status": "ok", "service": "finsight-cfo-api" }
```

## Compile Check

Run after making changes to catch syntax errors:

```powershell
.\.venv\Scripts\python.exe -m compileall app
```

## Run Tests

Run pytest to verify backend endpoints:

```powershell
.\.venv\Scripts\python.exe -m pytest
```
