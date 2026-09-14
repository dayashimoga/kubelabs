"""
REST API endpoints for real-time telemetry: PromQL metrics, logs, traces, and topology.
"""

import time
import random
from typing import Any, Dict, List
from fastapi import APIRouter

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/metrics")
def get_live_metrics(perturbed: bool = False) -> Dict[str, Any]:
    """Generates real-time metrics time-series point."""
    now = int(time.time())
    if perturbed:
        return {
            "timestamp": now,
            "requests_per_second": round(random.uniform(1200, 1800), 1),
            "error_rate_5xx_percent": round(random.uniform(14.0, 26.5), 2),
            "latency_p50_ms": round(random.uniform(80.0, 140.0), 1),
            "latency_p95_ms": round(random.uniform(800.0, 1400.0), 1),
            "latency_p99_ms": round(random.uniform(3200.0, 5100.0), 1),
            "cpu_utilization_percent": round(random.uniform(85.0, 96.0), 1),
            "memory_usage_mb": round(random.uniform(1800, 2040), 1),
        }
    return {
        "timestamp": now,
        "requests_per_second": round(random.uniform(850, 950), 1),
        "error_rate_5xx_percent": round(random.uniform(0.01, 0.08), 3),
        "latency_p50_ms": round(random.uniform(12.0, 18.0), 1),
        "latency_p95_ms": round(random.uniform(45.0, 65.0), 1),
        "latency_p99_ms": round(random.uniform(110.0, 150.0), 1),
        "cpu_utilization_percent": round(random.uniform(32.0, 44.0), 1),
        "memory_usage_mb": round(random.uniform(620, 740), 1),
    }


@router.get("/logs")
def get_live_logs(service: str = "all", limit: int = 30) -> List[Dict[str, Any]]:
    """Returns streaming structured log items."""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return [
        {"timestamp": now, "level": "INFO", "service": "edge-gateway", "message": "POST /api/v2/checkout HTTP/2.0 status=504 upstream_time=5.002s"},
        {"timestamp": now, "level": "WARN", "service": "checkout-service", "message": "Downstream RPC to inventory-service timed out after 5000ms"},
        {"timestamp": now, "level": "ERROR", "service": "checkout-service", "message": "org.springframework.web.client.ResourceAccessException: I/O error on POST request for 'http://inventory-service/reserve': Read timed out"},
        {"timestamp": now, "level": "INFO", "service": "payment-service", "message": "GET /healthz 200 OK 2ms"},
        {"timestamp": now, "level": "ERROR", "service": "inventory-service", "message": "HikariPool-1 - Connection is not available, request timed out after 30000ms (Active: 50/50, Idle: 0)"},
    ]


@router.get("/traces")
def get_live_traces() -> List[Dict[str, Any]]:
    """Returns distributed trace spans with waterfall durations."""
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    return [
        {
            "trace_id": trace_id,
            "span_id": "span-1",
            "parent_id": None,
            "service": "edge-gateway",
            "operation": "POST /api/v2/checkout",
            "duration_ms": 5012,
            "status": "ERROR",
            "tags": {"http.status_code": 504, "http.flavor": "2.0"},
        },
        {
            "trace_id": trace_id,
            "span_id": "span-2",
            "parent_id": "span-1",
            "service": "checkout-service",
            "operation": "OrderController.createOrder",
            "duration_ms": 5008,
            "status": "ERROR",
            "tags": {"error": True, "error.message": "downstream read timeout"},
        },
        {
            "trace_id": trace_id,
            "span_id": "span-3",
            "parent_id": "span-2",
            "service": "inventory-service",
            "operation": "InventoryClient.reserveSKU",
            "duration_ms": 5000,
            "status": "ERROR",
            "tags": {"error": True, "error.type": "SocketTimeoutException"},
        },
        {
            "trace_id": trace_id,
            "span_id": "span-4",
            "parent_id": "span-3",
            "service": "postgres",
            "operation": "SELECT * FROM inventory_items FOR UPDATE",
            "duration_ms": 4995,
            "status": "ERROR",
            "tags": {"db.statement": "SELECT * FROM inventory_items ...", "db.error": "lock wait timeout exceeded"},
        },
    ]
