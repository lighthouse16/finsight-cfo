# Architecture Decision Records (ADR)

This document records key architectural and design decisions for FinSight CFO.

## ADR 1: Environment-driven Configuration Separations
- **Date**: 2026-06-11
- **Status**: Accepted
- **Context**: The application was using hard-coded CORS origins in `main.py` and had no automated configuration validation check on startup.
- **Decision**: Externalize CORS to a comma-separated env string, parse it cleanly, and implement strict startup configuration validations (preventing demo mode/fixtures in production).
- **Consequences**: Improves security posture and ensures misconfigurations block startup early in the deployment pipeline.

## ADR 2: SQLite-to-PostgreSQL Migration Path
- **Date**: 2026-06-11
- **Status**: Proposed
- **Context**: Local file storage is insufficient for production multi-worker clusters.
- **Decision**: Migrate metadata and workspace configurations to PostgreSQL, keeping local storage for developer environments only.

## ADR-001: Use repository pattern for persistence abstraction
- **Status**: Approved
- **Context**: Directly importing file-based storage helpers (like `WorkspaceStore`) prevents introducing relational database connections without wide-ranging service modifications.
- **Decision**: Introduce abstract repository classes defining core storage operations. Refactor business services to depend on these abstract base classes instead of concrete storage managers.
- **Consequences**: Decouples API handlers and services from details of the database engines, facilitating alternate storage targets (JSON files vs SQLAlchemy DB) without altering downstream code.

## ADR-002: Target PostgreSQL for commercial persistence
- **Status**: Approved
- **Context**: Scaling the application requires a robust, transactional, multi-tenant capable persistence provider supporting horizontal scaling.
- **Decision**: Standardize production deployments on PostgreSQL.
- **Consequences**: Enables transactions, rich relational modeling, JSONB fields, indexing capabilities, and high-availability setups.

## ADR-003: Preserve local persistence adapter for demo/development during transition
- **Status**: Approved
- **Context**: Restructuring developer local machines to force running local PostgreSQL databases slows onboarding and offline demonstrations.
- **Decision**: Retain the local JSON file adapter and write testing setups supporting SQLite databases. Enable selecting active storage systems via `PERSISTENCE_BACKEND` env configuration.
- **Consequences**: Retains single-click demo reliability and rapid offline onboarding while allowing full database validation checks.

## ADR-004: Use organization_id as the primary tenant boundary
- **Status**: Approved
- **Context**: Commercial deployments are inherently multi-tenant. We need a secure boundary to ensure logical tenant data isolation.
- **Decision**: Apply an `organization_id` field across all database tables holding corporate metadata. Every read/write repository method must require `org_id` context.
- **Consequences**: Simplifies tenancy rules and prevents cross-tenant data leaks.

## ADR-005: Keep file bytes in object storage eventually, while storing metadata in DB
- **Status**: Approved
- **Context**: Database relational systems are poorly suited for storing large file binaries (like uploaded CSVs or PDFs), which increases database backup size and memory consumption.
- **Decision**: Relational schemas will only store file metadata and locations (S3 path). The physical bytes will remain on disk or live in object storage (e.g. S3).
- **Consequences**: Optimizes database sizing and enables leveraging direct-upload and content-delivery cloud networks.

## ADR-006: Use SQLAlchemy 2.0 ORM plus Alembic for commercial database foundation
- **Status**: Approved
- **Context**: The database persistence layer requires clean model mapping, transactions, metadata registry, and modular migrations to deploy schema alterations cleanly on SQLite and PostgreSQL.
- **Decision**: Standardize backend ORM mapping on SQLAlchemy 2.0 declarative styles (`Mapped[]` and `mapped_column()`) and manage database migrations using Alembic.
- **Consequences**: Ensures clean, standardized, static-type-friendly Python-to-SQL mapping, structured migrations histories, and straightforward local SQLite/production PostgreSQL compatibility.
## ADR-007: Introduce persistence repository contracts before database adapter implementation
- **Status**: Approved
- **Context**: Moving workspaces and snapshot storage directly to the database without abstraction interfaces leads to massive coupling and risks breaking local offline operations.
- **Decision**: Define persistence repository contracts as Protocol classes (WorkspaceRepository, FinancialSnapshotRepository, etc.) and create a factory layer that returns Local Workspace Adapters by default.
- **Consequences**: Safely isolates the database development track from the main runtime application, ensuring that local persistence remains the default and backend services are prepared to accept new adapters without contract disruptions.

