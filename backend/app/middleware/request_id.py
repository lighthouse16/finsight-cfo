"""
Middleware that attaches a unique X-Request-ID header to every response.

If the incoming request already carries an X-Request-ID it is forwarded;
otherwise a new UUID is generated.
"""

import uuid
from app.core.config import settings


async def request_id_middleware(request, call_next):
    """ASGI middleware that ensures every response has an X-Request-ID."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
