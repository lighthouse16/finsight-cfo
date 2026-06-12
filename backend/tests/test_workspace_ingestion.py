import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_storage_and_settings():
    # Store settings
    orig_mode = settings.APP_MODE
    orig_fallback = settings.ALLOW_DEMO_FALLBACK
    
    # Clear database if database mode is active
    if settings.normalized_persistence_backend == "database":
        from app.db.session import SessionLocal, get_engine
        get_engine()
        from app.db.session import SessionLocal
        if SessionLocal is not None:
            session = SessionLocal()
            try:
                from app.db.models import Workspace, WorkspaceFile, WorkspaceFileVersion, FinancialSnapshot, FinancialSnapshotVersion, AnalysisRun, AuditEvent, Job, Report
                session.query(WorkspaceFileVersion).delete()
                session.query(WorkspaceFile).delete()
                session.query(FinancialSnapshotVersion).delete()
                session.query(FinancialSnapshot).delete()
                session.query(AnalysisRun).delete()
                session.query(AuditEvent).delete()
                session.query(Job).delete()
                session.query(Report).delete()
                session.query(Workspace).delete()
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
                
    # Let tests run
    yield
    
    # Restore settings
    settings.APP_MODE = orig_mode
    settings.ALLOW_DEMO_FALLBACK = orig_fallback