## ADR-008: Implement database adapters behind persistence factory without switching runtime defaults
- **Status**: Approved
- **Context**: The database adapter must be introduced and tested without affecting the existing default local file storage runtime behavior or API handlers.
- **Decision**: Implement `DatabaseWorkspaceRepository` implementing the `WorkspaceRepository` contract, and update the repository factory to return it only when `PERSISTENCE_BACKEND="database"` and an active SQLAlchemy `db_session` is explicitly provided.
- **Consequences**: Enables parallel testing of the database persistence layer using in-memory SQLite without changing runtime application routes, ensuring full backward compatibility and safe incremental deployment.

## ADR-009: Store file bytes outside the database and persist only file metadata/version pointers in DB
- **Status**: Approved
- **Context**: Relational databases are poorly suited for storing large file binaries (like uploaded CSVs or Excel spreadsheets), which causes substantial database inflation and slower transactional operations.
- **Decision**: Persist only logical file metadata (e.g., workspace association, status) and file version pointers (e.g., storage URI, size, SHA256 checksum) in the database. Keep physical file bytes in localized disks (for local dev) or cloud object storage (e.g., S3 in production).
- **Consequences**: Keeps the database lean, allows direct-upload capabilities, simplifies logical file histories/versioning, and separates metadata queries from binary file content reading.

## ADR-010: Keep ORM and Alembic migrations aligned before adding more DB adapters
- **Status**: Approved
- **Context**: Discrepancies between the SQLAlchemy ORM models and physical Alembic migrations can lead to runtime errors when deploying schema adjustments in staging/production environments.
- **Decision**: Perform schema drift checks and execute Alembic migrations on in-memory/temporary SQLite databases during testing to verify that schema state matches model declarations before introducing further persistence features.
- **Consequences**: Assures database upgrade/downgrade consistency, catches schema anomalies early, and maintains clean git history.

## ADR-011: Persist analysis run metadata and outputs behind repository adapters before switching runtime routes
- **Status**: Approved
- **Context**: Storing analysis runs in the database requires capturing inputs, outputs, errors, execution durations, and execution metadata. We must expose this capability behind repository interfaces to allow local JSON file storage to remain the default while enabling full database storage capabilities.
- **Decision**: Implement `DatabaseAnalysisRunRepository` matching the abstract `AnalysisRunRepository` protocol, supporting dynamic duration calculations, status updates, and JSON payloads, while wiring it through the persistence factory.
- **Consequences**: Enables database-backed analysis runs for tests and future integrations, preserves default local persistence, and prevents regressions in existing runtime routes.

## ADR-012: Persist audit events behind repository adapters before runtime database cutover
- **Status**: Approved
- **Context**: The system log audit trail must be recorded securely and queryable at both the workspace level and the organization level. Introducing a database-backed repository allows routing this trail to a relational database during commercialization while leaving the local JSON storage default active.
- **Decision**: Implement `DatabaseAuditEventRepository` implementing the `AuditEventRepository` interface protocol, allowing optional workspace association and filtering by workspace or organization. Wire it into the persistence factory and configure migrations to align schema tables.
- **Consequences**: Standardizes audit storage, facilitates organization-wide compliance logging, preserves developer-friendly local default persistence, and prevents regressions.

