# Database Runtime Test Matrix

This test matrix outlines the validation suites, current coverage status, and requirements for both local file-based storage and relational database modes.

## Persistence Test Matrix

| Mode | Area | Test Type | Current Coverage | Missing Coverage | Required Before Cutover | Owner / Task ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Local** | Current Demo Flow | Integration | High (Legacy tests) | None | Yes | QA Team / T-103 |
| **Local** | Data Room Upload | Integration / Manual | High (Mocked store) | None | Yes | QA Team / T-105 |
| **Local** | Sample Reset | Manual / Script | High (Utility check) | None | Yes | Dev Team / T-104 |
| **Local** | Analysis Run | Integration | High (Advisory tests) | None | Yes | Dev Team / T-107 |
| **Local** | Reports | Manual | None (Stubbed) | UI download assertions | Yes | Dev Team / T-110 |
| **Local** | AI CFO | Integration / UI | High (Session mocks) | Multi-turn persistence | No | AI Team |
| **Local** | Market Data Fallback | Integration | High (Fixtures) | None | Yes | Dev Team |
| **Database** | Workspace CRUD | Unit / Integration | High (Adapter tests) | Concurrent access | Yes | Backend Team / T-104 |
| **Database** | File Metadata CRUD | Unit / Integration | High (Version checks) | S3 path integration | Yes | Backend Team / T-105 |
| **Database** | Analysis Runs | Unit / Integration | High (Artifact stores) | Payload formatting | Yes | Backend Team / T-107 |
| **Database** | Audit Events | Unit / Integration | High (Org filters) | None | Yes | Backend Team / T-108 |
| **Database** | Jobs | Unit / Integration | High (Status flows) | Real Celery tasks | No | Platform Team / T-109 |
| **Database** | Reports | Unit / Integration | High (Soft delete) | PDF export wire | Yes | Backend Team / T-110 |
| **Database** | Migration Upgrade | DB Integration | High (Alembic `head`) | Postgres syntax check | Yes | DB Admin / T-102 |
| **Database** | Migration Downgrade | DB Integration | High (Alembic `base`) | Postgres batch drops | Yes | DB Admin / T-102 |
| **Database** | Empty DB Bootstrap | Integration | High (Startup check) | Seed script tests | Yes | Platform Team / T-106 |
| **Database** | Rollback to Local | Manual / Integration | None | Automatic fallback test | Yes | Platform Team / T-111 |

## Missing Coverage Action Plan

1. **Staging Postgres Checks**: All migrations must be run against a real PostgreSQL container in the CI pipeline (currently running on SQLite).
2. **Post-Rollback Integrity Tests**: Create an automated scenario where database mode is toggled off mid-lifecycle, verifying that the system successfully falls back to local files without dropping active states.
3. **Multi-Turn AI CFO DB Tests**: Verify that long consulting sessions are queryable by session token after DB cutover.
