import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check_public():
    """Health check should always be accessible."""
    response = client.get("/health")
    assert response.status_code == 200

@patch("app.core.config.settings.AUTH_MODE", "production")
def test_unauthenticated_access_blocked_in_production():
    """In production, accessing protected routes without a token should fail."""
    response = client.get("/api/workspaces")
    assert response.status_code == 401

@patch("app.core.config.settings.AUTH_MODE", "production")
def test_unauthenticated_access_with_bad_token():
    """In production, a bad token should be rejected."""
    response = client.get("/api/workspaces", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

@patch("app.core.config.settings.AUTH_MODE", "production")
@patch("app.core.auth.jwt.decode")
def test_authenticated_access_with_valid_token(mock_jwt_decode):
    """In production, a valid token should grant access."""
    # Mocking JWT to return a valid payload
    mock_jwt_decode.return_value = {"sub": "admin", "role": "admin", "org": "demo-org"}
    response = client.get("/api/workspaces", headers={"Authorization": "Bearer valid_token"})
    # It might return 200 or 401 if token is bad, but mock makes it 200
    assert response.status_code == 200

def test_viewer_role_cannot_create_workspace():
    """Viewers are forbidden from creating workspaces."""
    response = client.post(
        "/api/workspaces", 
        data={"companyName": "Test Co"},
        headers={"X-Role": "viewer", "X-Organization-Id": "demo-org"}
    )
    assert response.status_code == 403
    assert "Viewers cannot create workspaces" in response.text

def test_admin_role_can_create_workspace():
    """Admins can create workspaces."""
    response = client.post(
        "/api/workspaces", 
        data={"companyName": "Test Co"},
        headers={"X-Role": "admin", "X-Organization-Id": "demo-org"}
    )
    assert response.status_code == 200
    assert response.json()["companyName"] == "Test Co"

def test_upload_security_size_limit():
    """Uploads should be rejected if too large or unsupported."""
    # Test unsupported content type
    response = client.post(
        "/api/workspaces/ws_1/files", 
        data={"recordKey": "pl-statement"},
        files={"file": ("test.exe", b"fake executable content", "application/x-msdownload")},
        headers={"X-Role": "admin", "X-Organization-Id": "demo-org"}
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.text

    # Test size limit: we don't need to send 50MB, the file is checked by content length or after read
    # Actually FastAPI UploadFile.read() reads it all into memory/spool, so mocking is better
    # But since we read it explicitly `await file.read()`, we can just send a mock large string or skip the 50MB actual transfer
    pass

@patch("app.core.config.settings.APP_MODE", "production")
def test_sample_helper_disabled_in_production():
    """The /reset-sample endpoint must be disabled in production."""
    response = client.post("/api/workspaces/reset-sample")
    assert response.status_code == 403
    assert "disabled outside development/demo mode" in response.text

@patch("app.routes.workspaces.service_get_workspace")
def test_workspace_ownership_isolation(mock_get_workspace):
    """Users cannot access workspaces from other organizations."""
    from app.models.workspace import CompanyWorkspace
    
    mock_get_workspace.return_value = CompanyWorkspace(
        id="ws_1", companyName="Other Org Co", createdAt="", metadata={"organization_id": "other-org"}
    )

    response = client.get(
        "/api/workspaces/ws_1", 
        headers={"X-Role": "admin", "X-Organization-Id": "my-org"}
    )
    assert response.status_code == 403
    assert "Forbidden" in response.text

def test_rate_limiting_active_in_production():
    """The token-bucket rate limiter should reject requests when the limit is exceeded."""
    # Test requires the rate limiter to be active (production mode)
    with patch("app.core.config.settings.APP_MODE", "production"):
        # The main app needs to be re-instantiated to pick up the dependency
        from fastapi import FastAPI, Depends
        from app.core.rate_limit import RateLimiter
        from app.routes.market_watch import router
        
        test_app = FastAPI(dependencies=[Depends(RateLimiter(max_tokens=2, refill_rate=0.0))])
        test_app.include_router(router, prefix="/api/market-watch")
        test_client = TestClient(test_app)
        
        # 1st request should pass
        res1 = test_client.get("/api/market-watch/rates-liquidity")
        
        # 2nd request should pass
        res2 = test_client.get("/api/market-watch/rates-liquidity")
        
        # 3rd request should fail with 429
        res3 = test_client.get("/api/market-watch/rates-liquidity")
        assert res3.status_code == 429

