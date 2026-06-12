import logging
from typing import Optional
import time
import httpx

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

_jwks_cache = None
_jwks_cache_expiry = 0.0

def get_jwks_keys() -> list:
    global _jwks_cache, _jwks_cache_expiry
    now = time.time()
    if _jwks_cache is not None and now < _jwks_cache_expiry:
        return _jwks_cache

    jwks_url = getattr(settings, "OIDC_JWKS_URL", "")
    if not jwks_url:
        issuer = getattr(settings, "OIDC_ISSUER_URL", "")
        if issuer:
            try:
                discovery_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
                resp = httpx.get(discovery_url, timeout=5.0)
                resp.raise_for_status()
                config = resp.json()
                jwks_url = config.get("jwks_uri")
            except Exception as e:
                logger.error(f"Failed OIDC discovery from {issuer}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OIDC provider discovery failed"
                )
        
    if not jwks_url:
        logger.error("OIDC_JWKS_URL or OIDC_ISSUER_URL must be configured for oidc auth mode.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC auth is not properly configured on the server."
        )

    try:
        resp = httpx.get(jwks_url, timeout=5.0)
        resp.raise_for_status()
        jwks = resp.json()
        keys = jwks.get("keys", [])
        _jwks_cache = keys
        _jwks_cache_expiry = now + 86400.0  # cache for 24 hours
        return keys
    except Exception as e:
        logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
        if _jwks_cache is not None:
            logger.warning("Using stale JWKS cache due to fetch failure.")
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve OIDC keys for signature verification"
        )

def verify_oidc_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        logger.warning(f"Unparseable JWT header: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing key ID (kid)")

    keys = get_jwks_keys()
    matching_key = None
    for key in keys:
        if key.get("kid") == kid:
            matching_key = key
            break

    if not matching_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature key not found")

    try:
        payload = jwt.decode(
            token,
            matching_key,
            algorithms=["RS256"],
            audience=settings.OIDC_AUDIENCE or settings.OIDC_CLIENT_ID or None,
            issuer=settings.OIDC_ISSUER_URL or None
        )
        return payload
    except JWTError as e:
        logger.warning(f"OIDC token signature validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

def resolve_oidc_claims(payload: dict) -> RequestContext:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is missing sub claim")
        
    organization_id = None
    for claim in ("org", "organization", "tenant", "organization_id", "tenant_id"):
        val = payload.get(claim)
        if val:
            if isinstance(val, dict):
                organization_id = val.get("id") or val.get("name")
            else:
                organization_id = str(val)
            break
            
    if not organization_id:
        organization_id = settings.AUTH_DEFAULT_ORGANIZATION_ID
        
    role = None
    roles_claim = payload.get("role") or payload.get("roles") or payload.get("groups") or []
    if isinstance(roles_claim, str):
        roles_list = [roles_claim]
    elif isinstance(roles_claim, list):
        roles_list = roles_claim
    else:
        roles_list = []
        
    resource_access = payload.get("resource_access", {})
    if settings.OIDC_CLIENT_ID and settings.OIDC_CLIENT_ID in resource_access:
        client_roles = resource_access[settings.OIDC_CLIENT_ID].get("roles", [])
        roles_list.extend(client_roles)

    normalized_roles = [str(r).strip().lower() for r in roles_list]
    for candidate in ("admin", "analyst", "viewer"):
        if candidate in normalized_roles:
            role = candidate
            break
            
    if not role:
        role = settings.AUTH_DEFAULT_ROLE
        
    try:
        return RequestContext(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            auth_mode="oidc"
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


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
    
    auth_mode = settings.normalized_auth_mode
    
    if auth_mode == "oidc":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = verify_oidc_jwt(token)
        return resolve_oidc_claims(payload)

    if auth_mode == "production":
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
