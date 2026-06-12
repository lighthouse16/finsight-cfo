import pytest
from fastapi import HTTPException
from app.core.auth import RequestContext, get_request_context

def test_request_context_valid_roles():
    ctx = RequestContext(
        organization_id="org1",
        user_id="user1",
        role="admin",
        auth_mode="local"
    )
    assert ctx.role == "admin"
    
    ctx = RequestContext(
        organization_id="org1",
        user_id="user1",
        role="analyst",
        auth_mode="local"
    )
    assert ctx.role == "analyst"

def test_request_context_invalid_role_raises():
    with pytest.raises(ValueError, match="role must be one of: admin, analyst, viewer"):
        RequestContext(
            organization_id="org1",
            user_id="user1",
            role="superhacker",
            auth_mode="local"
        )

def test_get_request_context_invalid_role(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "AUTH_ALLOW_HEADER_OVERRIDES", True)
    
    with pytest.raises(HTTPException) as exc_info:
        get_request_context(
            x_organization_id="org",
            x_user_id="user",
            x_role="invalid_role"
        )
    assert exc_info.value.status_code == 400
    assert "role must be one of" in str(exc_info.value.detail)

def test_get_request_context_fallback_defaults(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "AUTH_ALLOW_HEADER_OVERRIDES", False)
    monkeypatch.setattr(settings, "AUTH_DEFAULT_ROLE", "viewer")
    
    # Even if headers are provided, they should be ignored if overrides are disabled.
    ctx = get_request_context(
        x_organization_id="hacked_org",
        x_user_id="hacked_user",
        x_role="admin"
    )
    assert ctx.role == "viewer"
    assert ctx.organization_id == settings.AUTH_DEFAULT_ORGANIZATION_ID
    assert ctx.user_id == settings.AUTH_DEFAULT_USER_ID
