"""Shared fixtures for queue-rate-limit-metrics tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client_factory():
    """Return a callable that creates a fresh TestClient for the app."""
    def _make_client():
        return TestClient(app)
    return _make_client
