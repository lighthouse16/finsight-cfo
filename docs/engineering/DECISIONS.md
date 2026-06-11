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
