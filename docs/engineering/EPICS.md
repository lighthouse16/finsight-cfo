# Engineering Epics

This document tracks active and upcoming large-scale engineering initiatives (Epics).

## Epic 1: Configuration & CI Hardening
- **Goal**: Clean configuration separation and automatic linting/testing.
- **Status**: Active (Task `commercial/foundation-config-ci`)
- **Key Deliverables**:
  - Environment validation check at startup.
  - Strict linting and build checks in GitHub Actions.

## Epic DB-001: Persistence Abstraction
- **Goal**: Define repository interfaces to decouple API code from direct storage implementations.
- **Scope**: Create `WorkspaceRepository`, `FileRepository`, and `AnalysisRunRepository` abstract interfaces. Refactor existing local storage code to implement these.
- **Out of Scope**: Writing SQL database code.
- **Suggested PRs**:
  - `PR-101`: Define abstract base classes and model mappings.
- **Acceptance Criteria**: Existing unit and integration tests run successfully with zero API response modifications.

## Epic DB-002: Schema and Migrations
- **Goal**: Establish the base SQL database structures.
- **Scope**: Set up SQLAlchemy, Alembic configs, database models for all entities in `DB_SCHEMA_PROPOSAL.md`, and write the initial migration script.
- **Out of Scope**: Business logic integration.
- **Suggested PRs**:
  - `PR-102`: Add SQL dependencies, base models, and Alembic migrations.
- **Acceptance Criteria**: Migrations can be run up and down on SQLite and PostgreSQL.

## Epic DB-003: Workspace DB Adapter
- **Goal**: Connect workspaces and snapshots storage to the database.
- **Scope**: Implement `SqlWorkspaceRepository` using SQLAlchemy. Add a config-driven factory switcher.
- **Out of Scope**: File metadata and AnalysisRun tables.
- **Suggested PRs**:
  - `PR-103`: Implement Workspace DB repository and tests.
- **Acceptance Criteria**: Workspaces can be created and queried successfully from the DB when the config flag is active.

## Epic DB-004: File Metadata DB Adapter
- **Goal**: Save Data Room file records in the database.
- **Scope**: Implement `SqlFileRepository` registering file listings and version paths.
- **Out of Scope**: Physical file uploads (remain on disk / cloud storage).
- **Suggested PRs**:
  - `PR-104`: Implement File metadata DB adapter and tests.
- **Acceptance Criteria**: File listings are persisted in and queried from the DB.

## Epic DB-005: Analysis Run Persistence
- **Goal**: Save diagnostic results and blueprint records in database tables.
- **Scope**: Implement `SqlAnalysisRunRepository` to store analysis runs and run artifacts JSON payloads.
- **Out of Scope**: Reports or audit trail tables.
- **Suggested PRs**:
  - `PR-105`: Implement AnalysisRun DB adapter.
- **Acceptance Criteria**: Diagnostic calculations write to the database and can be queried.

## Epic DB-006: Audit, Job, and Report Persistence
- **Goal**: Track immutable audit trails, asynchronous job statuses, and report compilation histories.
- **Scope**: Implement DB repository adapters for AuditEvents, Jobs, and Reports tables.
- **Out of Scope**: Integrations with external queues like Celery.
- **Suggested PRs**:
  - `PR-106`: Implement Audit, Job, and Report DB adapters.
- **Acceptance Criteria**: Audit events are logged successfully; reports history is queried from database.

## Epic DB-007: Migration and Dual-Read/Dual-Write Strategy
- **Goal**: Migrate data from JSON file repositories safely without downtime.
- **Scope**: Build the backfill ingestion script. Verify double-write/sync capability if needed.
- **Out of Scope**: Production server deployment.
- **Suggested PRs**:
  - `PR-107`: Implement DB ingestion utility and verification suite.
- **Acceptance Criteria**: Ingestion scripts run correctly and verify 100% record match.
