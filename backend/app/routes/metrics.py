"""
Prometheus / OpenMetrics endpoint.

Exports HTTP status counter, active task gauge, and
queue depth histogram via the standard /metrics endpoint.
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from fastapi import APIRouter, Response

router = APIRouter()

# --- Metrics ---

http_requests_total = Counter(
    "finsight_http_requests_total",
    "Total HTTP requests by status code",
    labelnames=["status_code", "method", "path"],
)

active_tasks = Gauge(
    "finsight_active_tasks",
    "Number of tasks currently in-flight",
)

request_duration_seconds = Histogram(
    "finsight_request_duration_seconds",
    "HTTP request duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

queue_depth = Gauge(
    "finsight_queue_depth",
    "Current number of pending tasks in the queue",
)


@router.get("/metrics")
def metrics_endpoint():
    """Return Prometheus-format metrics."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type="text/plain; charset=utf-8")
