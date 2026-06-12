"""
Queue backend factory.

Selects the appropriate backend based on the application's
persistence / deployment settings.
"""

from app.core.config import settings
from app.queue.base import BaseQueue
from app.queue.in_process import InProcessQueue


def get_queue_backend() -> BaseQueue:
    """Return the correct queue backend for the current configuration."""
    mode = (settings.APP_MODE or "development").strip().lower()

    if mode == "production":
        # Attempt a Redis-backed queue when running in production.
        from app.queue.redis_backend import RedisBackedQueue

        return RedisBackedQueue()

    # Development, testing, or any unknown mode → in-process.
    return InProcessQueue()


# Module-level singleton so callers can reuse the same instance.
queue_backend: BaseQueue = get_queue_backend()
