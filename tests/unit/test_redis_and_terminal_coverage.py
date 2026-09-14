"""
Unit tests for RedisManager, Terminal WebSocket streaming, and Telemetry API.
"""

import time
import pytest
from fastapi.testclient import TestClient

from apps.api.src.main import app
from apps.api.src.core.redis_manager import RedisManager

client = TestClient(app)


def test_redis_manager_in_memory_kv():
    rm = RedisManager()
    rm._redis_client = None
    rm.is_connected = False

    # Set and Get
    assert rm.set("test_key", "test_val", ttl_seconds=60) is True
    assert rm.get("test_key") == "test_val"

    # Delete
    assert rm.delete("test_key") is True
    assert rm.get("test_key") is None

    # Health check
    assert rm.check_health() is True


def test_redis_manager_rate_limiting():
    rm = RedisManager()
    rm._redis_client = None
    rm.is_connected = False

    client_id = "test-rate-limit-client"
    # Allow 3 requests per 10 seconds
    assert rm.check_rate_limit(client_id, limit=3, window_seconds=10) is True
    assert rm.check_rate_limit(client_id, limit=3, window_seconds=10) is True
    assert rm.check_rate_limit(client_id, limit=3, window_seconds=10) is True
    # 4th request must be blocked
    assert rm.check_rate_limit(client_id, limit=3, window_seconds=10) is False


def test_telemetry_endpoints():
    # Metrics endpoint
    res_metrics = client.get("/api/v1/telemetry/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert "requests_per_second" in metrics_data
    assert "latency_p50_ms" in metrics_data

    # Logs endpoint
    res_logs = client.get("/api/v1/telemetry/logs")
    assert res_logs.status_code == 200
    logs_data = res_logs.json()
    assert len(logs_data) > 0
    assert "level" in logs_data[0]

    # Traces endpoint
    res_traces = client.get("/api/v1/telemetry/traces")
    assert res_traces.status_code == 200
    traces_data = res_traces.json()
    assert len(traces_data) > 0
    assert "trace_id" in traces_data[0]


def test_terminal_websocket_protocol():
    with client.websocket_connect("/ws/terminal/test-session-term-01") as websocket:
        # Receive initial banner
        banner = websocket.receive_text()
        assert "KubeLabs SRE Shell Environment" in banner

        # Receive prompt
        prompt = websocket.receive_text()
        assert "kubelabs-sandbox" in prompt

        # Send Enter command
        websocket.send_text("\r")
        echo_nl = websocket.receive_text()
        assert echo_nl == "\r\n"
