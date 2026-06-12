"""Tests for the queue backend implementations."""

import pytest
from app.queue.in_process import InProcessQueue
from app.queue.redis_backend import RedisBackedQueue


@pytest.mark.asyncio
async def test_in_process_enqueue_dequeue():
    q = InProcessQueue()
    task_id = await q.enqueue({"type": "test", "data": 42})
    assert task_id is not None

    envelope = await q.dequeue(timeout=1.0)
    assert envelope is not None
    assert envelope["payload"]["type"] == "test"


@pytest.mark.asyncio
async def test_in_process_dequeue_timeout():
    q = InProcessQueue()
    result = await q.dequeue(timeout=0.1)
    assert result is None


@pytest.mark.asyncio
async def test_in_process_ack_nack():
    q = InProcessQueue()
    task_id = await q.enqueue("hello")
    await q.dequeue(timeout=1.0)
    assert await q.ack(task_id) is True
    assert await q.nack(task_id) is True


@pytest.mark.asyncio
async def test_in_process_length():
    q = InProcessQueue()
    assert await q.length() == 0
    await q.enqueue("a")
    await q.enqueue("b")
    assert await q.length() == 2


@pytest.mark.asyncio
async def test_in_process_flush():
    q = InProcessQueue()
    await q.enqueue(1)
    await q.enqueue(2)
    flushed = await q.flush()
    assert flushed == 2
    assert await q.length() == 0


# Redis-backed queue tests (uses fallback when Redis is unavailable)


@pytest.mark.asyncio
async def test_redis_backed_fallback_enqueue_dequeue():
    """When Redis is unavailable, RedisBackedQueue falls back to in-process."""
    q = RedisBackedQueue(redis_url="redis://127.0.0.1:16379/0")  # unlikely port
    task_id = await q.enqueue("fallback-task")
    assert task_id is not None

    envelope = await q.dequeue(timeout=1.0)
    assert envelope is not None
    # In fallback mode, envelope is the raw dict (no json serialization)
    payload = envelope.get("payload", envelope)
    assert "fallback" in str(payload)


@pytest.mark.asyncio
async def test_redis_backed_length_flush():
    q = RedisBackedQueue(redis_url="redis://127.0.0.1:16379/0")
    await q.enqueue("a")
    await q.enqueue("b")
    assert await q.length() == 2
    flushed = await q.flush()
    assert flushed == 2
    assert await q.length() == 0
