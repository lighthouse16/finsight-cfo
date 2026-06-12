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

        # Rule 4: If APP_MODE == "production", JWT_SECRET_KEY must be set
        if not getattr(settings, "JWT_SECRET_KEY", ""):
            raise RuntimeError("JWT_SECRET_KEY must be set in production mode.")
