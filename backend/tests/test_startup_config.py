import pytest
from app.core.config import Settings
from app.core.startup_checks import validate_startup_config

def test_development_defaults_pass():
    """
    Verifies that the default development configuration passes startup checks.
    """
    settings = Settings(
        APP_MODE="development",
        ALLOW_DEMO_FALLBACK=True,
        MARKET_WATCH_USE_FIXTURES=True,
        CORS_ALLOW_ORIGINS="http://localhost:5173"
    )
    # Should not raise any exception
    validate_startup_config(settings)

def test_valid_production_config_passes():
    """
    Verifies that a valid production configuration passes startup checks.
    """
    settings = Settings(
        APP_MODE="production",
        ALLOW_DEMO_FALLBACK=False,
        MARKET_WATCH_USE_FIXTURES=False,
        CORS_ALLOW_ORIGINS="http://localhost:5173,https://my-production-app.com",
        AUTH_SECRET="super-secret-key-32-chars-long"
    )
    # Should not raise any exception
    validate_startup_config(settings)

def test_production_with_demo_fallback_fails():
    """
    Verifies that production mode fails if ALLOW_DEMO_FALLBACK is True.
    """
    settings = Settings(
        APP_MODE="production",
        ALLOW_DEMO_FALLBACK=True,
        MARKET_WATCH_USE_FIXTURES=False,
        CORS_ALLOW_ORIGINS="http://localhost:5173,https://my-production-app.com",
        AUTH_SECRET="super-secret-key-32-chars-long"
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "ALLOW_DEMO_FALLBACK must be false in production mode" in str(exc_info.value)

def test_production_with_market_fixtures_fails():
    """
    Verifies that production mode fails if MARKET_WATCH_USE_FIXTURES is True.
    """
    settings = Settings(
        APP_MODE="production",
        ALLOW_DEMO_FALLBACK=False,
        MARKET_WATCH_USE_FIXTURES=True,
        CORS_ALLOW_ORIGINS="http://localhost:5173,https://my-production-app.com",
        AUTH_SECRET="super-secret-key-32-chars-long"
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "MARKET_WATCH_USE_FIXTURES must be false in production mode" in str(exc_info.value)

def test_empty_cors_origins_fails():
    """
    Verifies that an empty CORS_ALLOW_ORIGINS value raises a RuntimeError.
    """
    settings = Settings(
        APP_MODE="development",
        CORS_ALLOW_ORIGINS=""
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "CORS_ALLOW_ORIGINS cannot be empty" in str(exc_info.value)

def test_cors_origins_parsing_behavior():
    """
    Verifies that CORS origins are parsed correctly, trimming spaces and discarding empty items.
    """
    settings = Settings(
        CORS_ALLOW_ORIGINS=" http://localhost:5173 , , http://127.0.0.1:5173  , "
    )
    assert settings.parsed_cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Should pass startup validation in development mode
    validate_startup_config(settings)

def test_production_cors_only_localhost_fails():
    """
    Verifies that production mode fails if CORS only contains localhost.
    """
    settings = Settings(
        APP_MODE="production",
        ALLOW_DEMO_FALLBACK=False,
        MARKET_WATCH_USE_FIXTURES=False,
        CORS_ALLOW_ORIGINS="http://localhost:5173,http://127.0.0.1:8080",
        AUTH_SECRET="super-secret-key-32-chars-long"
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "CORS_ALLOW_ORIGINS cannot only contain localhost origins" in str(exc_info.value)

def test_production_without_auth_secret_fails():
    """
    Verifies that production mode fails if AUTH_SECRET is empty.
    """
    settings = Settings(
        APP_MODE="production",
        ALLOW_DEMO_FALLBACK=False,
        MARKET_WATCH_USE_FIXTURES=False,
        CORS_ALLOW_ORIGINS="https://my-production-app.com",
        AUTH_SECRET=""
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "AUTH_SECRET must be configured" in str(exc_info.value)

def test_database_persistence_without_url_fails():
    """
    Verifies that if PERSISTENCE_BACKEND is database,DATABASE_URL cannot be empty.
    """
    settings = Settings(
        APP_MODE="development",
        PERSISTENCE_BACKEND="database",
        DATABASE_URL=""
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_config(settings)
    assert "DATABASE_URL must be configured when PERSISTENCE_BACKEND is set to database" in str(exc_info.value)

