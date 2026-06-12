import logging
from typing import Optional

logger = logging.getLogger(__name__)

"""
PRODUCTION ROADMAP (OIDC/SAML Integration):
The current auth mode relies on local defaults and header overrides for demonstration.
For production cutover:
1. Integrate a real identity provider (e.g., Keycloak, Auth0, PingIdentity).
2. Validate incoming JWTs using FastAPI `Depends(OAuth2PasswordBearer)` or an OIDC middleware.
3. Extract `organization_id`, `user_id`, and `role` claims strictly from the verified JWT payload.
4. Disable `AUTH_ALLOW_HEADER_OVERRIDES`.
5. Ensure no JWT bearer tokens or sensitive claims are logged to stdout/telemetry.
"""

from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel, field_validator

from app.core.config import settings

ALLOWED_ROLES = ("admin", "analyst", "viewer")


class RequestContext(BaseModel):
    organization_id: str
    user_id: str
    role: str
    auth_mode: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized_role = (value or "").strip().lower()
        if normalized_role not in ALLOWED_ROLES:
            allowed_roles = ", ".join(ALLOWED_ROLES)
            raise ValueError(f"role must be one of: {allowed_roles}")
        return normalized_role


def _resolve_auth_value(header_value: Optional[str], default_value: str) -> str:
    candidate = header_value if header_value is not None else default_value
    value = (candidate or "").strip()
    if value:
        return value
    return default_value


def get_request_context(
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> RequestContext:
    allow_header_overrides = (
        settings.normalized_auth_mode == "local" and settings.AUTH_ALLOW_HEADER_OVERRIDES
    )

    organization_id = settings.AUTH_DEFAULT_ORGANIZATION_ID
    user_id = settings.AUTH_DEFAULT_USER_ID
    role = settings.AUTH_DEFAULT_ROLE

    if allow_header_overrides:
        organization_id = _resolve_auth_value(
            x_organization_id,
            settings.AUTH_DEFAULT_ORGANIZATION_ID,
        )
        user_id = _resolve_auth_value(
            x_user_id,
            settings.AUTH_DEFAULT_USER_ID,
        )
        role = _resolve_auth_value(
            x_role,
            settings.AUTH_DEFAULT_ROLE,
        )

    try:
        ctx = RequestContext(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            auth_mode=settings.normalized_auth_mode,
        )
        
        # Safely log request context initialization.
        # Do not log raw headers, bearer tokens, or PII claims.
        logger.debug(
            f"Context resolved: org={ctx.organization_id}, user={ctx.user_id}, role={ctx.role}, mode={ctx.auth_mode}"
        )
        return ctx
    except ValueError as exc:
        logger.warning(f"Invalid context values rejected: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def require_role(role: str):
    def dependency(context: RequestContext = Depends(get_request_context)) -> RequestContext:
        if context.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required.",
            )
        return context
    return dependency


def require_any_role(*roles: str):
    def dependency(context: RequestContext = Depends(get_request_context)) -> RequestContext:
        if context.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {roles} required.",
            )
        return context
    return dependency


def require_write_access(context: RequestContext = Depends(get_request_context)) -> RequestContext:
    if context.role not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access required for this action.",
        )
    return context


def require_admin(context: RequestContext = Depends(get_request_context)) -> RequestContext:
    if context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this action.",
        )
    return context

