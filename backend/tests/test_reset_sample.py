import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore
from app.storage.file_store import FileStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_config():
    # Store settings
    orig_mode = settings.APP_MODE
    orig_fallback = settings.ALLOW_DEMO_FALLBACK
    
    # Clean up workspace sample if exists
    WorkspaceStore.delete_workspace("workspace_sample_novus")
    FileStore.delete_workspace_files("workspace_sample_novus")

    yield
    
    # Restore settings
    settings.APP_MODE = orig_mode
    settings.ALLOW_DEMO_FALLBACK = orig_fallback
    
    # Cleanup workspace sample after tests
    WorkspaceStore.delete_workspace("workspace_sample_novus")
    FileStore.delete_workspace_files("workspace_sample_novus")


def test_reset_sample_disabled_in_production():
    # APP_MODE = "production", ALLOW_DEMO_FALLBACK = True -> should fail (403)
    settings.APP_MODE = "production"
    settings.ALLOW_DEMO_FALLBACK = True
    
    response = client.post("/api/workspaces/reset-sample")
    assert response.status_code == 403
    json_data = response.json()
    assert json_data["detail"]["code"] == "DEMO_HELPER_DISABLED"
    assert json_data["detail"]["source"] == "system_config"


def test_reset_sample_disabled_without_demo_fallback():
    # APP_MODE = "development", ALLOW_DEMO_FALLBACK = False -> should fail (403)
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = False
    
    response = client.post("/api/workspaces/reset-sample")
    assert response.status_code == 403
    json_data = response.json()
    assert json_data["detail"]["code"] == "DEMO_HELPER_DISABLED"
    assert json_data["detail"]["source"] == "system_config"


def test_reset_sample_success_and_idempotent():
    # APP_MODE = "development", ALLOW_DEMO_FALLBACK = True -> should succeed
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = True
    
    # First execution
    response = client.post("/api/workspaces/reset-sample")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["workspaceId"] == "workspace_sample_novus"
    assert data["companyName"] == "Novus Retail Solutions Ltd"
    assert data["snapshotId"].startswith("snap_workspace_sample_novus_")
    
    runs = data["runs"]
    assert "financial_health" in runs
    assert "valuation" in runs
    assert "credit_score" in runs
    assert "funding_strategy" in runs
    assert "advisory_blueprint" in runs
    assert "workflow" in runs

    # Verify workspace, snapshot, and runs exist in storage
    workspace = WorkspaceStore.get_workspace("workspace_sample_novus")
    assert workspace is not None
    assert workspace.company_name == "Novus Retail Solutions Ltd"
    
    snapshot = WorkspaceStore.get_active_snapshot("workspace_sample_novus")
    assert snapshot is not None
    assert snapshot.id == data["snapshotId"]
    assert snapshot.reporting_period == "FY2025"
    assert snapshot.currency == "HKD"
    
    fh_run = WorkspaceStore.get_latest_run_by_type("workspace_sample_novus", "financial_health")
    assert fh_run is not None
    assert fh_run.id == runs["financial_health"]
    
    # Second execution (idempotency check: delete/recreate succeeds)
    response_again = client.post("/api/workspaces/reset-sample")
    assert response_again.status_code == 200
    data_again = response_again.json()
    
    assert data_again["status"] == "success"
    assert data_again["workspaceId"] == "workspace_sample_novus"
    assert data_again["companyName"] == "Novus Retail Solutions Ltd"
    
    # Confirm old runs/snapshots are replaced or new ones compiled cleanly
    snapshot_again = WorkspaceStore.get_active_snapshot("workspace_sample_novus")
    assert snapshot_again is not None
    assert snapshot_again.id == data_again["snapshotId"]
