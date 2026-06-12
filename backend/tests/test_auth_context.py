from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import (
    get_request_context,
    require_role,
    require_any_role,
    require_write_access,
    require_admin,
)
from app.core.config import settings


app = FastAPI()


@app.get("/request-context")
def read_request_context(request_context=Depends(get_request_context)):
    return request_context.model_dump()


@app.get("/require-role-admin")
def check_require_role_admin(context=Depends(require_role("admin"))):
    return {"status": "ok", "role": context.role}


@app.get("/require-any-role")
def check_require_any_role(context=Depends(require_any_role("admin", "analyst"))):
    return {"status": "ok", "role": context.role}


@app.get("/require-write-access")
def check_require_write_access(context=Depends(require_write_access)):
    return {"status": "ok", "role": context.role}


@app.get("/require-admin")
def check_require_admin(context=Depends(require_admin)):
    return {"status": "ok", "role": context.role}


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


def test_require_role():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES
    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True

    try:
        # admin should pass
        res_admin = client.get("/require-role-admin", headers={"X-Role": "admin"})
        assert res_admin.status_code == 200
        assert res_admin.json() == {"status": "ok", "role": "admin"}

        # analyst should be forbidden
        res_analyst = client.get("/require-role-admin", headers={"X-Role": "analyst"})
        assert res_analyst.status_code == 403

        # viewer should be forbidden
        res_viewer = client.get("/require-role-admin", headers={"X-Role": "viewer"})
        assert res_viewer.status_code == 403
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides


def test_require_any_role():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES
    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True

    try:
        # admin should pass
        res_admin = client.get("/require-any-role", headers={"X-Role": "admin"})
        assert res_admin.status_code == 200

        # analyst should pass
        res_analyst = client.get("/require-any-role", headers={"X-Role": "analyst"})
        assert res_analyst.status_code == 200

        # viewer should be forbidden
        res_viewer = client.get("/require-any-role", headers={"X-Role": "viewer"})
        assert res_viewer.status_code == 403
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides


def test_require_write_access():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES
    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True

    try:
        # admin should pass
        res_admin = client.get("/require-write-access", headers={"X-Role": "admin"})
        assert res_admin.status_code == 200

        # analyst should pass
        res_analyst = client.get("/require-write-access", headers={"X-Role": "analyst"})
        assert res_analyst.status_code == 200

        # viewer should be forbidden
        res_viewer = client.get("/require-write-access", headers={"X-Role": "viewer"})
        assert res_viewer.status_code == 403
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides


def test_require_admin():
    original_auth_mode = settings.AUTH_MODE
    original_allow_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES
    settings.AUTH_MODE = "local"
    settings.AUTH_ALLOW_HEADER_OVERRIDES = True

    try:
        # admin should pass
        res_admin = client.get("/require-admin", headers={"X-Role": "admin"})
        assert res_admin.status_code == 200

        # analyst should be forbidden
        res_analyst = client.get("/require-admin", headers={"X-Role": "analyst"})
        assert res_analyst.status_code == 403

        # viewer should be forbidden
        res_viewer = client.get("/require-admin", headers={"X-Role": "viewer"})
        assert res_viewer.status_code == 403
    finally:
        settings.AUTH_MODE = original_auth_mode
        settings.AUTH_ALLOW_HEADER_OVERRIDES = original_allow_overrides
