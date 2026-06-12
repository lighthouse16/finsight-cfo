import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
import asyncio

# A simple in-memory store for rate limiting. 
# Key: str (IP address or user identifier)
# Value: Tuple[float, int] (last_refill_time, current_tokens)
_rate_limits: Dict[str, Tuple[float, int]] = {}
_lock = asyncio.Lock()

class RateLimiter:
    """
    A simple token-bucket rate limiter dependency for FastAPI.
    """
    def __init__(self, max_tokens: int = 100, refill_rate: float = 1.0):
        # max_tokens: maximum burst capacity
        # refill_rate: tokens added per second
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate

    async def __call__(self, request: Request):
        # Use client IP as the key, or fallback to something generic
        client_ip = request.client.host if request.client else "unknown"
        key = client_ip

        async with _lock:
            now = time.time()
            if key not in _rate_limits:
                _rate_limits[key] = (now, self.max_tokens - 1)
                return True

            last_time, tokens = _rate_limits[key]
            
            # Refill tokens based on time passed
            time_passed = now - last_time
            new_tokens = min(self.max_tokens, tokens + int(time_passed * self.refill_rate))
            
            if new_tokens > 0:
                _rate_limits[key] = (now, new_tokens - 1)
                return True
            else:
                _rate_limits[key] = (now, 0)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests"
                )
