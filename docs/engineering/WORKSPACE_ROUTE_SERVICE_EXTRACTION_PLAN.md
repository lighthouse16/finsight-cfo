# Workspace Route Service Extraction Plan

This document outlines the focused architecture plan for extracting oversized runtime orchestrations and persistence routing from `backend/app/routes/workspaces.py` into dedicated service modules in future PRs.

## 1. Current Problem Statement

The `backend/app/routes/workspaces.py` file has accumulated significant responsibilities over multiple database cutover iterations. It currently contains:
* FastAPI route handlers.
* Persistence routing through the repository factory.
* Optional database session dependency providers.
* Storage safety wrappers and monkeypatches (`WorkspaceStore` overrides).
* Best-effort audit logging calls.
* File metadata tracking and file system interactions.
* Calculations analysis orchestrations and results saving.
* Report creation, updates, listing, and soft-deletes.

**Risk**: The route module is becoming large and complex, which makes it harder to review, test, maintain, and safely modify without causing regressions.

## 2. Non-Goals

During service extraction in future PRs, the following boundaries must be strictly observed:
* **No API Response Changes**: Returned JSON structures, camelCase casing, and HTTP status codes must remain 100% identical.
* **No Route Path Changes**: Route paths, HTTP methods, parameters, and query options must not be changed.
* **No Frontend Changes**: The frontend must not be modified or affected.
* **No DB Schema Changes**: No changes to database models or migrations.
* **No Business Logic Rewrites**: The calculation logic, run execution steps, and core behaviors must remain exactly as is.

## 3. Proposed Service Boundaries

To separate concerns, logic should be refactored into the following target service/helper modules:

1. **Workspace Service (`backend/app/services/workspace_service.py`)**:
   * Encapsulates workspace creation, soft-deletion, list querying, and config configuration.
   * Interacts with `WorkspaceRepository` and legacy local `WorkspaceStore`.
2. **File Metadata Service (`backend/app/services/file_metadata_service.py`)**:
   * Encapsulates physical file saving/removal and metadata registry in database mode vs. legacy file store updates.
   * Interacts with `FileMetadataRepository` and legacy `FileStore`.
3. **Analysis Runtime Service (`backend/app/services/analysis_runtime_service.py`)**:
   * Orchestrates the execution of advisory runs and ratio calculation outputs, saving runs to the repository/local JSON.
   * Interacts with `AnalysisRunRepository`.
4. **Report Service (`backend/app/services/report_service.py`)**:
   * Handles saving report payloads, retrieving list configurations, and marking status updates or soft deletions.
   * Interacts with `ReportRepository`.
5. **Audit Service (`backend/app/services/audit_service.py`)**:
   * Implements best-effort audit logs and handles database/local routing checks.
   * Interacts with `AuditEventRepository`.
6. **Runtime Persistence Helpers (`backend/app/routes/workspaces.py` or separate module)**:
   * Retains FastAPI dependency injections (`Depends(...)`), the optional database session provider `get_db_session_optional()`, and `WorkspaceStore` monkeypatch hooks.

## 4. Proposed Extraction Order

To minimize risk, extraction must be completed in sequential, isolated phases:

* **Phase 1: Extract Audit Helper** [COMPLETED]
  * Move best-effort route-level logging checks and DB checks into `backend/app/services/audit_service.py`.
* **Phase 2: Extract Report Service** [COMPLETED]
  * Move report CRUD operations and validations into `backend/app/services/report_service.py`.
* **Phase 3: Extract File Metadata Service** [COMPLETED]
  * Move file save/delete logic and repository registrations into `backend/app/services/file_metadata_service.py`.
* **Phase 4: Extract Analysis Runtime Service**
  * Move execution wrap and `_db_save_run` orchestration into `backend/app/services/analysis_runtime_service.py`.
* **Phase 5: Extract Workspace Service**
  * Move workspace CRUD operations into `backend/app/services/workspace_service.py`.
* **Phase 6: Jobs/Workers Evaluation**
  * Final review of background jobs metadata processing.

## 5. Guardrails for Every Extraction PR

Every future refactoring PR must adhere to these guardrails:
1. **Single Responsibility per PR**: Refactor exactly one area (e.g., reports only) in each PR. Avoid multi-component refactors.
2. **No API Payloads/Response Regressions**: Strictly maintain response shapes.
3. **Local Mode as Default**: Keep `PERSISTENCE_BACKEND="local"` as the default setting.
4. **No DB Initialization in Local Mode**: Do not instantiate a database engine, connection pool, or session when local mode is active.
5. **Verification**: Run the full suite of health check and contract tests.
6. **Clean Working Tree**: Ensure zero unrelated or temporary files are committed.

## 6. Test Strategy

We will validate future extractions using:
* **Route Contract Guardrails**: Checks that HTTP paths, methods, and schemas remain exactly intact.
* **Health Check Integration Suite**: Runs the end-to-end flow to verify stability and check for DB engine leaks in local mode.
* **In-Memory SQLite**: Validates database mode during tests via a clean memory pool.
* **Temporary Directories**: Isolates filesystem alterations for local mode tests.

## 7. Risks and Mitigation

* **Risk**: Hidden Coupling with Calculation Engine.
  * *Mitigation*: Keep service APIs clean and avoid changing argument structures passed to execution functions.
* **Risk**: Accidental Database Session Initialization in Local Mode.
  * *Mitigation*: Continue using the dependency overrides and check that `db_session_mod._engine` is not set during local test runs.
* **Risk**: Best-effort Audit Failure Blockage.
  * *Mitigation*: Retain strict `try-except` wrappers around audit calls so that audit logging issues do not crash the primary route handlers.
* **Risk**: Duplication of Test Fixtures.
  * *Mitigation*: Centralize mock definitions and utilize standardized pytest fixtures.

## 8. Definition of Done for Future Extraction PRs

A service extraction PR is ready for merge only when:
* Route handlers contain only clean service delegations.
* No API response paths, payloads, or HTTP methods have changed.
* Local mode and Database mode test suites pass 100%.
* Production file sizes for `workspaces.py` are significantly reduced.
* Documentation (Roadmap, Task Board) is updated to mark the active phase as completed.
