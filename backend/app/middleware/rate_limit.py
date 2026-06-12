"""
Token-bucket rate limiting middleware.

Limits requests per IP address and per Workspace header.
Settings are read dynamically from the application state for testability.

NOTE: Rate limiting is only enforced when APP_MODE == "production".
In development and test modes the middleware passes through without
checking buckets. This avoids leaking rate-limit state into the
shared test suite.
"""

import asyncio
import time
from typing import Dict

from starlette.responses import JSONResponse

from app.core.config import settings

# Per-IP token buckets: {ip: (tokens, last_refill)}
_ip_buckets: Dict[str, list] = {}
# Per-Workspace token buckets: {workspace_id: (tokens, last_refill)}
_ws_buckets: Dict[str, list] = {}

_lock = asyncio.Lock()


def _refill(tokens: float, last_refill: float, rate: float, capacity: float):
    """Refill tokens based on elapsed time since *last_refill*."""
    now = time.monotonic()
    elapsed = now - last_refill
    tokens = min(capacity, tokens + elapsed * rate)
    return tokens, now


async def rate_limit_middleware(request, call_next):
    """
    ASGI middleware that applies token-bucket rate limiting.

    Only enforced in production mode to avoid interfering with
    development and test suites.
    """
    # Only enforce in production
    mode = getattr(settings, "APP_MODE", "development").strip().lower()
    if mode != "production":
        return await call_next(request)

    # Read limits dynamically from settings (allows test patching).
    ip_rate = getattr(settings, "RATE_LIMIT_IP_RATE", 10.0)
    ip_burst = getattr(settings, "RATE_LIMIT_IP_BURST", 20.0)
    ws_rate = getattr(settings, "RATE_LIMIT_WS_RATE", 50.0)
    ws_burst = getattr(settings, "RATE_LIMIT_WS_BURST", 100.0)

    # Determine caller identity
    client_ip = request.client.host if request.client else "unknown"
    workspace_id = request.headers.get("X-Workspace-ID", "")

    async with _lock:
        # --- IP bucket ---
        if client_ip not in _ip_buckets:
            _ip_buckets[client_ip] = [ip_burst, time.monotonic()]
        tokens_ip, last_ip = _ip_buckets[client_ip]
        tokens_ip, last_ip = _refill(tokens_ip, last_ip, ip_rate, ip_burst)
        if tokens_ip < 1:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests", "code": "RATE_LIMITED_IP"},
            )
        _ip_buckets[client_ip] = [tokens_ip - 1, last_ip]

        # --- Workspace bucket ---
        if workspace_id:
            if workspace_id not in _ws_buckets:
                _ws_buckets[workspace_id] = [ws_burst, time.monotonic()]
            tokens_ws, last_ws = _ws_buckets[workspace_id]
            tokens_ws, last_ws = _refill(tokens_ws, last_ws, ws_rate, ws_burst)
            if tokens_ws < 1:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests", "code": "RATE_LIMITED_WS"},
                )
            _ws_buckets[workspace_id] = [tokens_ws - 1, last_ws]

    response = await call_next(request)
    return response
