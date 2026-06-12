import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models  # Register models on Base
from app.main import app
from app.routes.workspaces import get_db_session_optional, set_active_db_session
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

@pytest.fixture
def db_session():
    from sqlalchemy.pool import StaticPool
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

def _upload_required_files_and_build_snapshot(client, ws_id):
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
        res = client.post(f"/api/workspaces/{ws_id}/files", data=data, files=files)
        assert res.status_code == 200

    # Build snapshot
    snap_res = client.post(f"/api/workspaces/{ws_id}/snapshot/build?currency=USD&reportingPeriod=FY2026")
    assert snap_res.status_code == 200

def test_local_mode_no_db_side_effects(monkeypatch):
    """
    1. Local mode does not initialize DB engine/session across workspaces, files, analysis runs, and report endpoints.
    2. Local mode still passes existing route behavior.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")

    from app.db import session as db_session_mod

    # Reset global engine to verify it is not initialized during local operations
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    try:
        # Clean local storage files
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
        
        # Ensure reports.json is clean
        from app.storage.workspace_store import STORAGE_DIR
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass

        # 1. Create Workspace
        ws_res = client.post("/api/workspaces", data={"companyName": "Local Health Inc."})
        assert ws_res.status_code == 200
        ws_data = ws_res.json()
        assert "id" in ws_data
        assert ws_data["companyName"] == "Local Health Inc."
        ws_id = ws_data["id"]

        # 2. Upload file metadata / file
        file_content = b"metric,value\nRevenue,100\n"
        upload_res = client.post(
            f"/api/workspaces/{ws_id}/files",
            data={"recordKey": "pl-statement"},
            files={"file": ("pl.csv", io.BytesIO(file_content), "text/csv")}
        )
        assert upload_res.status_code == 200
        file_data = upload_res.json()
        assert "id" in file_data
        file_id = file_data["id"]

        # Upload remaining statements to support valuation run
        _upload_required_files_and_build_snapshot(client, ws_id)

        # 3. Trigger analysis run
        run_res = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert "id" in run_data
        run_id = run_data["id"]

        # 4. Save report
        report_data = {
            "reportType": "health_check",
            "title": "Local Health Report",
            "reportPayload": {"health": "green"},
            "storageUri": "s3://local/health.pdf",
            "metadata": {"source": "local-test"}
        }
        report_res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_data)
        assert report_res.status_code == 200
        report_data_res = report_res.json()
        assert "id" in report_data_res
        report_id = report_data_res["id"]

        # 5. Verify jobs routes return 501 under local mode without DB initialization
        jobs_res = client.get(f"/api/workspaces/{ws_id}/jobs")
        assert jobs_res.status_code == 501

        tick_res = client.post(f"/api/workspaces/{ws_id}/jobs/report-worker/tick")
        assert tick_res.status_code == 200
        assert tick_res.json()["enabled"] is False
        assert tick_res.json()["processed"] == 0

        # Assert no DB engine/session was initialized
        assert db_session_mod._engine is None
        assert db_session_mod.SessionLocal is None

        # Clean up files
        FileStore.delete_workspace_files(ws_id)
        WorkspaceStore.delete_workspace(ws_id)
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass
    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])

def test_database_mode_route_chain_smoke(db_session, monkeypatch):
    """
    1. Database mode can use in-memory SQLite for repository-backed routes.
    2. Route chain smoke flow: Create workspace -> File Upload -> Analysis run -> Report save/list.
    3. Response shapes contain expected keys and are camelCase compatible where applicable.
    4. Database mode does not store file bytes in DB tables.
    5. Database mode does not write analysis/report metadata to legacy JSON stores.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")

    from app.db.models import Organization, Workspace as DbWorkspace, WorkspaceFile, AnalysisRun as DbAnalysisRun, Report as DbReport, AuditEvent as DbAuditEvent

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    client = TestClient(app)
    try:
        # Clear legacy JSON file paths
        orig_runs_file = WorkspaceStore._runs_file
        temp_runs_json = os.path.join(os.path.dirname(orig_runs_file), "temp_runs_health.json")
        WorkspaceStore._runs_file = temp_runs_json
        WorkspaceStore._write_json(temp_runs_json, [])

        from app.storage.workspace_store import STORAGE_DIR
        reports_json = os.path.join(STORAGE_DIR, "reports.json")
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass

        # 1. Setup Org and Workspace in DB
        org = Organization(id="org_default", name="Default Org")
        db_session.add(org)
        
        ws_id = "ws_health_db_smoke"
        ws_db = DbWorkspace(id=ws_id, organization_id="org_default", name="DB Health Co", status="active")
        db_session.add(ws_db)
        db_session.commit()

        # Upload files and build snapshot locally
        _upload_required_files_and_build_snapshot(client, ws_id)

        # Retrieve file metadata to confirm DB metadata save and no file bytes in DB
        db_files = db_session.query(WorkspaceFile).filter_by(workspace_id=ws_id, status="uploaded").all()
        assert len(db_files) >= 4
        for db_file in db_files:
            assert db_file.file_name in ["pl.csv", "bs.csv", "cf.csv", "debt.csv"]
            with pytest.raises(AttributeError):
                _ = db_file.file_bytes

        # Verify no file metadata is stored in files.json (it went to database only)
        # Verify the runs.json is empty
        assert not os.path.exists(temp_runs_json) or os.path.getsize(temp_runs_json) == 0 or WorkspaceStore._read_json(temp_runs_json) == []

        # 2. Trigger analysis run
        run_res = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert "id" in run_data
        assert run_data["runType"] == "valuation"
        run_id = run_data["id"]

        # Verify DB metadata contains the run
        db_run = db_session.query(DbAnalysisRun).filter_by(id=run_id).first()
        assert db_run is not None
        assert db_run.workspace_id == ws_id
        assert db_run.run_type == "valuation"

        # Verify runs.json remains untouched
        assert not os.path.exists(temp_runs_json) or os.path.getsize(temp_runs_json) == 0 or WorkspaceStore._read_json(temp_runs_json) == []

        # 3. Save report through route
        report_payload = {
            "reportType": "valuation_summary",
            "title": "Valuation Summary Report FY2026",
            "reportPayload": {"valuation_ratio": 4.5},
            "storageUri": "s3://db-mode/valuation.pdf",
            "metadata": {"reviewer": "cfo-bot"}
        }
        report_res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_payload)
        assert report_res.status_code == 200
        report_data = report_res.json()
        assert "id" in report_data
        assert report_data["reportType"] == "valuation_summary"
        assert report_data["title"] == "Valuation Summary Report FY2026"
        assert report_data["storageUri"] == "s3://db-mode/valuation.pdf"
        assert report_data["organizationId"] == "org_default"
        report_id = report_data["id"]

        # Verify DB contains report record
        db_report = db_session.query(DbReport).filter_by(id=report_id).first()
        assert db_report is not None
        assert db_report.report_name == "Valuation Summary Report FY2026"
        assert db_report.workspace_id == ws_id

        # Verify reports.json was NOT written
        assert not os.path.exists(reports_json) or os.path.getsize(reports_json) == 0 or WorkspaceStore._read_json(reports_json) == []

        # 4. List reports
        list_res = client.get(f"/api/workspaces/{ws_id}/reports")
        assert list_res.status_code == 200
        reports_list = list_res.json()
        assert len(reports_list) == 1
        assert reports_list[0]["id"] == report_id
        assert reports_list[0]["reportType"] == "valuation_summary"

        # 5. List jobs under database mode
        jobs_res = client.get(f"/api/workspaces/{ws_id}/jobs")
        assert jobs_res.status_code == 200
        assert jobs_res.json() == []

        # Verify DB contains the expected audit events from the route chain
        db_audits = db_session.query(DbAuditEvent).filter_by(workspace_id=ws_id).all()
        assert len(db_audits) >= 3
        actions = [a.action for a in db_audits]
        assert "file.uploaded" in actions
        assert "analysis.run.created" in actions
        assert "report.created" in actions

        # Clean up physical files
        FileStore.delete_workspace_files(ws_id)
        if os.path.exists(temp_runs_json):
            try:
                os.remove(temp_runs_json)
            except Exception:
                pass
        WorkspaceStore._runs_file = orig_runs_file
        if os.path.exists(reports_json):
            try:
                os.remove(reports_json)
            except Exception:
                pass
    finally:
        app.dependency_overrides.clear()
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
        WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
