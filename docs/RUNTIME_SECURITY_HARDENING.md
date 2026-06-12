# Runtime Security Hardening

This document outlines the runtime security and readiness guardrails implemented for the FinSight CFO platform. These measures ensure that local demonstration instances remain usable while protecting against insecure commercial deployments.

## 1. Readiness & Status Endpoints

The backend exposes three system-level monitoring endpoints:
* **`GET /health`**: A lightweight liveness probe. Returns HTTP 200 with `{"status": "ok"}` if the server is running.
* **`GET /ready`**: A readiness probe. Future database or cache connectivity checks will block readiness if critical services are unreachable.
* **`GET /api/runtime/status`**: A detailed runtime configuration status that returns safe system configuration parameters (app version, auth mode, persistence mode, report worker status) and explicit warnings if insecure configurations are detected. *No secrets or API keys are exposed via this endpoint.*

## 2. Production Configuration Guardrails

During startup (via `app/core/startup_checks.py`), the system aggressively validates its environment. When `APP_MODE` is set to `production`:
* **Auth Mode Warning**: Warns if `AUTH_MODE=local`, as the system must use real OIDC/SAML in production.
* **Persistence Warning**: Warns if `PERSISTENCE_BACKEND=local`, as all production data should be backed by a persistent database (e.g., PostgreSQL).
* **Storage Warning**: Warns if `STORAGE_BACKEND=local`, as object storage should be implemented for robust file handling.
* **Worker Warning**: Warns if `REPORT_WORKER_ENABLED=false`, since async background tasks and report generation depend on it.

## 3. Audit and Request Context Hardening

The core authentication framework (`app/core/auth.py`) implements:
* **Role Constraint Validation**: The system strictly validates `X-Role` headers against a whitelist (`admin`, `analyst`, `viewer`), raising a `400 Bad Request` if invalid.
* **Safe Logging**: Only benign claims (organization ID, user ID, role, and auth mode) are logged. Raw headers and Bearer tokens are scrubbed to prevent PII/secret leakage.
* **OIDC Roadmap**: The auth module is explicitly documented to require an identity provider integration (e.g., Keycloak or Auth0) before commercialization.

## 4. Operational Worker Foundation

We implemented a safe local scheduler runner to handle background report jobs without requiring complex daemon dependencies like Celery or Redis:
* **Script**: `backend/app/scripts/run_report_worker_once.py`
* **Purpose**: Allows executing a single worker tick manually or via system `cron`.
* **Behavior**: It securely instantiates the required repositories based on the active backend mode (`local` or `database`) and safely outputs structured logs.

## 5. Deployment Guardrails

The included `docker-compose.yml` runs safely in local development. For production usage, ensure:
* External secrets management (e.g., AWS Secrets Manager, HashiCorp Vault) is implemented.
* A reverse proxy (e.g., Traefik or NGINX with TLS) fronts all ingress.
* Network boundaries limit database access strictly to the FastAPI backend.
