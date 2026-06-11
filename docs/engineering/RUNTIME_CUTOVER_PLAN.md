# Runtime Database Cutover Plan

This document outlines the strategy, steps, and guardrails for transitioning FinSight CFO's runtime persistence from localized JSON file storage to a relational database backend.

## 1. Purpose

The transition of FinSight CFO to a database-backed persistence model must be executed incrementally to prevent regressions. This plan defines the transition phase from the local development default (`PERSISTENCE_BACKEND="local"`) to the database backend (`PERSISTENCE_BACKEND="database"`).

## 2. Current State

All database schema migrations, repository interfaces, and SQL-backed adapters have been implemented and validated.
Workspace CRUD routes in `backend/app/routes/workspaces.py` have been migrated to route through the persistence factory.
However, other backend handlers still import and invoke their legacy stores directly. The factory functions in `backend/app/persistence/factory.py` are fully functional but are not yet wired into those endpoints.

## 3. Adapter Inventory

The following persistence repository interfaces are fully implemented and available:

* **WorkspaceRepository**: Manages workspace lifecycle (creation, deletion, reading details).
  * *Local*: `LocalWorkspaceRepository` (delegates to legacy `WorkspaceStore`).
  * *Database*: `DatabaseWorkspaceRepository` (maps to `Workspace` and `Organization` ORM models).
* **FileMetadataRepository**: Manages file tracking and versions.
  * *Local*: `LocalFileMetadataRepository` (Not implemented in legacy).
  * *Database*: `DatabaseFileMetadataRepository` (maps to `WorkspaceFile` and `WorkspaceFileVersion`).
* **FinancialSnapshotRepository**: Manages financial snapshotted periods (income statements, balance sheets, cash flows).
  * *Local*: `LocalFinancialSnapshotRepository` (delegates snapshot saves/reads to `WorkspaceStore`).
  * *Database*: *To be mapped / completed during route integration.*
* **AnalysisRunRepository**: Manages execution state and outputs of CFO tools.
  * *Local*: `LocalAnalysisRunRepository` (delegates to JSON).
  * *Database*: `DatabaseAnalysisRunRepository` (maps to `AnalysisRun` and `AnalysisRunArtifact`).
* **AuditEventRepository**: Manages logical access logs and data resets.
  * *Local*: `LocalAuditEventRepository` (delegates to audits JSON).
  * *Database*: `DatabaseAuditEventRepository` (maps to `AuditEvent`).
* **JobRepository**: Tracks background tasks and execution statuses.
  * *Local*: `LocalJobRepository` (Not implemented).
  * *Database*: `DatabaseJobRepository` (maps to `Job`).
* **ReportRepository**: Stores compiled CFO reports and download metadata.
  * *Local*: `LocalReportRepository` (Not implemented).
  * *Database*: `DatabaseReportRepository` (maps to `Report`).

## 4. What Is Ready

* **ORM Schema Mapping**: SQLAlchemy declarative models representing all target tables.
* **Migrations**: Alembic migrations `0001` through `0006` matching the schema design and compatible with SQLite and PostgreSQL.
* **Repository Adapters**: Complete implementations for Workspaces, Files, Analysis Runs, Audit Events, Jobs, and Reports database persistence.
* **Factory & Helper Logic**: Factory methods to switch between local and database modes based on `PERSISTENCE_BACKEND` configurations.
* **Test Coverage**: In-memory SQLite test suites validating schema upgrades, downgrades, and repository operations.

## 5. What Is Not Ready

* **HTTP Routes / Handler Integration**: Workspace CRUD, File Metadata, and Analysis Run endpoints are integrated. Other handlers (audits, reports, jobs) are not yet wired.
* **Database Session Middleware**: FastAPI dependency injection is integrated in workspaces.
* **Data Migration Scripts**: Tools to serialize legacy localized JSON database records and insert them into the relational database.
* **Tenant Access Rules (RBAC)**: Fine-grained user-to-workspace mapping checks (deferred to a subsequent Auth/RBAC task).

## 6. Cutover Strategy

To ensure zero downtime and safe developer workflows:

