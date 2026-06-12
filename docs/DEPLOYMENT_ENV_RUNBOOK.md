# Deployment Environment Runbook

This runbook guides administrators and engineers on configuring, running, and deploying the FinSight CFO platform across different environments (local development, staging, and production).

---

## 1. Environment Configurations

### Local Development Configuration

For local development, the system is designed to run out of the box with zero external infrastructure dependencies. Key settings are tuned for local storage and mock validation:

```env
# Mode and general settings
APP_MODE=development
ALLOW_DEMO_FALLBACK=true
MARKET_WATCH_USE_FIXTURES=true
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Persistence and storage
PERSISTENCE_BACKEND=local
OBJECT_STORAGE_BACKEND=local_file

# Queue backend
QUEUE_BACKEND=in_process
```

* Persistence operates on flat files (`storage/workspaces.json`, etc.).
* File uploads are saved directly to the local directory `storage/uploads/`.
* Queue runs synchronously in-process (no background queue required).

---

## 2. External Provider Integration Configurations

For production or staging environments, the mock modes must be disabled (`ALLOW_DEMO_FALLBACK=false`, `MARKET_WATCH_USE_FIXTURES=false`), and real infrastructure/APIs must be configured.

### Google AI / Gemini Configuration

To enable the live AI CFO advisory feature, configure the Google AI provider:

```env
LLM_PROVIDER=google_ai
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_AI_MODEL=gemini-1.5-flash
# Optional: GOOGLE_AI_BASE_URL=
```

* **Production Requirement**: A valid, non-empty `GOOGLE_API_KEY` is required.
* **Safe Fallback**: If the key is missing or calls fail due to network/auth issues, the system logs a warning and degrades gracefully to `deterministic_fallback` mode (using predefined template responses).

### Redis Queue Configuration

For asynchronous task and report execution in production, connect to a Redis instance:

```env
QUEUE_BACKEND=redis
QUEUE_REDIS_URL=redis://localhost:6379/0
```

* **Operational Note**: Ensure the Redis server is reachable.
* **Safe Fallback**: If `QUEUE_BACKEND=redis` is set but the Redis service is unreachable or fails to connect, the worker system logs a warning and falls back to synchronous `in_process` execution to guarantee operational continuity.

### S3 / MinIO Object Storage Configuration

Durable storage for uploaded financial documents (PDFs, CSVs, Excel sheets) can be backed by AWS S3 or a MinIO-compatible store:

```env
OBJECT_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://minio.yourdomain.com  # Optional: omit if using AWS S3
S3_BUCKET=your-finsight-bucket-name
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
S3_REGION=us-east-1
S3_FORCE_PATH_STYLE=true
```

* **Safe Fallback**: If `s3` is enabled but the `S3_BUCKET` is not set or authentication fails, the storage system logs a warning, returns a status of `provider_not_configured`, and stores the files in the local disk directory as a secondary fallback.

### Database / Postgres / TimescaleDB Configuration

Production persistence utilizes PostgreSQL (with TimescaleDB support) via SQLAlchemy:

```env
PERSISTENCE_BACKEND=database
DATABASE_URL=postgresql://db_user:db_password@db_host:5432/db_name
TIMESCALE_DATABASE_URL=postgresql://db_user:db_password@db_host:5432/db_name  # Optional: defaults to DATABASE_URL
```

* **TimescaleDB Support**: The database engine automatically connects and verifies if the TimescaleDB extension is enabled.
* **Safe Fallback**: If `PERSISTENCE_BACKEND=database` is requested but `DATABASE_URL` is unset, the system falls back to a local SQLite database at `./storage_db/finsight_dev.db` for convenience.
* **Schema Migrations**: Schema creation and upgrades are handled via Alembic. Running `alembic upgrade head` is required during deployment.

### OIDC / OAuth2 Identity Provider Configuration

To enable enterprise-grade single-sign-on (SSO) and role-based access control (RBAC), configure the OIDC provider settings:

```env
AUTH_MODE=oidc
OIDC_ISSUER_URL=https://your-identity-provider.com/realms/your-realm
OIDC_CLIENT_ID=finsight-cfo-app
OIDC_AUDIENCE=finsight-cfo-api          # Optional: defaults to OIDC_CLIENT_ID
OIDC_JWKS_URL=https://your-identity-provider.com/realms/your-realm/protocol/openid-connect/certs  # Optional: resolved via Discovery if empty
```

* **Token Signature Check**: Incoming bearer tokens are verified against the OIDC provider's public keys fetched dynamically from the `OIDC_JWKS_URL` (and cached in-memory with a 24-hour TTL).
* **Claims Resolution**: Claims are parsed to construct the request context:
  * `sub` claim is mapped to `user_id`.
  * `org`/`tenant`/`organization` claims are mapped to `organization_id`.
  * `role`/`roles`/`groups` claims (including Keycloak resource-access client roles) are mapped to `role` (`admin`, `analyst`, or `viewer`).
  * If configuration is missing or token verification fails, the system blocks the request with a `401 Unauthorized` response.

