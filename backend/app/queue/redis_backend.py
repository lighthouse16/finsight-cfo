"""
Redis-backed task queue backend.

Tasks are stored in a Redis list and processed with a simple
enqueue / dequeue / ack lifecycle.

Gracefully degrades when Redis is unavailable by falling back
to the in-process queue.
"""

import json
import logging
import uuid
from typing import Any, Optional

from app.queue.base import BaseQueue
from app.queue.in_process import InProcessQueue

logger = logging.getLogger(__name__)


class RedisBackedQueue(BaseQueue):
    """Redis-backed queue that falls back to InProcessQueue on connection failure."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        queue_key: str = "finsight:tasks",
        fallback_maxsize: int = 1000,
    ) -> None:
        self._redis_url = redis_url
        self._queue_key = queue_key
        self._fallback_maxsize = fallback_maxsize  # set BEFORE _init_redis
        self._fallback: Optional[InProcessQueue] = None
        self._redis = None
        self._available = False
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            self._available = True
        except Exception as exc:
            logger.warning("Redis unavailable (%s); using in-process fallback", exc)
            self._fallback = InProcessQueue(maxsize=self._fallback_maxsize)
            self._available = False

    async def enqueue(self, task: Any, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        envelope = json.dumps({"task_id": task_id, "payload": task}, default=str)
        if self._available and self._redis:
            try:
                await self._redis.rpush(self._queue_key, envelope)
                return task_id
            except Exception:
                logger.exception("Redis enqueue failed; falling back")
                self._available = False
                self._fallback = InProcessQueue(maxsize=self._fallback_maxsize)
        # Fallback
        return await self._fallback.enqueue(task)

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Any]:
        if self._available and self._redis:
            try:
                result = await self._redis.blpop(self._queue_key, timeout=int(timeout or 0))
                if result:
                    _, raw = result
                    return json.loads(raw)
                return None
            except Exception:
                logger.exception("Redis dequeue failed; falling back")
                self._available = False
                self._fallback = InProcessQueue(maxsize=self._fallback_maxsize)
        return await self._fallback.dequeue(timeout=timeout)

    async def ack(self, task_id: str) -> bool:
        # Redis BLPop removes tasks atomically so ack is a no-op.
        if not self._available:
            return await self._fallback.ack(task_id)
        return True

    async def nack(self, task_id: str) -> bool:
        if not self._available:
            return await self._fallback.nack(task_id)
        # Re-enqueue the task
        try:
            raw = await self._redis.lindex(self._queue_key, -1)
            if raw:
                await self._redis.rpush(self._queue_key, raw)
            return True
        except Exception:
            return False

    async def length(self) -> int:
        if self._available and self._redis:
            try:
                return await self._redis.llen(self._queue_key)
            except Exception:
                return await self._fallback.length()
        return await self._fallback.length()

    async def flush(self) -> int:
        if self._available and self._redis:
            try:
                count = await self._redis.llen(self._queue_key)
                await self._redis.delete(self._queue_key)
                return count
            except Exception:
                pass
        return await self._fallback.flush()
