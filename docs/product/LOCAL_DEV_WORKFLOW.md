# FinSight CFO — Local Dev Workflow

## Overview

FinSight CFO has two runtimes:
- **Frontend**: Vite + React + TypeScript
- **Backend**: FastAPI (Python 3)

The frontend works standalone with seed data.
The Market Watch Rates & Liquidity tab fetches from the backend when available.
Other Market Watch tabs use seed data until their backend endpoints are built.

## Frontend Setup

```powershell
cd D:\projects\finsight-cfo
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`.

### Optional: configure API base URL

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Edit `VITE_API_BASE_URL` if your backend runs on a different port.
If not set, the frontend falls back to `http://127.0.0.1:8000`.

---

## Backend Setup

```powershell
cd D:\projects\finsight-cfo\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy the environment example:

```powershell
copy .env.example .env
```

Start the dev server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Test the backend

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/market-watch/rates-liquidity"
```

Expected health response:
```json
{ "status": "ok", "service": "finsight-cfo-api" }
```

Expected rates response: typed JSON with `metadata`, `rates`, `liquidityEvents`, `sourceStatus`.

### Fixture mode

To run the backend with local seed data (no HKMA call):

```powershell
$env:MARKET_WATCH_USE_FIXTURES="true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Or set `MARKET_WATCH_USE_FIXTURES=true` in `backend/.env`.

### Compile check

```powershell
.\.venv\Scripts\python.exe -m compileall app
```

Run after changes to catch syntax errors before starting the server.

---

## Run Both

Open two terminals:

| Terminal | Command |
|----------|---------|
| 1 (backend) | `cd D:\projects\finsight-cfo\backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000` |
| 2 (frontend) | `cd D:\projects\finsight-cfo && npm run dev` |

Open `http://localhost:5173/platform/market-watch` and navigate to **Rates & Liquidity**.

---

## What Works When

| Scenario | Rates & Liquidity | Other Tabs |
|----------|-------------------|------------|
| Backend running | HKMA source-fresh rates | Seed data |
| Backend offline | Seed data (graceful fallback) | Seed data |

---

## Safety Notes

- Do **not** display "Live", "Real-time", "Verified", "Bank-grade", or "Guaranteed" in the UI.
- Use **"Source-fresh"**, **"Daily"**, **"As of [timestamp]"** for rate labels.
- HKMA data is daily/source-timestamped — not universal realtime.
- The backend currently serves only the **Rates & Liquidity** endpoint.
  - FX, Sector Benchmarks, Commodities, and Stress Signals return seed data on the frontend.
- No auth or database is configured yet.
