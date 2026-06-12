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

def _upload_required_files_and_build_snapshot(client, ws_id, headers):
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
        res = client.post(f"/api/workspaces/{ws_id}/files", data=data, files=files, headers=headers)
        assert res.status_code == 200

    # Build snapshot
    snap_res = client.post(f"/api/workspaces/{ws_id}/snapshot/build?currency=USD&reportingPeriod=FY2026", headers=headers)
    assert snap_res.status_code == 200

def test_database_mode_product_smoke_flow(db_session, monkeypatch):
    """
    Validates the core product flow in Database Mode:
    1. Create workspace
    2. Validate auth/local request context overrides don't break routes
    3. Upload workspace data & build snapshot
    4. Run stable analysis run (valuation)
    5. Save a report manually
    6. Create a report.generation background job
    7. List and Get the pending job
    8. Trigger worker tick manually
    9. Verify job completes and report is persisted
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "database")
    monkeypatch.setattr(settings, "AUTH_MODE", "local")
    monkeypatch.setattr(settings, "AUTH_ALLOW_HEADER_OVERRIDES", True)
    monkeypatch.setattr(settings, "AUTH_DEFAULT_ORGANIZATION_ID", "org_default")
    monkeypatch.setattr(settings, "AUTH_DEFAULT_USER_ID", "demo-user")
    monkeypatch.setattr(settings, "AUTH_DEFAULT_ROLE", "admin")

    def override_get_db_session():
        set_active_db_session(db_session)
        try:
            yield db_session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session
    client = TestClient(app)

    # 0. Validate new endpoints
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/api/runtime/status").status_code == 200

    headers = {
        "X-Organization-Id": "org_default",
        "X-User-Id": "demo-user",
        "X-Role": "admin"
    }

    ws_id = None
    try:
        # 1. Create Workspace
        ws_res = client.post("/api/workspaces", data={"companyName": "Smoke Test Corp"}, headers=headers)
        assert ws_res.status_code == 200
        ws_data = ws_res.json()
        assert "id" in ws_data
        ws_id = ws_data["id"]

        # 2. Validate auth/local request context doesn't break route usage
        # We perform the remaining requests passing custom overrides.
        
        # 3. Upload workspace data and build snapshot
        _upload_required_files_and_build_snapshot(client, ws_id, headers)

        # 4. Run stable analysis run path
        run_res = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run", headers=headers)
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert "id" in run_data
        assert run_data["runType"] == "valuation"

        # 5. Create / persist a report manually
        report_payload = {
            "reportType": "valuation_summary",
            "title": "Smoke Valuation Report",
            "reportPayload": {"valuation_ratio": 5.0},
            "storageUri": "s3://smoke-mode/valuation.pdf",
            "metadata": {"reviewer": "smoke-tester"}
        }
        report_res = client.post(f"/api/workspaces/{ws_id}/reports", json=report_payload, headers=headers)
        assert report_res.status_code == 200

        # 6. Create a report.generation job
        job_payload = {
            "reportType": "financial_health",
            "reportPayload": {"revenue": 150000, "expenses": 100000},
            "metadata": {"title": "Q4 Smoke Report"},
            "storageUri": "s3://smoke-bucket/reports/q4_smoke.pdf",
            "maxAttempts": 3
        }
        job_res = client.post(f"/api/workspaces/{ws_id}/jobs/report-generation", json=job_payload, headers=headers)
        assert job_res.status_code == 201
        job_data = job_res.json()
        job_id = job_data["id"]

        # 7. List jobs
        list_res = client.get(f"/api/workspaces/{ws_id}/jobs", headers=headers)
        assert list_res.status_code == 200
        jobs_list = list_res.json()
        assert len(jobs_list) == 1
        assert jobs_list[0]["id"] == job_id
        assert jobs_list[0]["status"] == "pending"

        # 8. Get job
        get_res = client.get(f"/api/workspaces/{ws_id}/jobs/{job_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "pending"

        # 9. Enable feature flag & call manual worker tick
        monkeypatch.setattr(settings, "REPORT_WORKER_ENABLED", True)
        monkeypatch.setattr(settings, "REPORT_WORKER_MAX_JOBS_PER_TICK", 1)

        tick_res = client.post(f"/api/workspaces/{ws_id}/jobs/report-worker/tick", headers=headers)
        assert tick_res.status_code == 200
        tick_data = tick_res.json()
        assert tick_data["enabled"] is True
        assert tick_data["processed"] == 1
        assert tick_data["succeeded"] == 1
        assert job_id in tick_data["jobIds"]

        # 10. Verify job status / progress moves and reports are persisted safely
        get_res_after = client.get(f"/api/workspaces/{ws_id}/jobs/{job_id}", headers=headers)
        assert get_res_after.status_code == 200
        assert get_res_after.json()["status"] == "completed"

        from app.db.models import Report as DbReport
        db_reports = db_session.query(DbReport).filter_by(workspace_id=ws_id).all()
        assert len(db_reports) == 2
        report_names = [r.report_name for r in db_reports]
        assert "Smoke Valuation Report" in report_names
        assert "Q4 Smoke Report" in report_names

    finally:
        app.dependency_overrides.clear()
        if ws_id:
            FileStore.delete_workspace_files(ws_id)
            # We don't delete from SQLite DB directly since in-memory DB is discarded after test,
            # but cascade file deletes is still good practice.

def test_local_mode_fallback_smoke_flow(monkeypatch):
    """
    Validates that local-mode 501 fallback behavior remains safe if job persistence
    is unavailable in that mode.
    """
    monkeypatch.setattr(settings, "PERSISTENCE_BACKEND", "local")
    monkeypatch.setattr(settings, "AUTH_MODE", "local")
    monkeypatch.setattr(settings, "AUTH_ALLOW_HEADER_OVERRIDES", True)

    from app.db import session as db_session_mod
    orig_engine = db_session_mod._engine
    orig_session_local = db_session_mod.SessionLocal
    db_session_mod._engine = None
    db_session_mod.SessionLocal = None

    client = TestClient(app)
    headers = {
        "X-Organization-Id": "demo-org",
        "X-User-Id": "demo-user",
        "X-Role": "admin"
    }

    try:
        # Create workspace in local JSON first to satisfy workspace existence checks
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
        WorkspaceStore.create_workspace("ws_local_smoke", "Local Corp")

        # 1. GET jobs fallback (501)
        res_list = client.get("/api/workspaces/ws_local_smoke/jobs", headers=headers)
        assert res_list.status_code == 501
        assert "Background jobs are not supported" in res_list.json()["detail"]

        # 2. GET individual job fallback (501)
        res_get = client.get("/api/workspaces/ws_local_smoke/jobs/job_any", headers=headers)
        assert res_get.status_code == 501

        # 3. POST create job fallback (501)
        res_post = client.post(
            "/api/workspaces/ws_local_smoke/jobs/report-generation",
            json={
                "reportType": "financial_health",
                "reportPayload": {"revenue": 10000},
                "metadata": {"title": "Q3 Reports"}
            },
            headers=headers
        )
        assert res_post.status_code == 501

        # 4. POST worker tick fallback (200, disabled, scanned=0)
        res_tick = client.post("/api/workspaces/ws_local_smoke/jobs/report-worker/tick", headers=headers)
        assert res_tick.status_code == 200
        assert res_tick.json()["enabled"] is False
        assert res_tick.json()["processed"] == 0

    finally:
        db_session_mod._engine = orig_engine
        db_session_mod.SessionLocal = orig_session_local
        WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
