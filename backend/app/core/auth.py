from typing import Optional

from fastapi import Header, HTTPException, status
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
        return RequestContext(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            auth_mode=settings.normalized_auth_mode,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

