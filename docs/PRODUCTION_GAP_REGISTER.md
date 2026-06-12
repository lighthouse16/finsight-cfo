# Production Gap Register

This document defines the explicit gaps that must be closed to transition the current FinSight CFO system from a functional prototype to a production-grade financial intelligence platform. Each gap is tagged with its severity, affected component, and recommended remediation.

---

## Gap Register

### 1. Authentication & Authorization

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-AUTH-01 |
| **Title** | No OIDC / OAuth2 integration |
| **Severity** | **Critical** |
| **Component** | Security / RBAC |
| **Current State** | Workspace access controlled by an ID token stub. No user session management, no JWT validation, no role-based access control (RM vs. SME vs. Admin). |
| **Required State** | Integrate with an OIDC provider (e.g., Keycloak, Azure AD, Auth0) for user authentication, token validation, and role assignment. |
| **Effort Estimate** | 2–3 weeks |
| **Dependencies** | Deployment environment, OIDC provider setup |

### 2. Data Room Storage

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-DATA-01 |
| **Title** | Production object storage requires bucket configuration |
| **Severity** | **Medium** |
| **Component** | Data Room |
| **Current State** | **Code adapter exists.** Local file mode and AWS S3/MinIO compatible object storage adapters are implemented. However, production deployments still require provisioning and configuring a secure, durable cloud bucket. |
| **Required State** | Provision production S3/GCS bucket, set up Access Key / Secret credentials and configure corresponding environment variables. |
| **Effort Estimate** | 1–2 days (configuration only) |
| **Dependencies** | Cloud storage provisioning |

### 3. OCR Capability

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-DATA-02 |
| **Title** | No OCR for scanned documents |
| **Severity** | **Medium** |
| **Component** | Data Room |
| **Current State** | Only raw text extraction from CSV/XLSX/PDF is supported. Scanned image PDFs cannot be processed. |
| **Required State** | Integrate an OCR engine (Tesseract, Google Document AI, or Azure Form Recognizer) to extract text from scanned documents. |
| **Effort Estimate** | 2–3 weeks |
| **Dependencies** | GAP-DATA-01 (requires durable storage configuration) |

### 4. Database Migration Pipeline

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-DB-01 |
| **Title** | No Alembic-managed schema migrations for production Postgres |
| **Severity** | **High** |
| **Component** | Persistence |
| **Current State** | SQLite auto-creates tables via `Base.metadata.create_all`. No migration history, no rollback, no production Postgres schema management. |
| **Required State** | Alembic migrations configured for Postgres. CI pipeline runs migrations on deploy. Rollback procedure documented. |
| **Effort Estimate** | 1 week |
| **Dependencies** | Production Postgres instance |

### 5. Multi-Worker Persistence Safety

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-DB-02 |
| **Title** | JSON file persistence is unsafe in multi-worker deployments |
| **Severity** | **High** |
| **Component** | Persistence |
| **Current State** | `PERSISTENCE_BACKEND=local` reads/writes a single JSON file. Two workers writing simultaneously will corrupt data (split-brain). |
| **Required State** | Enforce `PERSISTENCE_BACKEND=database` with Postgres when `ENVIRONMENT=production`. Warn on startup if local backend is used in production mode. |
| **Effort Estimate** | 3–5 days |
| **Dependencies** | GAP-DB-01 |

