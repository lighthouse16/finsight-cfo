import logging

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

        # Rule 4: Production guardrails for runtime security readiness
        if settings.normalized_auth_mode == "local":
            logger.warning("INSECURE: AUTH_MODE is 'local' in production. This is highly unsafe for real data. Replace with real OIDC/SAML.")
        
        if settings.normalized_persistence_backend == "local":
            logger.warning("PRODUCTION RISK: PERSISTENCE_BACKEND is 'local'. Database persistence should be enabled.")
            
        if getattr(settings, "STORAGE_BACKEND", "local") == "local":
            logger.warning("PRODUCTION RISK: STORAGE_BACKEND is 'local'. Object storage should be configured.")

        if not getattr(settings, "REPORT_WORKER_ENABLED", False):
            logger.warning("PRODUCTION RISK: REPORT_WORKER_ENABLED is False. Async report generation will not function.")
