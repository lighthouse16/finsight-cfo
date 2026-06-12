# Real Integration Status

This document establishes the definitive production truth-lock layer for the FinSight CFO platform. Every external interface is catalogued below with its integration status, provider configuration, and whether it is **real** (connected to a live external service), **mock** (uses embedded fixtures/simulations), or **deferred** (not yet implemented).

---

## Integration Status Table

| Component | Interface / Provider | Real / Mock / Deferred | Configuration | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **AI CFO — LLM Provider** | `openai` | Real | `LLM_PROVIDER=openai`, `OPENAI_API_KEY` | Live OpenAI GPT completion. Falls back to deterministic templates on API error. |
| **AI CFO — LLM Provider** | `azure_openai` | Real | `LLM_PROVIDER=azure_openai`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` | Live Azure OpenAI completion. Falls back to deterministic templates on API error. |
| **AI CFO — No LLM** | `deterministic_fallback` | Mock | `LLM_PROVIDER` unset or unrecognized | Keyword-templated response. Clearly marks `aiMode = deterministic_fallback`. No external dependency. |
| **AI CFO — RAG Index** | BM25 keyword index | Real | `storage/document_index.json` | On-disk BM25 index with workspace isolation. Built from uploaded documents. |
| **AI CFO — Safety Gate** | System prompt injection | Real | Hardcoded in `ai_provider.py` | Rejects credit underwriting, loan approvals, or guaranteed funding in all modes. |
| **Market Watch — HIBOR** | HKAB web scraper | Real | `HKAB_BASE_URL` (defaults to `https://www.hkab.org.hk`) | Live DOM scraping of HKAB HIBOR rates page. May break on schema changes. |
| **Market Watch — Interbank Liquidity** | HKMA web scraper | Real | `HKMA_BASE_URL` (defaults to `https://www.hkma.gov.hk`) | Live DOM scraping of HKMA balance sheet data. May break on schema changes. |
| **Market Watch — FX Rates** | Frankfurter API | Real | `FRANKFURTER_BASE_URL` (defaults to `https://api.frankfurter.app`) | Live REST API for EUR-based FX conversion rates. |
| **Market Watch — Commodities** | — | Deferred | None | No provider implemented. Adapter contract exists in provider interfaces. |
| **Market Watch — Bond Yields** | — | Deferred | None | No provider implemented. Adapter contract exists in provider interfaces. |
| **Market Watch — Inflation** | — | Deferred | None | No provider implemented. Adapter contract exists in provider interfaces. |
| **Market Watch — Credit Ratings** | — | Deferred | None | No provider implemented. Adapter contract exists in provider interfaces. |
| **Market Watch — Central Bank Rates** | — | Deferred | None | No provider implemented. Adapter contract exists in provider interfaces. |
| **Persistence — Workspace** | `local` (JSON file) | Mock | `PERSISTENCE_BACKEND=local` | Stores workspace data in `storage/workspaces.json`. Suitable for single-user dev, not for multi-worker production. |
| **Persistence — Workspace** | `database` (SQLite/Postgres) | Real | `PERSISTENCE_BACKEND=database`, `DATABASE_URL` | SQLAlchemy-based persistence. In dev mode uses SQLite; production targets Postgres. |
| **Persistence — Document Index** | Local JSON file | Mock | `storage/document_index.json` | Single-file JSON persistence. Subject to write contention in multi-worker deployments. |
| **Queue / Scheduler** | `in_process` | Mock | `QUEUE_BACKEND=in_process` | Synchronous in-process job execution. No durability, no retry, no visibility. |
| **Queue / Scheduler** | `redis` | Real | `QUEUE_BACKEND=redis`, `REDIS_URL` | Redis-backed queue for async job execution. Provides persistence and retry semantics. |
| **Queue / Scheduler** | `celery` | Real | `QUEUE_BACKEND=celery`, `CELERY_BROKER_URL` | Worker-based queue with full async task management. |
| **Data Room — File Upload** | In-memory | Mock | N/A | Uploaded files stored in memory only. Lost on process restart. No S3/Blob storage. |
| **Data Room — OCR** | — | Deferred | None | No OCR provider configured. File preview relies on raw text extraction. |
| **Report Generation — PDF** | WeasyPrint | Real | System-installed WeasyPrint | Server-side HTML-to-PDF rendering. |
| **Authentication** | Workspace ID stub | Mock | N/A | No OAuth2/OIDC integration. Workspace access controlled by ID token only. |
| **CDI / Alternative Data** | — | Deferred | None | No live API integrations for CDI, CCRA, MPF, or CargoX. |
| **Financial Data — Live Feeds** | — | Deferred | None | No real-time ticker or market data feed. All calculations use uploaded snapshots. |

---

## Provider Configuration Truth Table

The following table defines exactly how the system behaves based on environment configuration:

| `LLM_PROVIDER` | `OPENAI_API_KEY` | `AZURE_OPENAI_API_KEY` | Result | `aiMode` |
| :--- | :--- | :--- | :--- | :--- |
| *unset / invalid* | — | — | Deterministic template fallback | `deterministic_fallback` |
| `openai` | *set* | — | Live OpenAI completion | `openai` |
| `openai` | *unset* | — | Returns error with deterministic fallback | `deterministic_fallback` |
| `azure_openai` | — | *set* | Live Azure OpenAI completion | `azure_openai` |
| `azure_openai` | — | *unset* | Returns error with deterministic fallback | `deterministic_fallback` |

| `PERSISTENCE_BACKEND` | `DATABASE_URL` | Result | Notes |
| :--- | :--- | :--- | :--- |
| `local` | — | JSON file storage | Dev-only; split-brain risk in multi-worker |
| `database` | *set* | SQLAlchemy (SQLite/Postgres) | Production-ready with RDS |
| `database` | *unset* | Falls back to SQLite `./storage/app.db` | Dev convenience |

| `QUEUE_BACKEND` | `REDIS_URL` / `CELERY_BROKER_URL` | Result | Notes |
| :--- | :--- | :--- | :--- |
| `in_process` | — | Synchronous execution | Dev-only; no durability |
| `redis` | *set* | Redis-backed jobs | Requires Redis server |
| `celery` | *set* | Celery worker pool | Requires broker (Redis/RabbitMQ) |

---

## Deterministic Fallback Behavior

When an external provider is not configured or fails at runtime, the system **must**:

1. **Detect** the absence or failure deterministically (no silent fallback to hardcoded keys).
2. **Log** a clear warning indicating which provider is unavailable.
3. **Return** a deterministic response marked with the appropriate `aiMode` / fallback indicator.
4. **Never** fabricate data, hallucinate credit decisions, or pretend a provider is available when it is not.

This behavior is enforced in:
- [ai_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/ai_provider.py) — LLM provider detection and fallback
- [config.py](file:///D:/projects/finsight-cfo/backend/app/core/config.py) — `is_llm_configured`, `normalized_persistence_backend`, `normalized_queue_backend`
- [factory.py](file:///D:/projects/finsight-cfo/backend/app/persistence/factory.py) — Persistence backend routing
