# FinSight CFO — Deployment Runtime

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Docker Host                       │
│                                                      │
│   ┌──────────────┐    ┌─────────────────────────┐   │
│   │   Frontend    │    │     Backend (FastAPI)    │   │
│   │  (nginx:80)   │◄──►│     (uvicorn:8000)      │   │
│   │               │    │                         │   │
│   │  ┌─────────┐  │    │  ┌───────────────────┐  │   │
│   │  │ Static  │  │    │  │  Routes + Services │  │   │
│   │  │ Assets  │  │    │  └───────────────────┘  │   │
│   │  └─────────┘  │    │                         │   │
│   └──────┬───────-┘    └──────────┬──────────────┘   │
│          │                       │                   │
│          │  Host :8080          │ Host :8000         │
│          └──────────────┬───────┘                    │
│                     User                              │
└─────────────────────────────────────────────────────┘
```

### Key Points

- **Frontend** is served by **nginx** and contains only compiled static assets.
- nginx **reverse-proxies** all `/api/*` requests to the backend service.
- The frontend and API appear on the **same origin** (port 8080), avoiding CORS issues.
- No Node.js runtime is needed in production — just nginx + Python.
- A PostgreSQL service is ready but **commented out** — activate it when the app gains database support.

## Services

| Service   | Container Name          | Internal Port | Host Port | Base Image          |
|-----------|-------------------------|---------------|-----------|---------------------|
| Frontend  | `finsight-cfo-frontend` | 80            | 8080      | nginx:alpine        |
| Backend   | `finsight-cfo-backend`  | 8000          | 8000      | python:3.11-slim    |
| Postgres* | `finsight-cfo-postgres` | 5432          | 5432      | postgres:16-alpine  |

\* Postgres is commented out in `docker-compose.yml`. Uncomment when database support is added.

## Prerequisites

- **Docker** ≥ 24.x
- **Docker Compose** ≥ 2.x (V2 is integrated into Docker Desktop; V1 users run `docker-compose`)

Verify:

```powershell
docker --version
docker compose version
```

## Quick Start

### 1. Clone and enter the repository

```powershell
cd D:\projects\finsight-cfo
```

### 2. Configure environment

```powershell
# Copy backend env example (edit as needed)
copy backend\.env.example backend\.env
```

The default `backend/.env` uses **fixture mode** (`MARKET_WATCH_USE_FIXTURES=true`), so the backend works without any external API keys.

No frontend `.env` is required — the nginx reverse proxy handles API routing automatically.

### 3. Start all services

```powershell
docker compose up -d
```

This starts the backend and frontend services.

### 4. Open the app

Navigate to **http://localhost:8080**

### 5. Check status

```powershell
docker compose ps
```

Expected output (Postgres omitted):

```
NAME                    IMAGE                          STATUS          PORTS
finsight-cfo-backend    finsight-cfo-backend:latest    Up             0.0.0.0:8000->8000/tcp
finsight-cfo-frontend   finsight-cfo-frontend:latest   Up             0.0.0.0:8080->80/tcp
```

## Configuration

### Backend Environment

All backend configuration is in `backend/.env`. Key variables:

| Variable                      | Default                  | Description                                    |
|-------------------------------|--------------------------|------------------------------------------------|
| `MARKET_WATCH_USE_FIXTURES`   | `true`                   | Use local fixture data (no upstream API calls)  |
| `HKMA_BASE_URL`               | `https://api.hkma.gov.hk/public` | HKMA public API base URL               |
| `FX_PROVIDER`                 | `frankfurter`            | FX rate provider (`frankfurter` or other)      |
| `ALPHA_VANTAGE_API_KEY`       | _(empty)_                | API key for Alpha Vantage commodity data       |
| `HTTP_TIMEOUT_SECONDS`        | `10`                     | Timeout for upstream HTTP requests             |
| `RATES_TTL_SECONDS`           | `21600`                  | Cache TTL for rates (6 hours)                  |
| `LIQUIDITY_TTL_SECONDS`       | `21600`                  | Cache TTL for liquidity (6 hours)              |

### Frontend Environment (Build-Time)

The frontend is built with Vite. In Docker mode:
- `VITE_API_BASE_URL` is left **empty** (default: empty string)
- The frontend sends API requests to the same origin (e.g., `http://localhost:8080/api/...`)
- nginx proxies `/api/` to `http://backend:8000`

To override the API base URL at Docker build time:

```powershell
docker compose build --build-arg VITE_API_BASE_URL=http://custom-backend:8000 frontend
```

## Health Validation

### Docker Health Checks

The backend container has a built-in **healthcheck** that polls `GET /health` every 15 seconds.

```powershell
# Check overall stack health
docker compose ps

# Check backend health directly
docker compose exec backend python -c "import http.client; c=http.client.HTTPConnection('127.0.0.1',8000); c.request('GET','/health'); print(c.getresponse().read().decode())"
```

Expected health response:

```json
{"status":"ok","service":"finsight-cfo-api"}
```

### Frontend sanity check

```powershell
# Verify the frontend is serving
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# Expected: 200

# Verify SPA fallback works (non-file routes return index.html)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/platform/market-watch
# Expected: 200

# Verify API proxy works via the nginx route
curl -s http://localhost:8080/api/market-watch/rates-liquidity | python -c "import sys,json; d=json.load(sys.stdin); print('OK - rates count:', len(d.get('rates',[])))"
```

### Health and Status Endpoints (Backend)

The backend exposes endpoints to verify readiness and runtime configuration safely:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
Invoke-RestMethod -Uri "http://localhost:8080/api/health"   # via nginx proxy

Invoke-RestMethod -Uri "http://localhost:8080/api/ready"

Invoke-RestMethod -Uri "http://localhost:8080/api/runtime/status"
```
The `/api/runtime/status` endpoint provides the app version, persistence/auth modes, and operational warnings if insecure defaults are used in production mode (e.g. local file persistence).

## Common Commands

| Action                          | Command                          |
|---------------------------------|----------------------------------|
| Start all services              | `docker compose up -d`           |
| Stop all services               | `docker compose down`            |
| Stop and remove volumes         | `docker compose down -v`         |
| Rebuild a single service        | `docker compose build backend`   |
| Rebuild all services            | `docker compose build`           |
| View logs (follow)              | `docker compose logs -f`         |
| View logs for a service         | `docker compose logs -f backend` |
| Enter a running container       | `docker compose exec backend sh` |
| Restart a service               | `docker compose restart backend` |
| Run report worker (single tick) | `docker compose exec backend python -m app.scripts.run_report_worker_once` |

## Local Development vs. Docker

| Aspect              | Local Dev                          | Docker (Production-Like)                   |
|---------------------|------------------------------------|--------------------------------------------|
| Frontend            | `npm run dev` (:5173)              | nginx serves built assets (:8080)          |
| Backend             | uvicorn --reload (:8000)           | uvicorn (no reload) (:8000)                |
| API Base URL        | `VITE_API_BASE_URL=http://127.0.0.1:8000` | Same origin via nginx proxy         |
| CORS                | Enabled in FastAPI middleware       | Not needed (same origin)                   |
| Hot Reload          | Yes                                | No — rebuild container to update           |
| Persistence         | No database currently              | Postgres volume available (commented out)  |

## Adding Database Support

When the backend gains database support:

1. **Uncomment the `postgres` service** in `docker-compose.yml`.
2. **Uncomment the `depends_on` section** in the `backend` service.
3. **Add a database URL** to `backend/.env`:
   ```
   DATABASE_URL=postgresql://finsight:finsight_local_dev@postgres:5432/finsight_cfo
   ```
4. **Add Alembic or SQLAlchemy** dependencies to `backend/requirements.txt`.
5. **Recreate** the stack:
   ```powershell
   docker compose down
   docker compose up -d
   ```

## Troubleshooting

### Container exits immediately

Check logs:

```powershell
docker compose logs backend
```

Common causes:
- Missing `.env` file in `backend/`
- Python import error (check `backend/app/` structure)
- Port conflict on host port 8000 or 8080

### Backend fails to start

```powershell
docker compose run --rm backend python -c "from app.main import app; print('Import OK')"
```

### Frontend shows blank page or 502

1. Verify backend is running: `docker compose ps`
2. Check nginx logs: `docker compose logs frontend`
3. Verify API calls work: `curl -s http://localhost:8080/api/health`

### Port conflicts

Change host ports in `docker-compose.yml`:

```yaml
ports:
  - "8081:80"    # frontend → http://localhost:8081
```

```yaml
ports:
  - "8001:8000"  # backend → http://localhost:8001
```

## Production Considerations

> [!WARNING]
> The current setup is designed for **local production-like testing** and **internal environments**. It is **not hardened for public internet deployment** without additional measures.

For production deployment, consider:

1. **Secrets management**: Use Docker secrets or a vault instead of `.env` files.
2. **Health checks**: The backend healthcheck is basic — extend for DB connectivity checks when the database is active.
3. **Resource limits**: Add Docker resource constraints:
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           cpus: '0.5'
           memory: 512M
   ```
4. **TLS termination**: Place a reverse proxy (Traefik, Caddy, nginx) in front with Let's Encrypt.
5. **Database auth**: Change `POSTGRES_PASSWORD` to a strong password when enabling Postgres.
6. **Image tags**: Pin base image versions (already pinned to `<image>:<major>`) for reproducibility.
7. **Health check aggregation**: Monitor all services via a watchdog or Docker health events.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service orchestration |
| `Dockerfile` | Frontend build + nginx serve |
| `backend/Dockerfile` | Backend Python runtime |
| `nginx.conf` | nginx configuration for SPA + API proxy |
| `.dockerignore` | Build context exclusions |
| `.env.example` | Frontend env template |
| `backend/.env.example` | Backend env template |
| `docs/DEPLOYMENT_RUNTIME.md` | This file |
