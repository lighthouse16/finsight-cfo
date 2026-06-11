import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.storage.workspace_store import WorkspaceStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_settings():
    # Store original settings
    orig_mode = settings.APP_MODE
    orig_fallback = settings.ALLOW_DEMO_FALLBACK
    orig_fixtures = settings.MARKET_WATCH_USE_FIXTURES
    yield
    # Restore original settings
    settings.APP_MODE = orig_mode
    settings.ALLOW_DEMO_FALLBACK = orig_fallback
    settings.MARKET_WATCH_USE_FIXTURES = orig_fixtures

def test_financials_production_no_snapshot():
    settings.APP_MODE = "production"
    settings.ALLOW_DEMO_FALLBACK = True
    
    response = client.get("/api/financials/demo-analysis")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] in ("WORKSPACE_DATA_NOT_FOUND", "ACTIVE_SNAPSHOT_NOT_FOUND")
    assert data["detail"]["source"] == "workspace"
    assert "nextActions" in data["detail"]

def test_financials_fallback_disabled():
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = False
    
    response = client.get("/api/financials/demo-analysis")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["source"] == "workspace"

def test_financials_development_fallback_allowed():
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = True
    
    response = client.get("/api/financials/demo-analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["snapshot"]["companyName"] == "Harbour & Finch Trading Ltd."

def test_cdi_mock_consent_blocked_in_production():
    settings.APP_MODE = "production"
    
    response = client.post("/api/cdi/mock-consent", json={
        "companyId": "comp_123",
        "companyName": "Test Company",
        "requestedScopes": ["bank_transactions"]
    })
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["code"] == "CONSENT_PROVIDER_UNAVAILABLE"
    assert data["detail"]["source"] == "provider"

def test_cdi_mock_data_blocked_when_fallback_disabled():
    settings.APP_MODE = "development"
    settings.ALLOW_DEMO_FALLBACK = False
    
    response = client.get("/api/cdi/mock-data/mock_cdi_1234")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["code"] == "CONSENT_PROVIDER_UNAVAILABLE"

def test_market_watch_company_context_blocked_in_production():
    settings.APP_MODE = "production"
    
    response = client.get("/api/market-watch/company-context")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] in ("WORKSPACE_DATA_NOT_FOUND", "ACTIVE_SNAPSHOT_NOT_FOUND")

def test_market_watch_rates_liquidity_upstream_unavailable_in_production():
    settings.APP_MODE = "production"
    settings.MARKET_WATCH_USE_FIXTURES = True
    
    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["code"] == "UPSTREAM_UNAVAILABLE"
    assert data["detail"]["source"] == "provider"

def test_workspace_snapshot_build_insufficient_data():
    # Create workspace to build on
    ws_id = "ws_temp_test_hardening"
    # Ensure it's clean
    ws = WorkspaceStore.create_workspace(ws_id, "Hardening Temp Company")
    
    response = client.post(f"/api/workspaces/{ws_id}/snapshot/build")
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "INSUFFICIENT_WORKSPACE_DATA"
    assert "missingRequirements" in data["detail"]