## ADR-013: Persist job metadata behind repository adapters before implementing background workers
- **Status**: Approved
- **Context**: The background jobs system needs to record executions, payloads, results, and error details securely across multiple tenants. To build this logic safely, we must first abstract metadata storage behind job repository adapters without triggering any async workers or changing runtime persistence configurations.
- **Decision**: Implement `DatabaseJobRepository` conforming to the abstract `JobRepository` interface protocol, supporting job creation, updates, and terminal/transition status mappings. Wire it through the persistence factory and align database schemas through migrations.
- **Consequences**: Standardizes job metadata tracking, decouples task state monitoring from worker runtimes, preserves local developer storage, and prevents regressions.

## ADR-014: Persist report metadata and payloads behind repository adapters before report generation/export cutover
- **Status**: Approved
- **Context**: The report persistence system needs to record compiled corporate report metadata and payloads securely behind database-backed repository interfaces to allow developer environments to function using local storage by default.
- **Decision**: Implement `DatabaseReportRepository` conforming to the abstract `ReportRepository` interface protocol, supporting report saving, status updates, and soft deletion. Wire it through the persistence factory and align database schemas via migrations.
- **Consequences**: Standardizes report history tracking, enables database-backed report metadata querying, preserves local JSON file storage default, and prevents regressions in existing api routes.

## ADR-015: Plan runtime database cutover before route integration
- **Status**: Approved
- **Context**: Switching the application's runtime routes to database persistence directly risks regressions, connection issues, or dialect mismatch errors in production without a solid transition strategy and verification checklist.
- **Decision**: Author a comprehensive runtime cutover plan, DB test matrix, and rollback plan to guide future incremental route-to-repository integrations.
- **Consequences**: Safeguards local-first developer defaults, establishes a clear blueprint for route refactoring, and ensures high observability and zero data loss during rollbacks.

## ADR-016: Route workspace CRUD through repository factory with local default preserved
- **Status**: Approved
- **Context**: Integrating routes with the database layer must prevent regressions in the local JSON storage developer mode while allowing database-backed repository adapters when database persistence is enabled.
- **Decision**: Refactor workspaces router handlers to use repository factory methods via FastAPI dependencies, introducing a conditional database session helper that yields None in local mode to avoid database connection pool/engine initialization side effects.
- **Consequences**: Retains backward compatibility for local development, provides a tested template for route refactoring, and ensures full SQLite test coverage for workspaces database mode.

## ADR-017: Route file metadata persistence through repository factory while keeping file bytes outside the database
- **Status**: Approved
- **Context**: Uploaded files (CSVs, Excel sheets) require both physical byte storage and logical metadata registration. Database relational engines should not store raw binary blobs, and runtime cutover of file handlers must preserve the default offline local file storage behavior.
- **Decision**: Integrate file metadata routes in `backend/app/routes/workspaces.py` with `FileMetadataRepository` factory dependencies. In database mode, file bytes are written to the local uploads directory and metadata is registered in the relational database, bypassing the local JSON metadata file. In local mode, the endpoint delegates directly to legacy `FileStore` helpers.
- **Consequences**: Avoids storing file blobs in the database, provides transaction-safe file tracking for the database persistence mode, and maintains 100% backward compatibility with local developer storage.

## ADR-018: Route analysis run persistence through repository factory while preserving local calculation behavior
- **Status**: Approved
- **Context**: Analysis runs require heavy calculation logic. We must route execution persistence through database repository factory adapters in DB mode while keeping calculation engines local.
- **Decision**: Integrate workspace analysis run routes with `AnalysisRunRepository` factory dependencies. In database mode, runs are saved to the relational database and read from it, bypassing local `runs.json` writes. A thread-safe global `_active_db_session` provides workspace/snapshot querying capabilities during local calculation engine runs in database mode.
- **Consequences**: Safely persists and retrieves analysis run metadata in the database without altering core ratio, valuation, and advisory engines, maintaining backward-compatible response schemas.

