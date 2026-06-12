"""
Abstract base class for task queue backends.

All queue implementations must inherit from BaseQueue and implement
the core enqueue/dequeue lifecycle.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseQueue(ABC):
    """Abstract task queue backend."""

    @abstractmethod
    async def enqueue(self, task: Any, **kwargs) -> str:
        """Push a task onto the queue and return a unique task ID."""

    @abstractmethod
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Pop the next available task (block up to *timeout* seconds)."""

    @abstractmethod
    async def ack(self, task_id: str) -> bool:
        """Mark a task as successfully processed."""

    @abstractmethod
    async def nack(self, task_id: str) -> bool:
        """Mark a task as failed / requeue."""

    @abstractmethod
    async def length(self) -> int:
        """Return the current number of pending tasks."""

    @abstractmethod
    async def flush(self) -> int:
        """Remove all pending tasks and return the count removed."""