---

## 3. Rate Limiting Behavior

The token-bucket rate limiting middleware is **only active in production mode** (`APP_MODE=production`). In development and testing modes, requests are bypassed to facilitate automated flows and test coverage.

### Rate Limit Variables

Limits are enforced concurrently across two scopes (IP bucket and Workspace bucket):

```env
# Rate limit per IP address
RATE_LIMIT_IP_RATE=10.0
RATE_LIMIT_IP_BURST=20.0

# Rate limit per Workspace ID (from X-Workspace-ID header)
RATE_LIMIT_WS_RATE=50.0
RATE_LIMIT_WS_BURST=100.0
```

* **IP Bucket**: Refills at `RATE_LIMIT_IP_RATE` tokens per second up to `RATE_LIMIT_IP_BURST`. Every request from an IP consumes 1 token.
* **Workspace Bucket**: Refills at `RATE_LIMIT_WS_RATE` tokens per second up to `RATE_LIMIT_WS_BURST`. Every request carrying that workspace ID consumes 1 token.
* **Exceeded Limits**: When a bucket is exhausted, the server returns a `429 Too Many Requests` status code with the following structures:
  * IP limited: `{"detail": "Too Many Requests", "code": "RATE_LIMITED_IP"}`
  * Workspace limited: `{"detail": "Too Many Requests", "code": "RATE_LIMITED_WS"}`

---

## 4. Metrics, Logging and Environment Validation

The system is equipped with standard telemetry and admin endpoints for health checking and production verification.

### Production Environment Validation Endpoint

Administrators can trigger a deep, live validation of the production ecosystem using the following endpoint (restricted to `admin` role):

```http
GET /api/admin/validate-production-env
```

This runs a suite of live smoke tests and returns validation status for:
1. **Postgres / TimescaleDB**: Connection ping and checks if the `timescaledb` extension is active.
2. **Redis**: Connects, pings, writes a temporary key, reads it back, and deletes it.
3. **Object Storage**: Performs a live S3 upload/download/delete cycle of a dummy text file to verify S3 bucket read/write permissions.
4. **OIDC Provider**: Verifies discovery or JWKS connectivity and retrieves active keys.

If a component is unconfigured, the endpoint returns a status of `"provider_not_configured"`.

### Prometheus Metrics Endpoint

An OpenMetrics compatible endpoint is exposed at:

```http
GET /metrics
```

This endpoint returns raw metrics in Prometheus format:

* `finsight_http_requests_total`: A Counter tracks total HTTP requests, labeled by `status_code`, `method`, and `path`.
* `finsight_active_tasks`: A Gauge tracks the number of currently active, in-flight tasks.
* `finsight_request_duration_seconds`: A Histogram measures the duration of HTTP requests across standard bucket latencies.
* `finsight_queue_depth`: A Gauge tracks current pending tasks in the execution queue.

### Structured Logging and Credential Masking

Logs are formatted as single-line JSON records written to standard output (`stdout`/`stderr`), making them easily digestible by aggregators (Fluentd, Logstash, Loki).

* **Credential Masking**: The JSON log formatter (`SanitizingJSONFormatter`) scans message strings and automatically redacts sensitive data matches (e.g. `Authorization: Bearer ****`, `api_key=****`, `x-api-key: ****`).

---

## 5. GitHub Actions Continuous Deployment Workflow

The codebase includes an automated delivery pipeline at `.github/workflows/deploy.yml` which triggers on pushes to the `commercial/**` and `main` branches.

### Pipeline Stages
1. **Build & Test**: Builds Docker containers, lints frontend code, and runs the pytest suite on the backend.
2. **Database Migration**: Executes `alembic upgrade head` using database credentials provided in GitHub secrets.
3. **Infrastructure Deploy (Dry-Run / Production)**: Simulates the deployment steps. If SSH secrets (`DEPLOY_HOST`, `DEPLOY_KEY`) are provided in repository secrets, executes a remote update to deploy the production containers.

---

## 6. What Remains Deferred (Not Real)

The following components currently operate in mock or stub mode because live commercial integrations do not yet exist:

1. **CDI / Alternative Data**: Live connectors for CDI, CCRA, MPF, or CargoX do not exist. Ingestion and consent flows rely on stubs and prechecks.
2. **Calibrated PD Models**: The Probability of Default (PD) score is a rule-based index computed locally. It has not been statistically calibrated against historical bank portfolio default data.
3. **Paid Market Feeds**: Market Watch scrapes HIBOR from the HKAB public rates page, interbank liquidity from the HKMA public page, and FX from Frankfurter API. Real-time ticker feeds, commodities, bonds, inflation, and central bank rates do not have live commercial feeds.
4. **Production Document Index Storage**: The BM25 keyword search index for AI CFO RAG reads and writes a single on-disk flat JSON file (`storage/document_index.json`). In a multi-worker production deployment, this must be migrated to a dedicated database or search service.
