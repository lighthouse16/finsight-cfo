from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator
from jose import JWTError, jwt

from app.core.config import settings

ALLOWED_ROLES = ("admin", "analyst", "viewer")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

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
    token: Optional[str] = Depends(oauth2_scheme),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> RequestContext:
    
    is_production = settings.normalized_auth_mode == "production"
    
    if is_production:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            role: str = payload.get("role")
            organization_id: str = payload.get("org")
            if user_id is None or role is None or organization_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
            
        try:
            return RequestContext(
                organization_id=organization_id,
                user_id=user_id,
                role=role,
                auth_mode="production",
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Local mode fallback
    allow_header_overrides = settings.AUTH_ALLOW_HEADER_OVERRIDES

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

