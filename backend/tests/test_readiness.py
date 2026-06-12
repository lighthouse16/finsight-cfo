import sys
import pytest
from unittest.mock import MagicMock

# Define module-scoped fixture to inject and cleanup the mocked redis module
@pytest.fixture(scope="module", autouse=True)
def mock_redis_module():
    mock_redis = MagicMock()
    sys.modules["redis"] = mock_redis
    yield mock_redis
    if "redis" in sys.modules:
        del sys.modules["redis"]

from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_ready_endpoint_defaults_pass():
    """
    Verifies that the /ready endpoint passes when local persistence and local queue are active.
    """
    with patch.object(settings, "PERSISTENCE_BACKEND", "local"), \
         patch.object(settings, "QUEUE_BACKEND", "local"):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "not_applicable"
        assert data["checks"]["redis"] == "not_applicable"

def test_ready_database_check_success():
    """
    Verifies that /ready succeeds if database persistence is enabled and the DB query executes successfully.
    """
    with patch.object(settings, "PERSISTENCE_BACKEND", "database"), \
         patch.object(settings, "QUEUE_BACKEND", "local"), \
         patch("app.db.session.get_engine") as mock_get_engine:
        
        mock_conn = MagicMock()
        mock_get_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "ok"
        mock_conn.execute.assert_called_once()

def test_ready_database_check_failure():
    """
    Verifies that /ready fails (503) if database connection fails, without leaking details.
    """
    with patch.object(settings, "PERSISTENCE_BACKEND", "database"), \
         patch.object(settings, "QUEUE_BACKEND", "local"), \
         patch("app.db.session.get_engine") as mock_get_engine:
        
        mock_get_engine.return_value.connect.side_effect = Exception("DB Connection Refused")
        
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unready"
        assert data["detail"]["checks"]["database"] == "failed"

def test_ready_redis_check_success(mock_redis_module):
    """
    Verifies that /ready succeeds if Redis queue is active and ping responds.
    """
    with patch.object(settings, "PERSISTENCE_BACKEND", "local"), \
         patch.object(settings, "QUEUE_BACKEND", "redis"):
        
        mock_redis_module.reset_mock()
        mock_client = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_client
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["redis"] == "ok"
        mock_redis_module.Redis.from_url.assert_called_once()
        mock_client.ping.assert_called_once()

def test_ready_redis_check_failure(mock_redis_module):
    """
    Verifies that /ready fails (503) if Redis connection or ping fails.
    """
    with patch.object(settings, "PERSISTENCE_BACKEND", "local"), \
         patch.object(settings, "QUEUE_BACKEND", "redis"):
        
        mock_redis_module.reset_mock()
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Redis connection timed out")
        mock_redis_module.Redis.from_url.return_value = mock_client
        
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unready"
        assert data["detail"]["checks"]["redis"] == "failed"