def test_full_workspace_ingestion_lifecycle():
    # 1. Create workspace
    create_response = client.post("/api/workspaces", data={
        "companyName": "Ingestion Test Company Ltd.",
        "currency": "HKD",
        "reportingPeriod": "FY2025"
    })
    assert create_response.status_code == 200
    workspace = create_response.json()
    ws_id = workspace["id"]
    assert ws_id.startswith("workspace_")
    assert workspace["companyName"] == "Ingestion Test Company Ltd."
    assert workspace["metadata"]["currency"] == "HKD"
    assert workspace["metadata"]["reportingPeriod"] == "FY2025"

    # 2. Upload CSV P&L / Balance Sheet / Cash Flow / Debt Schedule
    statements = {
        "pl-statement": (
            "pl.csv",
            b"metric,value\nRevenue,2000\nCOGS,(900)\nOperating Expenses,500\nEBIT,420\nDepreciation & Amortization,80\nEBITDA,500\nInterest Expense,60\nEBT,360\nTaxes,70\nNet Income,300\n",
            "text/csv"
        ),
        "balance-sheet": (
            "bs.csv",
            b"metric,value\nCash and Cash Equivalents,200\nAccounts Receivable,300\nInventory,250\nPrepaid,50\nCurrent Assets,800\nfixed_assets,700\nTotal Assets,1500\nAccounts Payable,180\naccrued,70\nShort-Term Debt,100\nCurrent Portion of Long-Term Debt,80\nLong-Term Debt,420\nLease Liabilities,40\nCurrent Liabilities,450\nTotal Liabilities,800\nEquity,700\n",
            "text/csv"
        ),
        "cash-flow": (
            "cf.csv",
            b"metric,value\nOperating Cash Flow,360\ncapex,120\nDebt Issued,90\nDebt Repaid,80\nDividends,40\nnet_change_cash,210\n",
            "text/csv"
        ),
        "debt-schedule": (
            "debt.csv",
            b"metric,value\nScheduled Interest,60\nScheduled Principal,90\n",
            "text/csv"
        ),
    }

    uploaded_file_ids = []
    for key, (filename, content, content_type) in statements.items():
        files = {"file": (filename, content, content_type)}
        data = {"recordKey": key}
        upload_res = client.post(f"/api/workspaces/{ws_id}/files", data=data, files=files)
        assert upload_res.status_code == 200
        uploaded = upload_res.json()
        assert uploaded["recordKey"] == key
        assert uploaded["fileName"] == filename
        uploaded_file_ids.append(uploaded["id"])

    # 3. Parse uploaded files (verification by list endpoint)
    files_list_res = client.get(f"/api/workspaces/{ws_id}/files")
    assert files_list_res.status_code == 200
    files_list = files_list_res.json()
    assert len(files_list) == 4
    assert set(f["recordKey"] for f in files_list) == {
        "pl-statement", "balance-sheet", "cash-flow", "debt-schedule"
    }

    # 4. Build snapshot successfully
    build_res = client.post(f"/api/workspaces/{ws_id}/snapshot/build?currency=HKD&reportingPeriod=FY2025")
    assert build_res.status_code == 200
    build_data = build_res.json()
    assert build_data["status"] == "success"
    snapshot = build_data["snapshot"]
    assert snapshot["workspaceId"] == ws_id
    assert snapshot["currency"] == "HKD"
    assert snapshot["reportingPeriod"] == "FY2025"
    assert snapshot["incomeStatement"]["revenue"] == 2000
    assert snapshot["balanceSheet"]["totalAssets"] == 1500

    # 5. Get active snapshot
    active_res = client.get(f"/api/workspaces/{ws_id}/snapshot/active")
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data["status"] == "success"
    assert active_data["snapshot"]["id"] == snapshot["id"]

    # 6. Financial analysis resolves workspace snapshot
    # Configure production/no-demo mode
    settings.APP_MODE = "production"
    settings.ALLOW_DEMO_FALLBACK = False

    analysis_res = client.get("/api/financials/demo-analysis", headers={"x-workspace-id": ws_id})
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    assert analysis_data["snapshot"]["companyName"] == "Ingestion Test Company Ltd."
    assert analysis_data["snapshot"]["companyId"] == ws_id
    assert analysis_data["snapshot"]["currency"] == "HKD"
    assert analysis_data["snapshot"]["reportingPeriod"] == "FY2025"
    assert analysis_data["ratios"]["currentRatio"]["value"] > 0

    # 7. Build snapshot with missing required fields returns 422
    # Create another workspace with missing fields
    partial_ws_res = client.post("/api/workspaces", data={"companyName": "Partial Company"})
    partial_ws_id = partial_ws_res.json()["id"]
    
    # Upload only one file
    partial_files = {"file": ("pl.csv", statements["pl-statement"][1], "text/csv")}
    client.post(f"/api/workspaces/{partial_ws_id}/files", data={"recordKey": "pl-statement"}, files=partial_files)
    
    # Building snapshot should raise 422
    partial_build_res = client.post(f"/api/workspaces/{partial_ws_id}/snapshot/build")
    assert partial_build_res.status_code == 422
    assert partial_build_res.json()["detail"]["code"] == "INSUFFICIENT_WORKSPACE_DATA"

    # 8. Delete file removes metadata and physical file
    # Pick a file to delete from the first workspace
    target_file = files_list[0]
    target_file_id = target_file["id"]
    target_file_path = target_file["filePath"]
    
    assert os.path.exists(target_file_path)
    
    delete_file_res = client.delete(f"/api/workspaces/{ws_id}/files/{target_file_id}")
    assert delete_file_res.status_code == 200
    assert delete_file_res.json()["status"] == "success"
    
    # Assert physical file and metadata are gone
    assert not os.path.exists(target_file_path)
    assert FileStore.get_file_record(target_file_id) is None

    # 9. Delete workspace cascades workspace files/snapshots/runs/audits
    delete_ws_res = client.delete(f"/api/workspaces/{ws_id}")
    assert delete_ws_res.status_code == 200
    assert delete_ws_res.json()["status"] == "success"
    
    # Assert workspace is gone
    assert WorkspaceStore.get_workspace(ws_id) is None
    # Assert snapshots/runs/audits are gone
    assert WorkspaceStore.get_active_snapshot(ws_id) is None
    assert len(WorkspaceStore.get_audit_events(ws_id)) == 0
    # Assert remaining files are physically deleted
    for remaining_file in files_list[1:]:
        assert not os.path.exists(remaining_file["filePath"])

    # Clean up partial workspace
    client.delete(f"/api/workspaces/{partial_ws_id}")


def test_production_no_demo_never_falls_back_to_harbour_finch():
    settings.APP_MODE = "production"
    settings.ALLOW_DEMO_FALLBACK = False

    # Call financials without any workspace ID -> should raise WORKSPACE_DATA_NOT_FOUND (404)
    response = client.get("/api/financials/demo-analysis")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] in ("WORKSPACE_DATA_NOT_FOUND", "ACTIVE_SNAPSHOT_NOT_FOUND")
    assert "Harbour & Finch" not in response.text
