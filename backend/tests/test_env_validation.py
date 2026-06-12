import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings
from app.core.auth import get_request_context, RequestContext, verify_oidc_jwt, resolve_oidc_claims

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_settings():
    orig_auth_mode = settings.AUTH_MODE
    orig_persistence = settings.PERSISTENCE_BACKEND
    orig_storage = settings.OBJECT_STORAGE_BACKEND
    orig_queue = settings.QUEUE_BACKEND
    orig_db_url = settings.DATABASE_URL
    orig_ts_url = settings.TIMESCALE_DATABASE_URL
    orig_s3_bucket = settings.S3_BUCKET
    orig_oidc_client = settings.OIDC_CLIENT_ID
    yield
    settings.AUTH_MODE = orig_auth_mode
    settings.PERSISTENCE_BACKEND = orig_persistence
    settings.OBJECT_STORAGE_BACKEND = orig_storage
    settings.QUEUE_BACKEND = orig_queue
    settings.DATABASE_URL = orig_db_url
    settings.TIMESCALE_DATABASE_URL = orig_ts_url
    settings.S3_BUCKET = orig_s3_bucket
    settings.OIDC_CLIENT_ID = orig_oidc_client


def test_validate_env_endpoint_role_checks():
    """
    Verifies that validate-production-env requires admin privileges.
    """
    # 1. Non-admin user gets 403
    headers = {"X-User-Id": "test-user", "X-Role": "analyst", "X-Organization-Id": "test-org"}
    response = client.get("/api/admin/validate-production-env", headers=headers)
    assert response.status_code == 403

    # 2. Admin user gets 200
    headers = {"X-User-Id": "admin-user", "X-Role": "admin", "X-Organization-Id": "test-org"}
    response = client.get("/api/admin/validate-production-env", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


@patch("app.routes.env_validation.check_postgres_timescale")
@patch("app.routes.env_validation.check_redis")
@patch("app.routes.env_validation.check_object_storage")
@patch("app.routes.env_validation.check_oidc")
def test_validate_env_endpoint_failed_check(mock_oidc, mock_storage, mock_redis, mock_pg):
    """
    Verifies that if any smoke test fails, the overall status is 'failed'.
    """
    mock_pg.return_value = {"status": "ok", "details": "all good"}
    mock_redis.return_value = {"status": "ok", "details": "all good"}
    mock_storage.value = {"status": "ok", "details": "all good"}
    mock_oidc.return_value = {"status": "failed", "error": "connection failed"}

    # Mock object storage returning ok
    mock_storage.return_value = {"status": "ok", "details": "all good"}

    headers = {"X-User-Id": "admin-user", "X-Role": "admin", "X-Organization-Id": "test-org"}
    response = client.get("/api/admin/validate-production-env", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["checks"]["oidc"]["status"] == "failed"


@patch("app.routes.env_validation.get_engine")
def test_check_postgres_timescale_ok(mock_get_engine):
    """
    Test postgres checks when configured correctly.
    """
    settings.PERSISTENCE_BACKEND = "database"
    settings.DATABASE_URL = "postgresql://localhost/test"
    settings.TIMESCALE_DATABASE_URL = "postgresql://localhost/test"
    
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = ("timescaledb",)
    mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

    from app.routes.env_validation import check_postgres_timescale
    res = check_postgres_timescale()
    assert res["status"] == "ok"
    assert res["timescaledb_active"] is True


@patch("redis.Redis.from_url")
def test_check_redis_ok(mock_redis_from_url):
    """
    Test Redis checks when configured correctly.
    """
    settings.QUEUE_BACKEND = "redis"
    settings.QUEUE_REDIS_URL = "redis://localhost:6379/0"

    mock_client = MagicMock()
    mock_client.get.return_value = b"val"
    mock_redis_from_url.return_value = mock_client

    from app.routes.env_validation import check_redis
    res = check_redis()
    assert res["status"] == "ok"


@patch("boto3.client")
def test_check_s3_unconfigured(mock_boto):
    """
    Test S3 checks when unconfigured returns provider_not_configured.
    """
    settings.OBJECT_STORAGE_BACKEND = "s3"
    settings.S3_BUCKET = "" # missing

    from app.routes.env_validation import check_object_storage
    res = check_object_storage()
    assert res["status"] == "provider_not_configured"


def test_resolve_oidc_claims():
    """
    Tests claim resolution logic.
    """
    payload = {
        "sub": "user_12345",
        "org": "company_abc",
        "role": "analyst"
    }
    ctx = resolve_oidc_claims(payload)
    assert ctx.user_id == "user_12345"
    assert ctx.organization_id == "company_abc"
    assert ctx.role == "analyst"

    # Test keycloak client role mapping
    settings.OIDC_CLIENT_ID = "my-client"
    payload = {
        "sub": "user_12345",
        "resource_access": {
            "my-client": {
                "roles": ["admin", "viewer"]
            }
        }
    }
    ctx = resolve_oidc_claims(payload)
    assert ctx.role == "admin"
