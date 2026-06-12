"""Tests for the Prometheus /metrics endpoint."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    """The /metrics endpoint returns Prometheus-format text."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_contains_default_metrics():
    """The /metrics output contains at least some expected metric names."""
    response = client.get("/metrics")
    text = response.text
    # Python process metrics from prometheus_client are always present
    assert "python_info" in text


def test_metrics_include_finsight_prefix():
    """Custom finsight_ prefixed metrics are present."""
    response = client.get("/metrics")
    text = response.text
    assert "finsight_http_requests_total" in text
    assert "finsight_active_tasks" in text
    assert "finsight_request_duration_seconds" in text
    assert "finsight_queue_depth" in text
