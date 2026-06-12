"""Tests for the rate limiting middleware."""

from unittest.mock import patch

from app.core.config import settings
from app.middleware.rate_limit import _ip_buckets, _ws_buckets


def clear_buckets():
    _ip_buckets.clear()
    _ws_buckets.clear()


def test_rate_limit_allows_normal_requests(test_client_factory):
    """Normal requests within limits should pass through."""
    clear_buckets()
    client = test_client_factory()
    response = client.get("/health")
    assert response.status_code == 200


def test_rate_limit_exceeded_returns_429(test_client_factory):
    """
    When the IP bucket is exhausted, the middleware returns 429.

    Set rate=0 so tokens never refill; burst=3 means the 4th
    identical request is blocked.
    """
    clear_buckets()
    with (
        patch.object(settings, "APP_MODE", "production"),
        patch.object(settings, "RATE_LIMIT_IP_RATE", 0.0),
        patch.object(settings, "RATE_LIMIT_IP_BURST", 3.0),
    ):
        client = test_client_factory()

        # Exhaust the burst allowance (3 requests)
        for _ in range(3):
            resp = client.get("/health")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        # 4th request should be rate-limited
        resp = client.get("/health")
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code}"
        data = resp.json()
        assert data["code"] == "RATE_LIMITED_IP"


def test_rate_limit_per_workspace(test_client_factory):
    """Rate limiting by X-Workspace-ID header."""
    clear_buckets()
    with (
        patch.object(settings, "APP_MODE", "production"),
        patch.object(settings, "RATE_LIMIT_WS_RATE", 0.0),
        patch.object(settings, "RATE_LIMIT_WS_BURST", 1.0),
    ):
        client = test_client_factory()
        headers = {"X-Workspace-ID": "test-ws"}

        # First request should pass
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 200

        # Second request should be WS-limited
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 429
        data = resp.json()
        assert data["code"] == "RATE_LIMITED_WS"