## ADR-019: Route report persistence through repository factory while preserving local storage by default
- **Status**: Approved
- **Context**: Workspace reports contain corporate financial metadata and payloads. We need to route report persistence through the repository factory in DB mode while keeping local JSON-based file storage as the default.
- **Decision**: Integrate workspace report routes with `ReportRepository` factory dependencies in `backend/app/routes/workspaces.py`. In database mode, reports are saved to and read from the relational database, bypassing local `reports.json` writes. CamelCase API compatibility and response shapes are strictly preserved.
- **Consequences**: Safely persists and retrieves workspace report metadata and payloads in the database, preserving local-first default behavior with zero DB engine/session initialization when running in local mode.

## ADR-020: Add runtime cutover health checks before further route integration
- **Status**: Approved
- **Context**: The codebase underwent multiple incremental database persistence migrations. We need to verify that all integrated routes behave stably, preserve camelCase schemas, run correctly on in-memory DB setups, and that local mode has zero database engine initialization side-effects.
- **Decision**: Implement a dedicated runtime integration health check test suite in `backend/tests/test_runtime_cutover_health.py` validating the entire workspace-file-run-report flow under local and database persistence regimes.
- **Consequences**: Ensures regression safety, detects accidental file writes or DB engine leakage in local mode, validates response structures, and establishes a solid benchmark before integrating subsequent routes.

## ADR-021: Route audit event persistence through repository factory with best-effort route audit writes
- **Status**: Approved
- **Context**: Workspace operations, file management, analysis runs, and reports produce audit event histories. In database mode, we must persist these to the relational database using the repository factory while leaving the legacy local JSON audits store unmodified in local mode.
- **Decision**: Route workspace, file, run, and report audit events through the `AuditEventRepository` interface returned by the repository factory. Guard all route-level audit logs with a database mode settings check so they only run in database mode to avoid changing local mode behavior and side-effects. Use try/except blocks to make audit writing best-effort, preventing audit failures from blocking primary route actions.
- **Consequences**: Safely integrates audit event recording for database mode, fully isolates local development mode audits, and keeps the API robust against unexpected audit logging failures.

## ADR-022: Plan service extraction boundaries for workspace runtime routes before further cutover
- **Status**: Approved
- **Context**: The `routes/workspaces.py` route module has grown excessively large by managing file system operations, calculation orchestrations, report CRUD, DB sessions, and monkeypatches. In order to keep the router clean and testable, we need a formal extraction strategy.
- **Decision**: Define six service extraction phases (Audits, Reports, Files, Analysis, Workspaces, and Jobs) and implement contract guardrails enforcing route registration paths, HTTP methods, and DB initialization isolation. Production router changes are deferred to individual, isolated PRs.
- **Consequences**: Provides a safe blueprint for incremental router cleanup while guaranteeing zero API regression, zero frontend impacts, and zero DB session leaks in local mode.

## ADR-023: Extract best-effort audit write helper into audit service
- **Status**: Approved
- **Context**: As part of the routing refactoring plan, we need to extract logic out of `routes/workspaces.py` to keep it clean. The best-effort route-level audit logging check is the first phase candidate.
- **Decision**: Define a thread-safe async function `record_audit_event_best_effort` in `backend/app/services/audit_service.py` that checks the active persistence settings and records database-mode audit rows. Synchronous helpers execute this using `asyncio` loop introspection.
- **Consequences**: Successfully isolates all route-level auditing concerns, reduces workspaces route complexity, and ensures complete compatibility with existing local/database mode integration tests.

## ADR-024: Extract report CRUD orchestration into report service
- **Status**: Approved
- **Context**: Keeping the workspaces router thin and focused requires extracting nested orchestration behaviors. Following the audit service extraction, report CRUD operations are the next extraction candidate.
- **Decision**: Extract workspace report saving, list fetching, status patching, and soft deleting logic from `routes/workspaces.py` into `backend/app/services/report_service.py`. Enforce error routing using standard HTTPException raises in the service.
- **Consequences**: Successfully decouples workspace reports CRUD logic, simplifies workspaces route handlers down to single-line service calls, and retains full local/database mode test compatibility.

