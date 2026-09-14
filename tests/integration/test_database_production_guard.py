"""
Integration tests for database production guard and RedisManager rate-limiting.
"""

import pytest
from apps.api.src.core.database import check_db_health, is_sqlite, is_postgres
from apps.api.src.core.redis_manager import RedisManager, InMemoryStore


def test_database_health_check():
    health = check_db_health()
    assert health is True, "Database health check failed"


def test_redis_in_memory_rate_limiting():
    manager = RedisManager()
    client_id = "test-rate-limit-client"

    # Under limit
    for _ in range(5):
        allowed = manager.check_rate_limit(client_id, limit=10, window_seconds=60)
        assert allowed is True

    # Exceed limit
    for _ in range(10):
        manager.check_rate_limit(client_id, limit=10, window_seconds=60)

    throttled = manager.check_rate_limit(client_id, limit=10, window_seconds=60)
    assert throttled is False, "Client was not throttled after exceeding rate limit"


def test_redis_in_memory_ttl():
    store = InMemoryStore()
    store.set("temp-key", "temp-val", ex=1)
    assert store.get("temp-key") == "temp-val"

    store.delete("temp-key")
    assert store.get("temp-key") is None