### 6. Queue Production Configuration

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-QUEUE-01 |
| **Title** | Redis-compatible queue requires production hosting |
| **Severity** | **Medium** |
| **Component** | Queue / Scheduler |
| **Current State** | **Code adapter exists.** A Redis-compatible queue backend has been added (PR #56). Production environments still require a hosted Redis instance (e.g. AWS ElastiCache), queue depth monitoring, and worker scaling configuration. |
| **Required State** | Provision a managed Redis instance, set up worker logs, and wire the `QUEUE_REDIS_URL` in the deployment runbook. |
| **Effort Estimate** | 2–3 days (configuration only) |
| **Dependencies** | Redis server provisioning |

### 7. Real CDI / Alternative Data APIs

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-CDI-01 |
| **Title** | No live CDI, CCRA, MPF, or CargoX integrations |
| **Severity** | **Medium** |
| **Component** | Advisory / Credit |
| **Current State** | CDI/alternative data is represented as declarative checklist items in the hard-gate precheck. No real API calls are made. |
| **Required State** | Implement API connectors for one or more CDI/MPF platforms with proper authentication, rate limiting, and error handling. |
| **Effort Estimate** | 3–5 weeks per provider |
| **Dependencies** | Commercial agreements with data providers |

### 8. Calibrated Risk Models

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-RISK-01 |
| **Title** | Risk score is a rule-based index, not a calibrated PD model |
| **Severity** | **Medium** |
| **Component** | Advisory / Credit |
| **Current State** | Unified risk score (0–100) uses static weighted penalties. No statistical calibration against actual default data. |
| **Required State** | Develop a Probability of Default (PD) model calibrated on historical portfolio data. The current rule-based score should remain as a "readiness index" alongside the PD model. |
| **Effort Estimate** | 4–8 weeks |
| **Dependencies** | Historical loan performance data, data science resources |

### 9. Live Financial Data Feeds

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-FEED-01 |
| **Title** | No real-time market data feeds for rates, bonds, or commodities |
| **Severity** | **Low** |
| **Component** | Market Watch |
| **Current State** | HIBOR scraped from HKAB, interbank liquidity scraped from HKMA, FX from Frankfurter API. Commodities, bonds, inflation, credit ratings, and central bank rates have no provider. |
| **Required State** | Subscribe to Bloomberg/Reuters/Refinitiv feeds for all market data categories. Replace DOM scrapers with authenticated API feeds. |
| **Effort Estimate** | 4–8 weeks |
| **Dependencies** | Commercial agreements with data vendors |

### 10. LLM Provider Expansion

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-LLM-01 |
| **Title** | Production LLM approved models and keys configuration |
| **Severity** | **Low** |
| **Component** | AI CFO |
| **Current State** | **Code adapters exist.** Support for Google AI/Gemini, OpenAI, and Azure OpenAI has been implemented. Production requires provisioning api keys, confirming model selections, and establishing token quotas. |
| **Required State** | Input the approved production API keys and configure model parameters (e.g. `GOOGLE_AI_MODEL=gemini-1.5-flash`). |
| **Effort Estimate** | 1 day (configuration only) |
| **Dependencies** | LLM API provider access keys |

### 11. Structured Logging & Monitoring

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-OPS-01 |
| **Title** | Centralized tracing and log aggregation pending |
| **Severity** | **Medium** |
| **Component** | Operations |
| **Current State** | **Basic metrics and logs exist.** Structured JSON logging (with auto-masking of authorization headers and API keys) and a `/metrics` Prometheus endpoint have been added (PR #56). Full centralized log aggregation (ELK/Splunk) and distributed tracing (OpenTelemetry) are still pending. |
| **Required State** | Connect JSON logs to a logging collector, configure OpenTelemetry collectors, and build Grafana dashboards. |
| **Effort Estimate** | 1–2 weeks |
| **Dependencies** | Monitoring infrastructure (Grafana/Prometheus/Splunk) |

### 12. Rate Limiting & DoS Protection

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-OPS-02 |
| **Title** | Distributed rate limiting requires shared backend |
| **Severity** | **Medium** |
| **Component** | API Gateway |
| **Current State** | **Local middleware exists.** In-memory token-bucket rate limiting (per-IP and per-Workspace) has been implemented (PR #56). In a multi-worker production deployment, rate limits will be isolated to individual workers rather than cluster-wide. |
| **Required State** | Upgrade the rate limiter to query a shared Redis store to sync token buckets across multiple server instances. |
| **Effort Estimate** | 3–5 days |
| **Dependencies** | Redis server (shared with GAP-QUEUE-01) |

### 13. CI/CD Pipeline

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-OPS-03 |
| **Title** | No automated CI/CD for backend deployments |
| **Severity** | **Medium** |
| **Component** | Operations |
| **Current State** | Tests run manually via `pytest`. No automated build, test, or deploy pipeline. |
| **Required State** | GitHub Actions / GitLab CI pipeline that runs lint, type-check, test, build, and deploy stages on push to main. |
| **Effort Estimate** | 1 week |
| **Dependencies** | Container registry, deployment environment |

### 14. Loan Structuring — Dynamic Multi-Tranche Optimization

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-LOAN-01 |
| **Title** | Loan limits are simple EBITDA multipliers, not dynamic optimization |
| **Severity** | **Low** |
| **Component** | Advisory / Structuring |
| **Current State** | Loan limits computed as `EBITDA * base_multiplier` with debt service headroom check. No multi-tranche optimization or product-specific logic. |
| **Required State** | Connect to a live bank products database and implement multi-tranche optimization (split amount across term loan, revolver, trade finance). |
| **Effort Estimate** | 3–4 weeks |
| **Dependencies** | Bank product catalog data |

### 15. Document Index — Production Storage

| Attribute | Detail |
| :--- | :--- |
| **Gap ID** | GAP-INDEX-01 |
| **Title** | BM25 document index stores in a single JSON file |
| **Severity** | **Medium** |
| **Component** | Data Room / RAG |
| **Current State** | `document_index.json` is read/written as a flat file in `storage/`. Write contention in multi-worker deployments. |
| **Required State** | Migrate document index to PostgreSQL (or a dedicated search engine like Elasticsearch/Meilisearch) for concurrent read/write safety. |
| **Effort Estimate** | 2–3 weeks |
| **Dependencies** | GAP-DB-01 (Postgres migration) or Elasticsearch cluster |

---

## Summary

| Severity | Count | Key Gaps |
| :--- | :--- | :--- |
| **Critical** | 1 | GAP-AUTH-01 |
| **High** | 2 | GAP-DB-01, GAP-DB-02 |
| **Medium** | 9 | GAP-DATA-01, GAP-DATA-02, GAP-QUEUE-01, GAP-CDI-01, GAP-RISK-01, GAP-OPS-01, GAP-OPS-02, GAP-OPS-03, GAP-INDEX-01 |
| **Low** | 3 | GAP-FEED-01, GAP-LLM-01, GAP-LOAN-01 |

**Total gaps: 15** (5 gaps reclassified to reflect implemented adapters and code bases)
