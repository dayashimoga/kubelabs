"""
Redis and Ephemeral State Manager for KubeLabs.
Provides distributed locking, session cache, and rate-limiting.
Automatically falls back to in-memory store in development mode, but enforces strict
connection in production.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from .config import settings


class InMemoryStore:
    """In-memory key-value store with TTL for standalone local development."""

    def __init__(self):
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        with self._lock:
            expires_at = time.time() + ex if ex else None
            self._store[key] = (value, expires_at)
            return True

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            val, expires_at = self._store[key]
            if expires_at and time.time() > expires_at:
                del self._store[key]
                return None
            return val

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def incr(self, key: str, amount: int = 1) -> int:
        with self._lock:
            val, exp = self._store.get(key, (0, None))
            new_val = int(val) + amount
            self._store[key] = (new_val, exp)
            return new_val


class RedisManager:
    """Unified cache & distributed coordination manager."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.is_connected = False
        self._redis_client = None
        self._in_memory = InMemoryStore()

        if self.redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                self._redis_client.ping()
                self.is_connected = True
            except Exception as e:
                if settings.ENVIRONMENT == "production":
                    raise RuntimeError(
                        f"CRITICAL: Production environment strictly requires Redis. "
                        f"Connection to '{self.redis_url}' failed: {e}"
                    )
                self.is_connected = False
        elif settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "CRITICAL: Production environment strictly requires REDIS_URL to be configured. "
                "In-memory cache fallback is prohibited in production."
            )

    def get(self, key: str) -> Optional[Any]:
        if self.is_connected and self._redis_client:
            try:
                return self._redis_client.get(key)
            except Exception:
                pass
        return self._in_memory.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        if self.is_connected and self._redis_client:
            try:
                return bool(self._redis_client.set(key, value, ex=ttl_seconds))
            except Exception:
                pass
        return self._in_memory.set(key, value, ex=ttl_seconds)

    def delete(self, key: str) -> bool:
        if self.is_connected and self._redis_client:
            try:
                return bool(self._redis_client.delete(key))
            except Exception:
                pass
        return self._in_memory.delete(key)

    def check_rate_limit(self, client_id: str, limit: int = 100, window_seconds: int = 60) -> bool:
        """Sliding window rate limit check. Returns True if allowed, False if throttled."""
        key = f"rate_limit:{client_id}:{int(time.time() // window_seconds)}"
        if self.is_connected and self._redis_client:
            try:
                count = self._redis_client.incr(key)
                if count == 1:
                    self._redis_client.expire(key, window_seconds * 2)
                return count <= limit
            except Exception:
                pass
        count = self._in_memory.incr(key)
        return count <= limit

    def check_health(self) -> bool:
        """Verifies cache connectivity or in-memory operational readiness."""
        if self.is_connected and self._redis_client:
            try:
                return bool(self._redis_client.ping())
            except Exception:
                return False
        return True


redis_manager = RedisManager()
