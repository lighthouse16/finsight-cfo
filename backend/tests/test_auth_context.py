from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_request_context
from app.core.config import settings


app = FastAPI()


@app.get("/request-context")
def read_request_context(request_context=Depends(get_request_context)):
    return request_context.model_dump()


client = TestClient(app)


def test_default_local_request_context_uses_demo_values():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES
    original_org_id = settings.AUTH_DEFAULT_ORGANIZATION_ID
    original_user_id = settings.AUTH_DEFAULT_USER_ID
    original_role = settings.AUTH_DEFAULT_ROLE

    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True
    settings.AUTH_DEFAULT_ORGANIZATION_ID = "demo-org"
    settings.AUTH_DEFAULT_USER_ID = "demo-user"
    settings.AUTH_DEFAULT_ROLE = "admin"

    try:
        response = client.get("/request-context")
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides
        settings.AUTH_DEFAULT_ORGANIZATION_ID = original_org_id
        settings.AUTH_DEFAULT_USER_ID = original_user_id
        settings.AUTH_DEFAULT_ROLE = original_role

    assert response.status_code == 200
    assert response.json() == {
        "organization_id": "demo-org",
        "user_id": "demo-user",
        "role": "admin",
        "auth_mode": "local",
    }


def test_invalid_role_header_is_rejected():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES

    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True

    try:
        response = client.get(
            "/request-context",
            headers={"X-Role": "super-admin"},
        )
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides

    assert response.status_code == 400
    assert "role must be one of: admin, analyst, viewer" in response.json()["detail"]
