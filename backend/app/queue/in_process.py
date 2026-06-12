"""
In-process queue backend backed by an asyncio.Queue.

Tasks are stored in memory and lost on process restart.
Suitable for development and single-worker deployments.
"""

import asyncio
import uuid
from typing import Any, Optional

from app.queue.base import BaseQueue


class InProcessQueue(BaseQueue):
    """Simple in-memory async queue implementation."""

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, task: Any, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        envelope = {"task_id": task_id, "payload": task}
        await self._queue.put(envelope)
        return task_id

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Any]:
        try:
            envelope = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            return envelope
        except asyncio.TimeoutError:
            return None

    async def ack(self, task_id: str) -> bool:
        # In-process: tasks are already removed on dequeue; nothing to do.
        return True

    async def nack(self, task_id: str) -> bool:
        # In-process: no re-queue logic; caller must re-enqueue if needed.
        return True

    async def length(self) -> int:
        return self._queue.qsize()

    async def flush(self) -> int:
        count = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        return count
