# FinSight CFO Deployment Guide

This guide prepares FinSight CFO for a judge demo deployment with the frontend on Vercel and the FastAPI backend on Render, Railway, or Fly.io.

> [!IMPORTANT]
> Do not commit real `.env` files or production secrets. Configure secrets only in the hosting provider dashboard or secret manager.

## A. Frontend deployment on Vercel

### Project settings

- Framework preset: `Vite`
- Install command: `npm install --legacy-peer-deps`
- Build command: `npm run build`
- Output directory: `dist`

### Required frontend environment variables

| Variable | Example | Notes |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `https://your-backend.onrender.com` | Backend origin only; do not include a trailing `/api`. |

### Frontend API base URL behavior

The frontend reads API requests from `src/lib/apiBase.ts`:

```ts
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
```

For local development, the fallback points to the local FastAPI backend. In Vercel, set `VITE_API_BASE_URL` to the deployed backend origin.

### SPA routing

This repo includes `vercel.json` for SPA fallback routing so refreshed deep links resolve to `index.html`.

## B. Backend deployment on Render, Railway, or Fly.io

### Runtime

- Runtime: Python
- App directory: `backend`
- Install command: `pip install -r requirements.txt`
- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

If the platform does not inject `$PORT`, use its equivalent port variable or configure port `8000`.

### Required backend environment variables

| Variable | Example | Notes |
| --- | --- | --- |
| `APP_MODE` | `production` | Enables production-mode checks/rate limiting behavior. |
| `ALLOW_DEMO_FALLBACK` | `false` | Keep false for production-style demos unless explicitly testing fallback paths. |
| `MARKET_WATCH_USE_FIXTURES` | `true` | Safe judge-demo default for deterministic market data. |
| `LLM_PROVIDER` | `google_ai` | Use empty value for deterministic fallback if no provider is configured. |
| `GOOGLE_API_KEY` | provider secret | Configure only in the host dashboard; never commit. |
| `GOOGLE_AI_MODEL` | `gemini-1.5-flash` | Model name used by the Google AI provider. |
| `FRONTEND_ORIGINS` | `https://your-vercel-app.vercel.app` | Comma-separated CORS allowlist. Include localhost for local dev. |

`FRONTEND_ORIGINS` supports comma-separated values:

```bash
FRONTEND_ORIGINS=http://localhost:5173,https://your-vercel-app.vercel.app
```

The legacy `CORS_ALLOW_ORIGINS` setting is still supported as a fallback when `FRONTEND_ORIGINS` is unset.

### Health and status checks

Use these endpoints after deployment:

| Endpoint | Expected result | Purpose |
| --- | --- | --- |
| `/health` | `{"status":"ok","service":"finsight-cfo-api"}` | Basic service liveness. |
| `/ready` | `{"status":"ready",...}` | Dependency readiness. |
| `/api/runtime/status` | JSON config summary without secrets | Confirms runtime mode and provider status. |

For Render health checks, use `/health` unless you want deployment readiness to fail when optional dependencies are unavailable.

## C. Judge demo validation

1. Open the Vercel app URL.
2. Use the no-friction demo entry path and explore with mock/synthetic data.
3. Verify the `Synthetic Demo Data` badge appears where expected.
4. Verify AI CFO responds on the AI CFO page.
5. Verify the Reports page loads successfully.
6. Confirm browser network calls go to `VITE_API_BASE_URL` and are not calling `localhost`.
7. Confirm the backend runtime status page does not expose secrets.

## D. Known limits

- Demo mode uses synthetic data and fixture-backed market data when configured for judge demos.
- Provider contracts may be configured or unconfigured depending on environment variables and available credentials.
- AI CFO may run in deterministic fallback mode when no LLM provider key is configured.
- FinSight CFO is a planning and demonstration tool, not formal bank underwriting or credit approval.
- Do not use synthetic demo results as regulated financial, lending, legal, accounting, or investment advice.

## Pre-merge validation commands

```bash
npm install --legacy-peer-deps
npm run lint
npm run build
cd backend
python -m pytest tests
cd ..
docker compose config
```

If compose requires env files, temporarily copy `.env.example` to `.env` and `backend/.env.example` to `backend/.env`, run `docker compose config`, then delete those temporary `.env` files immediately.
