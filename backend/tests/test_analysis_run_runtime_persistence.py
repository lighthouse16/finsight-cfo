import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models  # Ensure models register on Base
from app.main import app
from app.routes.workspaces import get_db_session_optional
from app.core.config import settings

@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
    # Setup SQLite in-memory database with StaticPool for TestClient compatibility
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

def _setup_workspace_and_snapshot(client) -> str:
    # 1. Create workspace
    create_response = client.post("/api/workspaces", data={
        "companyName": "DB Run Test Inc.",
        "currency": "USD",
        "reportingPeriod": "FY2026"
    })
    ws_id = create_response.json()["id"]

    # 2. Upload statements
    statements = {
        "pl-statement": (
            "pl.csv",
            b"metric,value\nRevenue,1000\nCOGS,(400)\nOperating Expenses,200\nEBIT,400\nDepreciation & Amortization,50\nEBITDA,450\nInterest Expense,30\nEBT,370\nTaxes,50\nNet Income,320\n",
            "text/csv"
        ),
        "balance-sheet": (
            "bs.csv",
            b"metric,value\nCash and Cash Equivalents,100\nAccounts Receivable,150\nInventory,120\nPrepaid,30\nCurrent Assets,400\nfixed_assets,300\nTotal Assets,700\nAccounts Payable,90\naccrued,30\nShort-Term Debt,50\nCurrent Portion of Long-Term Debt,40\nLong-Term Debt,210\nLease Liabilities,20\nCurrent Liabilities,210\nTotal Liabilities,440\nEquity,260\n",
            "text/csv"
        ),
        "cash-flow": (
            "cf.csv",
            b"metric,value\nOperating Cash Flow,180\ncapex,60\nDebt Issued,45\nDebt Repaid,40\nDividends,20\nnet_change_cash,105\n",
            "text/csv"
        ),
        "debt-schedule": (
            "debt.csv",
            b"metric,value\nScheduled Interest,30\nScheduled Principal,40\n",
            "text/csv"
        ),
    }

    for key, (filename, content, content_type) in statements.items():
        files = {"file": (filename, content, content_type)}
        data = {"recordKey": key}
        client.post(f"/api/workspaces/{ws_id}/files", data={**data}, files=files)

    # 3. Build snapshot
    client.post(f"/api/workspaces/{ws_id}/snapshot/build?currency=USD&reportingPeriod=FY2026")
    return ws_id

def test_analysis_runs_local_mode_no_db_side_effects(monkeypatch):
    """
    Local mode tests:
    1. Analysis runs routes still work using local persistence.
    2. No DB engine/session is created in local mode.
    3. Response shape is unchanged.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod
    from app.storage.workspace_store import WorkspaceStore
    from app.storage.file_store import FileStore

    # Reset global engine to verify it is not initialized during local operations
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Clean local storage
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])

        ws_id = _setup_workspace_and_snapshot(client)

        # Trigger Valuation Run
        run_res = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert "id" in run_data
        assert run_data["runType"] == "valuation"
        run_id = run_data["id"]

        # Get Latest Valuation Run
        latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/valuation/latest")
        assert latest_res.status_code == 200
        assert latest_res.json()["id"] == run_id

        # List runs
        list_res = client.get(f"/api/workspaces/{ws_id}/runs?type=valuation")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1

        # Get run by ID
        get_res = client.get(f"/api/workspaces/{ws_id}/runs/{run_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == run_id

        # Assert no DB engine/sessionmaker was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None

        # Clean local store files
        FileStore.delete_workspace_files(ws_id)
        WorkspaceStore.delete_workspace(ws_id)
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])


def test_analysis_runs_database_mode(db_session, monkeypatch):
    """
    Database mode tests:
    1. Analysis run trigger/save writes run metadata to DB.
    2. Runs list reads from DB.
    3. Run retrieval reads from DB.
    4. Database mode does NOT write analysis run metadata to legacy WorkspaceStore runs.json.
    5. Database mode uses existing workspace organization_id.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization, Workspace as DbWorkspace, AnalysisRun as DbAnalysisRun
    from app.storage.workspace_store import WorkspaceStore
    from app.storage.file_store import FileStore

    # Setup FastAPI dependency override
    from app.routes.workspaces import set_active_db_session
    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # Clear legacy WorkspaceStore runs.json completely to ensure no reads/writes
        orig_runs_file = WorkspaceStore._runs_file
        temp_runs_json = os.path.join(os.path.dirname(orig_runs_file), "temp_runs_test.json")
        WorkspaceStore._runs_file = temp_runs_json
        WorkspaceStore._write_json(temp_runs_json, [])

        # Setup workspace locally (snapshots and files stay local for now)
        ws_id = _setup_workspace_and_snapshot(client)

        # 1. Trigger Valuation Run in DB mode
        run_res = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert "id" in run_data
        assert run_data["runType"] == "valuation"
        run_id = run_data["id"]

        # Assert no metadata was written to runs.json (monkeypatch intercept worked!)
        assert not os.path.exists(temp_runs_json) or os.path.getsize(temp_runs_json) == 0 or WorkspaceStore._read_json(temp_runs_json) == []

        # Assert metadata is stored in DB
        db_run = db_session.query(DbAnalysisRun).filter_by(id=run_id).first()
        assert db_run is not None
        assert db_run.workspace_id == ws_id
        assert db_run.run_type == "valuation"
        assert db_run.organization_id == "org_default"

        # 2. Get Latest Valuation Run
        latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/valuation/latest")
        assert latest_res.status_code == 200
        assert latest_res.json()["id"] == run_id

        # 3. List runs
        list_res = client.get(f"/api/workspaces/{ws_id}/runs?type=valuation")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1
        assert list_res.json()[0]["id"] == run_id

        # 4. Get run by ID
        get_res = client.get(f"/api/workspaces/{ws_id}/runs/{run_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == run_id

        # Clean up files & workspace directory
        FileStore.delete_workspace_files(ws_id)
        if os.path.exists(temp_runs_json):
            try:
                os.remove(temp_runs_json)
            except Exception:
                pass
        WorkspaceStore._runs_file = orig_runs_file
    finally:
        app.dependency_overrides.clear()
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
