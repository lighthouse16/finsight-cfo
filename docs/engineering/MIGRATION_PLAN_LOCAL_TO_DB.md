# Database Migration Plan: Local Storage to Database

This document details the transition plan from localized file-based JSON storage to database persistence for FinSight CFO.

---

## 1. Current Local Storage Overview

The MVP persists all structures as files in `backend/storage_db/`. Workspaces are stored in JSON format, and document uploads save as raw files.
- **`storage_db/workspaces.json`**: Core metadata containing list of workspaces.
- **`storage_db/workspace_preview_{workspace_id}.json`**: Temporary snapshot previews.
- **`storage_db/runs/`**: Folder containing individual analysis run results.

---

## 2. Migration Goals

- **Zero API Downtime / Code Disruptions**: The migration must not alter existing API endpoints, request schemas, or response shapes.
- **Robust Local Adaptability**: Keep local JSON adapter operational for developers and offline presentations.
- **Configuration-Driven Storage**: Use `PERSISTENCE_BACKEND` (values: `local` | `database`) to toggle storage modes dynamically.

---

## 3. Phased Migration Strategy

### Phase 1: Persistence Abstraction (Sprint 1)
- Create abstract repository base classes (e.g. `WorkspaceRepository`, `AnalysisRunRepository`).
- Refactor the existing `WorkspaceStore` into `LocalWorkspaceRepository` inheriting from the abstract interfaces.

### Phase 2: Schema Migrations (Sprint 1)
- Introduce SQLAlchemy/SQLModel models matching `DB_SCHEMA_PROPOSAL.md`.
- Set up Alembic migration scripts and run baseline migrations.

### Phase 3: DB Adapter Implementation & Tests (Sprint 1)
- Implement `SqlWorkspaceRepository` using SQLAlchemy.
- Run the repository test suites against both `LocalWorkspaceRepository` and `SqlWorkspaceRepository`.

### Phase 4: Integration & Feature Flag Activation (Sprint 1/2)
- Bind the factory pattern in dependency injection based on `PERSISTENCE_BACKEND`.
- Run full system integration tests in both `local` and `database` modes.

### Phase 5: Production Data Cutover (Sprint 2)
- Deploy database models to staging/production clusters.
- Run the extraction & import backfill script.
- Switch production configuration `PERSISTENCE_BACKEND=database`.

---

## 4. Compatibility Layer Design

We will introduce a Repository Factory function to wire repositories into FastAPI dependencies:

```python
# backend/app/core/repositories.py
from app.core.config import settings
from app.storage.workspace_store import LocalWorkspaceRepository
from app.storage.db_workspace_store import SqlWorkspaceRepository
from app.storage.interfaces import WorkspaceRepository

def get_workspace_repository() -> WorkspaceRepository:
    if settings.PERSISTENCE_BACKEND == "database":
        # Returns SQLAlchemy-backed repository
        return SqlWorkspaceRepository()
    # Fallback to local files
    return LocalWorkspaceRepository()
```

---

## 5. Suggested Repository Interfaces

We will define three core abstract classes under `backend/app/storage/interfaces.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional, list
from app.models.workspace import CompanyWorkspace, AnalysisRun

class WorkspaceRepository(ABC):
    @abstractmethod
    def get_workspace(self, workspace_id: str, org_id: str) -> Optional[CompanyWorkspace]:
        pass

    @abstractmethod
    def save_workspace(self, workspace: CompanyWorkspace, org_id: str) -> CompanyWorkspace:
        pass

class FileRepository(ABC):
    @abstractmethod
    def save_file_record(self, filename: str, workspace_id: str, org_id: str) -> str:
        pass

class AnalysisRunRepository(ABC):
    @abstractmethod
    def save_run(self, run: AnalysisRun, org_id: str) -> AnalysisRun:
        pass

    @abstractmethod
    def get_run(self, run_id: str, org_id: str) -> Optional[AnalysisRun]:
        pass
```

---

## 6. Backfill/Import Strategy for Local Demo Data

A script `backend/app/scripts/backfill_to_db.py` will handle data transfer:
1. Initialize the target database session.
2. Read the local `workspaces.json` directory.
3. For each workspace found:
   - Create or select an organization (default "demo-org").
   - Populate `workspaces` table record.
   - Read local snapshots, insert into `financial_snapshots` and `financial_snapshot_versions`.
   - Read local analysis runs from `storage_db/runs/` and insert them into `analysis_runs` and `analysis_run_artifacts`.
4. Run validation check: Verify that total records migrated matches file counts.

---

## 7. Rollback Strategy

If a production database error occurs after cutover:
1. Keep the local storage directory untouched during the initial database run.
2. Toggling the feature flag back (`PERSISTENCE_BACKEND=local`) will restore local JSON reads and writes immediately.
3. Keep database replication active or perform differential database backups before toggle.

---

## 8. Testing Strategy

- **Contract Tests**:
  Construct unit tests that accept any class implementing `WorkspaceRepository`. Run the exact same assertions against `LocalWorkspaceRepository` (pointing to temporary files) and `SqlWorkspaceRepository` (pointing to an in-memory SQLite database).
- **Integration Tests**:
  FastAPI test clients run two passes on CI: once with `PERSISTENCE_BACKEND=local` and once with `PERSISTENCE_BACKEND=database` (using SQLite backend).

---

## 9. Cutover Checklist

- [ ] Run pre-deployment backup of all local storage JSON files.
- [ ] Run Alembic migrations on the target production database.
- [ ] Deploy updated backend application image (includes repository factory).
- [ ] Run `backfill_to_db.py` script.
- [ ] Verify database record counts match local directory files.
- [ ] Toggle `PERSISTENCE_BACKEND=database`.
- [ ] Verify health checks and check client dashboards.

---

## 10. What Not to Migrate Yet

- **Raw File Bytes**: Do not migrate actual file binaries (CSV/XLSX bytes) to the database. File metadata and versions will live in the database, but bytes will remain on local filesystem storage until a dedicated Object Storage (AWS S3) PR is introduced.
- **RBAC Organization Management UI**: The UI will not have organization configuration pages yet; default user-to-organization mapping will be populated via configuration variables.
