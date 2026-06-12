import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def validate_startup_config(settings) -> None:
    """
    Validates startup configuration settings for FinSight CFO.
    Raises RuntimeError if any configuration violates security or operational rules.
    """
    # Rule 1: CORS_ALLOW_ORIGINS must not be empty after parsing
    origins = settings.parsed_cors_origins
    if not origins:
        raise RuntimeError("CORS_ALLOW_ORIGINS cannot be empty. API must have defined allowed origins.")

    # Rule 2: If APP_MODE == "production", ALLOW_DEMO_FALLBACK must be false
    if settings.APP_MODE == "production":
        if getattr(settings, "ALLOW_DEMO_FALLBACK", False):
            raise RuntimeError("ALLOW_DEMO_FALLBACK must be false in production mode.")

        # Rule 3: If APP_MODE == "production", MARKET_WATCH_USE_FIXTURES must be false
        if getattr(settings, "MARKET_WATCH_USE_FIXTURES", False):
            raise RuntimeError("MARKET_WATCH_USE_FIXTURES must be false in production mode.")

        # Rule 4: If APP_MODE == "production", CORS_ALLOW_ORIGINS must not only contain localhost
        local_hosts = {"localhost", "127.0.0.1", "[::1]", "::1"}
        is_only_local = True
        for origin in origins:
            if origin == "*":
                is_only_local = False
                break
            try:
                parsed = urlparse(origin)
                hostname = parsed.hostname
                if hostname not in local_hosts:
                    is_only_local = False
                    break
            except Exception:
                is_only_local = False
                break
        if is_only_local:
            raise RuntimeError("CORS_ALLOW_ORIGINS cannot only contain localhost origins in production mode.")

        # Rule 5: If APP_MODE == "production", JWT_SECRET_KEY or AUTH_SECRET must be configured
        jwt_key = getattr(settings, "JWT_SECRET_KEY", "")
        auth_sec = getattr(settings, "AUTH_SECRET", "")
        if (not jwt_key or jwt_key.strip() == "") and (not auth_sec or auth_sec.strip() == ""):
            raise RuntimeError("JWT_SECRET_KEY (or AUTH_SECRET) must be configured in production mode.")

        # Rule 6: Production warnings for runtime security readiness
        if settings.normalized_auth_mode == "local":
            logger.warning("INSECURE: AUTH_MODE is 'local' in production. This is highly unsafe for real data. Replace with real OIDC/SAML.")
        elif settings.normalized_auth_mode == "oidc":
            if not getattr(settings, "OIDC_ISSUER_URL", "") or not getattr(settings, "OIDC_JWKS_URL", ""):
                raise RuntimeError("OIDC_ISSUER_URL and OIDC_JWKS_URL must be configured when AUTH_MODE is 'oidc'.")
        
        if settings.normalized_persistence_backend == "local":
            logger.warning("PRODUCTION RISK: PERSISTENCE_BACKEND is 'local'. Database persistence should be enabled.")
            
        if getattr(settings, "STORAGE_BACKEND", "local") == "local":
            logger.warning("PRODUCTION RISK: STORAGE_BACKEND is 'local'. Object storage should be configured.")

        if not getattr(settings, "REPORT_WORKER_ENABLED", False):
            logger.warning("PRODUCTION RISK: REPORT_WORKER_ENABLED is False. Async report generation will not function.")

        if settings.normalized_queue_backend == "in_process":
            logger.warning("PRODUCTION RISK: QUEUE_BACKEND is 'in_process'. Redis/Celery queue is recommended for production scale.")

    # Rule 7: If PERSISTENCE_BACKEND == "database", DATABASE_URL must not be empty or missing
    if settings.normalized_persistence_backend == "database":
        db_url = getattr(settings, "DATABASE_URL", "")
        if not db_url or db_url.strip() == "":
            raise RuntimeError("DATABASE_URL must be configured when PERSISTENCE_BACKEND is set to database.")
        
        # Check TimescaleDB URL configuration
        timescale_url = getattr(settings, "TIMESCALE_DATABASE_URL", "")
        if not timescale_url or timescale_url.strip() == "":
            logger.warning("PRODUCTION RISK: TIMESCALE_DATABASE_URL is not configured. Falling back to DATABASE_URL.")