1. **Retain Local Default**: `PERSISTENCE_BACKEND` environment variable remains set to `"local"` by default in local developer machines and demo runtimes.
2. **Database Mode in Controlled Runtimes**: Relational database persistence (`PERSISTENCE_BACKEND="database"`) will be introduced under a hidden/experimental flag in dev/staging deployments first.
3. **Explicit Database Session Injection**: Every route module that utilizes a database adapter must fetch the session via FastAPI's `Depends(get_db)` dependency mechanism.
4. **Avoid Global Sessions**: Database engines and sessions must never be initialized globally or upon module import. They must remain scoped to the request lifecycle.

## 7. Recommended Route/Service Integration Order

To minimize risk, route wiring will proceed in sequential, isolated PRs:

1. **Workspace Service Integration** [COMPLETED]: Wired `WorkspaceRepository` into `routes/workspaces.py` to allow reading/writing workspaces.
2. **File Metadata Service Integration** [COMPLETED]: Wired `FileMetadataRepository` into `routes/workspaces.py` file endpoints to handle document metadata registrations and file listings.
3. **Analysis Run Service Integration** [COMPLETED]: Wired `AnalysisRunRepository` into advisory analysis handlers.
4. **Reports Integration** [COMPLETED]: Wired `ReportRepository` into workspaces report endpoints to handle corporate report metadata/payload lifecycle.
5. **Runtime Integration Health Check** [COMPLETED]: Added smoke tests verifying the combined route chain (workspace -> file -> run -> report) and guarding local mode against DB engine side-effects.
6. **Audit Events Integration** [COMPLETED]: Redirect audit trail operations to `AuditEventRepository`.
7. **Jobs / Background Processing Integration**: Introduce database-backed async processing task tracking.

## 8. Feature Flag Strategy

During the transition, routes will support both backends dynamically:
```python
@router.post("/workspaces")
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db_session_optional) # None if local mode
):
    repo = get_workspace_repository(db_session=db)
    return repo.create_workspace(payload.id, payload.company_name)
```
The helper `get_db_session_optional` returns `None` when `PERSISTENCE_BACKEND="local"` and fetches a transaction session when set to `"database"`.

## 9. API Compatibility Rules

* **Zero Schema Changes**: Returned payloads from routes must match the current JSON response schemas.
* **CamelCase Mapping**: DTO model serializers must retain CamelCase naming conventions for API consumers (e.g. `workspaceId`, `createdAt`).

## 10. Data Migration Assumptions

* **Staging/Production cutover**: Legacy local JSON workspace files will be read, serialized, and bulk-inserted into the database during a scheduled maintenance window.
* **Idempotence**: Database workspace inserts must skip workspace IDs that already exist.

## 11. Rollback Strategy

If a critical issue occurs during the database cutover:
- Toggle the environment variable `PERSISTENCE_BACKEND` back to `"local"`.
- Legacy files are preserved, enabling immediate local fallback.
*See [ROLLBACK_PLAN.md](file:///D:/projects/finsight-cfo-v3/docs/engineering/ROLLBACK_PLAN.md) for full details.*

## 12. Observability and Audit Requirements

* **Log Level**: Set SQL compilation logs to `INFO` in staging environments to verify statement structures.
* **Audit Trail**: Assert that every write operation to the database triggers a corresponding record in the `audit_events` table.

## 13. Risks and Mitigations

* **Risk**: DB Connection Exhaustion.
  * *Mitigation*: Configure connection pooling in SQLAlchemy (`pool_size=20`, `max_overflow=10`) and enforce `session.close()` via FastAPI dependencies.
* **Risk**: SQLite to PostgreSQL dialect differences (e.g. JSON columns).
  * *Mitigation*: Utilize standard SQLAlchemy `JSON` types and verify dialect-agnostic behavior in migration upgrade tests.

## 14. Acceptance Criteria before Switching Production Runtime

- [ ] All 6 repository adapters are wired to HTTP routes.
- [ ] 100% of backend tests pass with `PERSISTENCE_BACKEND="database"`.
- [ ] Migration check scripts run without drift against a clean PostgreSQL container.
- [ ] Read/write performance under PostgreSQL shows sub-50ms latency.
