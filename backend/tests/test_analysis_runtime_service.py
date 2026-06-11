import pytest
from typing import Optional
from fastapi import HTTPException
from app.services.analysis_runtime_service import (
    run_analysis_stage,
    get_latest_analysis_stage,
    list_workspace_runs,
    get_workspace_run_latest_generic,
    get_workspace_run_by_id,
)
from app.models.workspace import AnalysisRun

class DummyRunResult:
    def __init__(
        self,
        id="run_123",
        snapshot_id="snap_123",
        run_type="financial_health",
        status="completed",
        inputs=None,
        results=None,
        warnings=None,
        errors=None,
        source_trace=None,
        logic_version="v1",
        duration_ms=150,
    ):
        self.id = id
        self.snapshot_id = snapshot_id
        self.run_type = run_type
        self.status = status
        self.inputs = inputs or {}
        self.results = results or {"score": 85}
        self.warnings = warnings or []
        self.errors = errors or []
        self.source_trace = source_trace or {}
        self.logic_version = logic_version
        self.duration_ms = duration_ms
        self.created_at = "2026-06-11T00:00:00Z"

def dummy_sync_execution(workspace_id, snapshot_id):
    return DummyRunResult(id="run_sync_123")

async def dummy_async_execution(workspace_id, snapshot_id):
    return DummyRunResult(id="run_async_123", run_type="workflow_run")

class MockWorkspaceRepository:
    def __init__(self, exists=True):
        self.exists = exists

    def get_workspace(self, workspace_id: str):
        if self.exists:
            from app.models.workspace import CompanyWorkspace
            return CompanyWorkspace(
                id=workspace_id,
                companyName="Test Workspace",
                createdAt="2026-06-11T00:00:00Z",
                metadata={}
            )
        return None

