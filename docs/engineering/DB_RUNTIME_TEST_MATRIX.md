# Database Runtime Test Matrix

This test matrix outlines the validation suites, current coverage status, and requirements for both local file-based storage and relational database modes.

## Persistence Test Matrix

| Mode | Area | Test Type | Current Coverage | Missing Coverage | Required Before Cutover | Owner / Task ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Local** | Current Demo Flow | Integration | High (Legacy tests) | None | Yes | QA Team / T-103 |
| **Local** | Data Room Upload | Integration / Manual | High (Mocked store) | None | Yes | QA Team / T-105 |
| **Local** | Sample Reset | Manual / Script | High (Utility check) | None | Yes | Dev Team / T-104 |
| **Local** | Analysis Run | Integration | High (Advisory tests) | None | Yes | Dev Team / T-107 |
| **Local** | Reports | Integration / Route | High (Route tests) | None | Yes | Dev Team / T-110 |
| **Local** | AI CFO | Integration / UI | High (Session mocks) | Multi-turn persistence | No | AI Team |
| **Local** | Market Data Fallback | Integration | High (Fixtures) | None | Yes | Dev Team |
| **Database** | Workspace CRUD | Unit / Integration / Route | High (Adapter + Route tests) | None | Yes | Backend Team / T-112 |
| **Database** | File Metadata CRUD | Unit / Integration / Route | High (Adapter + Route tests) | S3 path integration | Yes | Backend Team / T-113 |
| **Database** | Analysis Runs | Unit / Integration / Route | High (Adapter + Route tests) | None | Yes | Backend Team / T-114 |
| **Database / Local** | Audit Events | Unit / Integration / Route | High (Adapter, route, and mode tests) | None | Yes | Backend Team / T-117 |
| **Database** | Jobs | Unit / Integration | High (Status flows) | Real Celery tasks | No | Platform Team / T-109 |
| **Database / Local** | Job/Worker Plan Guardrails | Unit / Docs / Architecture | High (Plan assertion tests) | None | Yes | Platform Team / T-124 |
| **Database / Local** | Job Service Facade | Unit | High (Lifecycle & payload validations) | None | Yes | Platform Team / T-125 |
| **Database / Local** | Report Gen Job Facade | Unit / Integration | High (Success/failure workflows & byte checks) | None | Yes | Platform Team / T-126 |
| **Database / Local** | Report Worker Prototype | Unit | High (Validation, error propagation, idempotency) | None | Yes | Platform Team / T-127 |
| **Database / Local** | Job Route Contract | Route | High (Endpoint responses, filters, local fallback, sanitization) | None | Yes | Platform Team / T-128 |
| **Database / Local** | Job Retry & Progress | Unit / Route | High (Attempt limits, progress updates, validation boundaries) | None | Yes | Platform Team / T-129 |
| **Database / Local** | Report Job Trigger Route | Route | High (POST creation endpoint, byte validations, local fallback) | None | Yes | Platform Team / T-130 |
| **Database / Local** | Report Worker Harness | Unit / Guardrail | High (Tick scanning, limit checks, error summaries, setting toggles) | None | Yes | Platform Team / T-131 |
| **Database / Local** | Manual Report Worker Tick Route | Route / Guardrail | High (workspace-scoped manual tick, disabled summary, local no-DB-init, max-per-tick) | None | Yes | Platform Team / T-132 |
| **Database / Local** | Product Smoke Flow | Integration / Route | High (E2E create, upload, run, report, job, worker tick flow) | None | Yes | Platform Team / T-132 |
| **Database** | Reports | Unit / Integration / Route | High (Adapter + Route tests) | None | Yes | Backend Team / T-110 |

| **Database** | Integration Health Check | Route / Guardrail | High (Smoke + Side-effect tests) | None | Yes | Backend Team / T-116 |
| **Local / Database** | Route Contract Guardrails | Route / API | High (Method/path checks) | None | Yes | Backend Team / T-118 |
| **Database** | Migration Upgrade | DB Integration | High (Alembic `head`) | Postgres syntax check | Yes | DB Admin / T-102 |
| **Database** | Migration Downgrade | DB Integration | High (Alembic `base`) | Postgres batch drops | Yes | DB Admin / T-102 |
| **Database** | Empty DB Bootstrap | Integration | High (Startup check) | Seed script tests | Yes | Platform Team / T-106 |
| **Database** | Rollback to Local | Manual / Integration | None | Automatic fallback test | Yes | Platform Team / T-111 |

## Missing Coverage Action Plan

1. **Staging Postgres Checks**: All migrations must be run against a real PostgreSQL container in the CI pipeline (currently running on SQLite).
2. **Post-Rollback Integrity Tests**: Create an automated scenario where database mode is toggled off mid-lifecycle, verifying that the system successfully falls back to local files without dropping active states.
3. **Multi-Turn AI CFO DB Tests**: Verify that long consulting sessions are queryable by session token after DB cutover.
