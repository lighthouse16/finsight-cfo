import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.models.workspace import AnalysisRun
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_storage_and_settings():
    # Store settings
    orig_mode = settings.APP_MODE
    orig_fallback = settings.ALLOW_DEMO_FALLBACK
    
    # Clear database
    WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
    WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
    WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
    WorkspaceStore._write_json(WorkspaceStore._audits_file, [])
    
    # Yield to run test
    yield
    
    # Restore settings
    settings.APP_MODE = orig_mode
    settings.ALLOW_DEMO_FALLBACK = orig_fallback

    # Clear database again
    WorkspaceStore._write_json(WorkspaceStore._workspaces_file, [])
    WorkspaceStore._write_json(WorkspaceStore._snapshots_file, [])
    WorkspaceStore._write_json(WorkspaceStore._runs_file, [])
    WorkspaceStore._write_json(WorkspaceStore._audits_file, [])


def _setup_active_workspace() -> str:
    # 1. Create workspace
    create_response = client.post("/api/workspaces", data={
        "companyName": "Analysis Test Inc.",
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


def test_analysis_run_serialization():
    """1. Test AnalysisRun model serialization/deserialization."""
    run_dict = {
        "id": "run_test_123",
        "workspaceId": "workspace_test_123",
        "snapshotId": "snap_test_123",
        "runType": "valuation",
        "status": "completed",
        "inputs": {"currency": "USD"},
        "results": {"enterpriseValue": 500000},
        "warnings": ["Test warning"],
        "errors": [],
        "sourceTrace": {"snapshot_source": "test"},
        "logicVersion": "ratio_engine_v1",
        "createdAt": "2026-06-11T00:00:00Z",
        "durationMs": 45
    }
    
    run_obj = AnalysisRun.model_validate(run_dict)
    assert run_obj.id == "run_test_123"
    assert run_obj.run_type == "valuation"
    assert run_obj.duration_ms == 45
    
    dumped = run_obj.model_dump(by_alias=True)
    assert dumped["runType"] == "valuation"
    assert dumped["durationMs"] == 45


def test_workspace_store_run_methods():
    """2. Test WorkspaceStore save/list/latest/get run methods."""
    ws_id = "ws_store_methods"
    run_1 = AnalysisRun(
        id="run_1",
        workspaceId=ws_id,
        snapshotId="snap_1",
        runType="financial_health",
        status="completed",
        results={"val": 1},
        createdAt="2026-06-11T00:00:00Z"
    )
    run_2 = AnalysisRun(
        id="run_2",
        workspaceId=ws_id,
        snapshotId="snap_1",
        runType="financial_health",
        status="completed",
        results={"val": 2},
        createdAt="2026-06-11T01:00:00Z"
    )
    
    # Save runs
    WorkspaceStore.save_analysis_run(run_1)
    WorkspaceStore.save_analysis_run(run_2)
    
    # Get run
    retrieved = WorkspaceStore.get_run("run_1")
    assert retrieved is not None
    assert retrieved.results == {"val": 1}
    
    # List runs
    runs = WorkspaceStore.list_runs(ws_id)
    assert len(runs) == 2
    
    # Latest run
    latest = WorkspaceStore.get_latest_run_by_type(ws_id, "financial_health")
    assert latest is not None
    assert latest.id == "run_2"


def test_financial_health_run_persistence():
    """3. Test financial_health run persistence via /demo-analysis header."""
    ws_id = _setup_active_workspace()
    
    # Calling demo-analysis with workspace header triggers persistence
    response = client.get("/api/financials/demo-analysis", headers={"x-workspace-id": ws_id})
    assert response.status_code == 200
    res_data = response.json()
    assert "run_metadata" in res_data
    
    run_id = res_data["run_metadata"]["runId"]
    stored_run = WorkspaceStore.get_run(run_id)
    assert stored_run is not None
    assert stored_run.run_type == "financial_health"
    assert stored_run.status == "completed"


def test_valuation_run_persistence():
    """4. Test valuation run persistence."""
    ws_id = _setup_active_workspace()
    
    response = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["runType"] == "valuation"
    
    latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/valuation/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == run_data["id"]


def test_credit_score_run_persistence():
    """5. Test credit_score run persistence."""
    ws_id = _setup_active_workspace()
    
    response = client.post(f"/api/workspaces/{ws_id}/analysis/credit-score/run")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["runType"] == "credit_score"
    
    latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/credit-score/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == run_data["id"]


def test_funding_strategy_run_persistence():
    """6. Test funding_strategy run persistence."""
    ws_id = _setup_active_workspace()
    
    response = client.post(f"/api/workspaces/{ws_id}/analysis/funding-strategy/run")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["runType"] == "funding_strategy"
    
    latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/funding-strategy/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == run_data["id"]


def test_advisory_blueprint_run_persistence():
    """7. Test advisory_blueprint run persistence."""
    ws_id = _setup_active_workspace()
    
    response = client.post(f"/api/workspaces/{ws_id}/analysis/advisory-blueprint/run")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["runType"] == "advisory_blueprint"
    
    latest_res = client.get(f"/api/workspaces/{ws_id}/analysis/advisory-blueprint/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == run_data["id"]


def test_workflow_run_persistence():
    """8. Test workflow_run persistence with subRunIds."""
    ws_id = _setup_active_workspace()
    
    response = client.post(f"/api/workspaces/{ws_id}/analysis/workflow/run")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["runType"] == "workflow_run"
    assert "subRunIds" in run_data["results"]
    assert "financial_health" in run_data["results"]["subRunIds"]
    
    # Verify subruns are persisted as individual AnalysisRuns
    fh_run_id = run_data["results"]["subRunIds"]["financial_health"]
    stored_fh = WorkspaceStore.get_run(fh_run_id)
    assert stored_fh is not None
    assert stored_fh.run_type == "financial_health"


def test_run_immutability():
    """9. Run immutability: two reruns produce two run_ids."""
    ws_id = _setup_active_workspace()
    
    run_1 = client.post(f"/api/workspaces/{ws_id}/analysis/financial-health/run").json()
    run_2 = client.post(f"/api/workspaces/{ws_id}/analysis/financial-health/run").json()
    
    assert run_1["id"] != run_2["id"]
    
    all_runs = client.get(f"/api/workspaces/{ws_id}/runs?type=financial_health").json()
    run_ids = [r["id"] for r in all_runs]
    assert run_1["id"] in run_ids
    assert run_2["id"] in run_ids


def test_latest_run_returns_newest():
    """10. Latest run query returns the most recent run."""
    ws_id = _setup_active_workspace()
    
    run_1 = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run").json()
    # Modify second run's created_at to guarantee newer sorting
    run_2 = client.post(f"/api/workspaces/{ws_id}/analysis/valuation/run").json()
    
    latest_run = client.get(f"/api/workspaces/{ws_id}/runs/latest?type=valuation").json()
    assert latest_run["id"] == run_2["id"]


def test_run_deletion_cascade():
    """11. Deleting workspace cascades run deletion."""
    ws_id = _setup_active_workspace()
    run = client.post(f"/api/workspaces/{ws_id}/analysis/financial-health/run").json()
    
    # Assert run exists in store
    assert WorkspaceStore.get_run(run["id"]) is not None
    
    # Delete workspace
    delete_res = client.delete(f"/api/workspaces/{ws_id}")
    assert delete_res.status_code == 200
    
    # Assert run is deleted from store
    assert WorkspaceStore.get_run(run["id"]) is None


def test_demo_fallback_paths_do_not_create_runs():
    """12. Demo fallback paths do not create runs."""
    settings.ALLOW_DEMO_FALLBACK = True
    settings.APP_MODE = "development"
    
    # Call financials and advisory demo endpoints without header
    res_fin = client.get("/api/financials/demo-analysis")
    assert res_fin.status_code == 200
    assert "run_metadata" not in res_fin.json()
    
    res_adv = client.get("/api/advisory/demo-blueprint")
    assert res_adv.status_code == 200
    assert "run_metadata" not in res_adv.json()


def test_production_no_demo_enforcement():
    """13. Production mode raises 404/422 on missing workspace/snapshot."""
    settings.ALLOW_DEMO_FALLBACK = False
    settings.APP_MODE = "production"
    
    # Call with non-existent workspace ID -> 404
    response = client.get("/api/financials/demo-analysis", headers={"x-workspace-id": "missing_123"})
    assert response.status_code == 404
    
    # Trigger POST run on missing workspace -> 404
    post_response = client.post("/api/workspaces/missing_123/analysis/financial-health/run")
    assert post_response.status_code == 404
