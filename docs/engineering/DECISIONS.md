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
