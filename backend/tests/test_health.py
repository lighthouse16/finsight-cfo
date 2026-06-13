from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "finsight-cfo-api"


def test_readiness():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_runtime_status_safe_defaults():
    from app.core.config import Settings

    safe_settings = Settings(
        APP_MODE="development",
        PERSISTENCE_BACKEND="local",
        AUTH_MODE="local",
        STORAGE_BACKEND="local",
        REPORT_WORKER_ENABLED=False,
        OPENAI_API_KEY="",
        AZURE_OPENAI_API_KEY="",
    )

    with patch("app.main.get_settings", return_value=safe_settings):
        response = client.get("/api/runtime/status")
    assert response.status_code == 200
    data = response.json()

    # Ensure no secrets leak
    assert "ALPHA_VANTAGE_API_KEY" not in str(data)

    assert data["app_mode"] == "development"
    assert data["persistence_backend"] == "local"
    assert data["auth_mode"] == "local"
    assert "disclaimers" in data
    assert len(data["warnings"]) == 0  # No warnings in development mode


def test_runtime_status_production_warnings():
    from app.core.config import Settings

    # Create a Settings instance with production values
    prod_settings = Settings(
        APP_MODE="production",
        PERSISTENCE_BACKEND="local",
        AUTH_MODE="local",
        STORAGE_BACKEND="local",
        REPORT_WORKER_ENABLED=False,
        OPENAI_API_KEY="",
        AZURE_OPENAI_API_KEY="",
        GOOGLE_API_KEY="",
    )
    with patch("app.main.get_settings", return_value=prod_settings):
        response = client.get("/api/runtime/status")
    assert response.status_code == 200
    data = response.json()

    # In production, local auth and persistence trigger warnings
    warnings = data["warnings"]
    assert any("Auth mode is 'local' in production" in w for w in warnings)
    assert any("Persistence backend is 'local'" in w for w in warnings)
    assert any("Storage backend is 'local'" in w for w in warnings)
    assert any("Report worker is disabled" in w for w in warnings)
    assert any("AI LLM provider is not configured" in w for w in warnings)
