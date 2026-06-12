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
        CORS_ALLOW_ORIGINS="http://localhost:5173"
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
        CORS_ALLOW_ORIGINS="http://localhost:5173"
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
        CORS_ALLOW_ORIGINS="http://localhost:5173"
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
    # Should pass startup validation
    validate_startup_config(settings)


def test_env_example_keys_exist_in_settings():
    """
    Verifies that all non-frontend config keys defined in backend/.env.example
    exist as attributes in the Settings class.
    """
    import os
    
    # Path to backend/.env.example relative to this test file
    env_example_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
    assert os.path.exists(env_example_path), f"backend/.env.example not found at {env_example_path}"
    
    # Read the file and extract key names
    keys = []
    with open(env_example_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments, blank lines, or VITE_ keys
            if not line or line.startswith("#") or line.startswith("VITE_"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0].strip()
                keys.append(key)
                
    # Instantiate Settings to check
    settings_instance = Settings()
    for key in keys:
        # Check if attribute exists on Settings (direct or lowercase fallback due to Pydantic mapping)
        assert hasattr(settings_instance, key) or hasattr(settings_instance, key.lower()), f"Settings is missing key: {key} defined in .env.example"