## ADR-025: Extract file metadata orchestration into file metadata service
- **Status**: Approved
- **Context**: Phase 3 of the workspace route service extraction plan involves isolating file upload, list, delete, and cascade cleanup logic from the router layer into a dedicated service module.
- **Decision**: Extract file upload (both database and local mode paths), file list querying, file deletion, raw bytes retrieval, and workspace cascade deletion logic from `routes/workspaces.py` into `backend/app/services/file_metadata_service.py`. The service interacts with repositories and legacy store APIs while avoiding FastAPI-specific routers or raw DB sessions.
- **Consequences**: Successfully isolates all file-related metadata management and disk storage interactions, keeps the HTTP routing layer thin, and preserves existing persistence adapter configurations and storage behaviors.

## ADR-026: Extract analysis runtime orchestration into analysis runtime service
- **Status**: Approved
- **Context**: Phase 4 of the workspace route service extraction plan involves isolating analysis execution, run listing, run details retrieval, and latest run endpoints from the router layer into a dedicated service module.
- **Decision**: Extract analysis stage run triggers (supporting sync and async execution flow), run list querying, run details querying, and latest run (both stage-specific and generic) handlers from `routes/workspaces.py` into `backend/app/services/analysis_runtime_service.py`. The service orchestrates persistence mapping and logs audit trails in database mode without modifying financial calculations or snapshot logic.
- **Consequences**: Successfully isolates all analysis run routing logic, reduces the route layer complexity, and preserves current database-mode persistence and local-mode default behavior.

## ADR-027: Extract workspace CRUD service
- **Status**: Approved
- **Context**: Phase 5 of the workspace route service extraction plan involves isolating workspace CRUD operations (create, list, get, delete) from the workspaces router into a dedicated service.
- **Decision**: Extract workspace CRUD orchestration logic from `routes/workspaces.py` into `backend/app/services/workspace_service.py`. The service accepts repository and audit repo dependencies, validates inputs, invokes the workspace and file repository operations, and records audit events, while avoiding DB session creation.
- **Consequences**: Further simplifies the workspaces route layer, separates HTTP delivery concerns from backend business orchestration, and guarantees zero runtime or response schema deviations.

## ADR-028: Evaluate job/worker rollout before implementing async runtime execution
- **Status**: Approved
- **Context**: In Phase 6, we need to design background processing for long-running financial calculations and document processing. However, introducing full worker daemons and messaging brokers directly without a transition strategy poses regression risks to the local developer default mode and demo environments.
- **Decision**: Formulate a comprehensive evaluation plan detailing lifecycle mappings, candidate async workloads (prioritizing report generation as the safest starting point), queue architecture options (comparing FastAPI BackgroundTasks, async loops, and Celery), and rollout phases. Add a strict docs guardrail test to enforce limits and forbid async runtime code changes or queue library additions in this phase.
- **Consequences**: Outlines a clear, safe route to production concurrency without disrupting local developer environments, guaranteeing that local-first defaults remain preserved.

## ADR-029: Add job service facade contract before worker runtime implementation
- **Status**: Approved
- **Context**: In Phase A of the background processing rollout, we must stabilize job lifecycle behavior and API payloads. Introducing background runner engines before routing and payload contracts are stable risks runtime failures.
- **Decision**: Create a lightweight `job_service` module implementing `create_job`, `get_job`, `list_jobs`, `mark_job_running`, `mark_job_completed`, `mark_job_failed`, and `cancel_job`. Enforce strict status transition rules and recursive payload validation to forbid raw file bytes storage in database columns, while keeping the execution inline/sync and avoiding DB session initialization.
- **Consequences**: Standardizes the job lifecycle and data payload rules at the service layer, preparing the codebase for clean worker prototype integration in later phases.

