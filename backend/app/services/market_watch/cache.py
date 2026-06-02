import time
from typing import Any, Dict, Optional

class CacheItem:
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.stored_at = time.time()
        self.expires_at = self.stored_at + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class SimpleCache:
    def __init__(self):
        self._store: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item and not item.is_expired():
            return item.value
        return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = CacheItem(value, ttl_seconds)

    def get_stale(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item:
            return item.value
        return None

# Singleton instance for now
cache = SimpleCache()