class MockAnalysisRunRepository:
    def __init__(self, runs=None):
        self.runs = runs or {}
        self.save_called = False
        self.session = "dummy_session"

    def save_run(
        self,
        workspace_id: str,
        run_type: str,
        status: str,
        input_payload: dict,
        output_payload: dict,
        summary: dict,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.save_called = True
        run_id = metadata.get("run_id") if metadata else f"run_{len(self.runs) + 1}"
        run_record = {
            "id": run_id,
            "workspaceId": workspace_id,
            "snapshotId": metadata.get("snapshot_id") if metadata else "snap_123",
            "runType": run_type,
            "status": status,
            "inputs": input_payload,
            "results": output_payload,
            "warnings": summary.get("warnings", []),
            "errors": summary.get("errors", []),
            "sourceTrace": metadata.get("source_trace", {}),
            "logicVersion": metadata.get("logic_version", "v1"),
            "createdAt": "2026-06-11T00:00:00Z",
            "completedAt": "2026-06-11T00:00:01Z",
            "durationMs": metadata.get("duration_ms", 100) if metadata else 100,
        }
        self.runs[run_id] = run_record
        return run_record

    def get_run(self, run_id: str):
        return self.runs.get(run_id)

    def list_runs(self, workspace_id: str):
        return sorted([r for r in self.runs.values() if r["workspaceId"] == workspace_id], key=lambda x: x["id"], reverse=True)

class MockSettings:
    def __init__(self, persistence_backend="database"):
        self.normalized_persistence_backend = persistence_backend

@pytest.mark.anyio
async def test_run_analysis_stage_sync_database():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository()
    settings = MockSettings("database")

    res = await run_analysis_stage(
        workspace_id="ws_123",
        snapshot_id="snap_123",
        execution_fn=dummy_sync_execution,
        run_repo=run_repo,
        workspace_repo=ws_repo,
        settings=settings
    )

    assert isinstance(res, AnalysisRun)
    assert res.id == "run_sync_123"
    assert res.run_type == "financial_health"
    assert run_repo.save_called

@pytest.mark.anyio
async def test_run_analysis_stage_async_database():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository()
    settings = MockSettings("database")

    res = await run_analysis_stage(
        workspace_id="ws_123",
        snapshot_id="snap_123",
        execution_fn=dummy_async_execution,
        run_repo=run_repo,
        workspace_repo=ws_repo,
        settings=settings
    )

    assert isinstance(res, AnalysisRun)
    assert res.id == "run_async_123"
    assert res.run_type == "workflow_run"
    assert run_repo.save_called

@pytest.mark.anyio
async def test_run_analysis_stage_local_mode():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository()
    settings = MockSettings("local")

    res = await run_analysis_stage(
        workspace_id="ws_123",
        snapshot_id="snap_123",
        execution_fn=dummy_sync_execution,
        run_repo=run_repo,
        workspace_repo=ws_repo,
        settings=settings
    )

    assert isinstance(res, DummyRunResult)
    assert res.id == "run_sync_123"
    assert not run_repo.save_called

@pytest.mark.anyio
async def test_run_analysis_stage_missing_workspace():
    ws_repo = MockWorkspaceRepository(exists=False)
    run_repo = MockAnalysisRunRepository()
    settings = MockSettings()

    with pytest.raises(HTTPException) as exc_info:
        await run_analysis_stage(
            workspace_id="ws_missing",
            snapshot_id="snap_123",
            execution_fn=dummy_sync_execution,
            run_repo=run_repo,
            workspace_repo=ws_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Workspace not found"

def test_get_latest_analysis_stage_database():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository(runs={
        "run_1": {
            "id": "run_1",
            "workspaceId": "ws_123",
            "snapshotId": "snap_123",
            "runType": "valuation",
            "status": "completed",
            "inputs": {},
            "results": {},
            "warnings": [],
            "errors": [],
            "sourceTrace": {},
            "logicVersion": "v1",
            "createdAt": "2026-06-11T00:00:00Z",
        }
    })
    settings = MockSettings("database")

    res = get_latest_analysis_stage(
        workspace_id="ws_123",
        run_type="valuation",
        workspace_repo=ws_repo,
        run_repo=run_repo,
        settings=settings
    )

    assert isinstance(res, AnalysisRun)
    assert res.id == "run_1"

def test_get_latest_analysis_stage_missing():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository()
    settings = MockSettings("database")

    with pytest.raises(HTTPException) as exc_info:
        get_latest_analysis_stage(
            workspace_id="ws_123",
            run_type="valuation",
            workspace_repo=ws_repo,
            run_repo=run_repo,
            settings=settings
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No valuation runs found for this workspace"

def test_list_workspace_runs_database():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository(runs={
        "run_1": {
            "id": "run_1",
            "workspaceId": "ws_123",
            "snapshotId": "snap_123",
            "runType": "valuation",
            "status": "completed",
            "inputs": {},
            "results": {},
            "warnings": [],
            "errors": [],
            "sourceTrace": {},
            "logicVersion": "v1",
            "createdAt": "2026-06-11T00:00:00Z",
        },
        "run_2": {
            "id": "run_2",
            "workspaceId": "ws_123",
            "snapshotId": "snap_123",
            "runType": "financial_health",
            "status": "completed",
            "inputs": {},
            "results": {},
            "warnings": [],
            "errors": [],
            "sourceTrace": {},
            "logicVersion": "v1",
            "createdAt": "2026-06-11T00:00:00Z",
        }
    })
    settings = MockSettings("database")

    res = list_workspace_runs(
        workspace_id="ws_123",
        run_type="valuation",
        workspace_repo=ws_repo,
        run_repo=run_repo,
        settings=settings
    )

    assert len(res) == 1
    assert res[0].id == "run_1"

def test_get_workspace_run_latest_generic():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository(runs={
        "run_1": {
            "id": "run_1",
            "workspaceId": "ws_123",
            "snapshotId": "snap_123",
            "runType": "valuation",
            "status": "completed",
            "inputs": {},
            "results": {},
            "warnings": [],
            "errors": [],
            "sourceTrace": {},
            "logicVersion": "v1",
            "createdAt": "2026-06-11T00:00:00Z",
        }
    })
    settings = MockSettings("database")

    res = get_workspace_run_latest_generic(
        workspace_id="ws_123",
        run_type="valuation",
        workspace_repo=ws_repo,
        run_repo=run_repo,
        settings=settings
    )

    assert res.id == "run_1"

def test_get_workspace_run_by_id():
    ws_repo = MockWorkspaceRepository()
    run_repo = MockAnalysisRunRepository(runs={
        "run_1": {
            "id": "run_1",
            "workspaceId": "ws_123",
            "snapshotId": "snap_123",
            "runType": "valuation",
            "status": "completed",
            "inputs": {},
            "results": {},
            "warnings": [],
            "errors": [],
            "sourceTrace": {},
            "logicVersion": "v1",
            "createdAt": "2026-06-11T00:00:00Z",
        }
    })
    settings = MockSettings("database")

    res = get_workspace_run_by_id(
        workspace_id="ws_123",
        run_id="run_1",
        workspace_repo=ws_repo,
        run_repo=run_repo,
        settings=settings
    )

    assert res.id == "run_1"
