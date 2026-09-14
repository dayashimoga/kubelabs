"""
Realistic Multi-Tier Microservices Topology for Production Incidents.
Defines the canonical 6-tier architecture:
frontend (React/Nginx) -> gateway (Envoy) -> auth / catalog / checkout / payment -> Redis & PostgreSQL.
"""

from typing import Dict, Any, List


def get_production_microservices_topology() -> Dict[str, Any]:
    """Return topology nodes and edges for the enterprise microservice system."""
    nodes = [
        {"id": "ingress-lb", "label": "AWS ALB / Cloud LB", "type": "alb", "status": "healthy"},
        {"id": "frontend", "label": "web-frontend (React/Nginx)", "type": "service", "status": "healthy"},
        {"id": "api-gateway", "label": "api-gateway (Envoy/Kong)", "type": "gateway", "status": "healthy"},
        {"id": "auth-service", "label": "auth-service (OAuth2/JWT)", "type": "service", "status": "healthy"},
        {"id": "catalog-service", "label": "catalog-service (gRPC)", "type": "service", "status": "healthy"},
        {"id": "checkout-service", "label": "checkout-service (HTTP)", "type": "service", "status": "healthy"},
        {"id": "payment-service", "label": "payment-service (Stripe API)", "type": "service", "status": "healthy"},
        {"id": "redis-cache", "label": "redis-session-cluster", "type": "cache", "status": "healthy"},
        {"id": "postgres-db", "label": "postgresql-primary (RDS)", "type": "database", "status": "healthy"},
    ]

    edges = [
        {"source": "ingress-lb", "target": "frontend", "protocol": "https", "status": "normal"},
        {"source": "frontend", "target": "api-gateway", "protocol": "http", "status": "normal"},
        {"source": "api-gateway", "target": "auth-service", "protocol": "http", "status": "normal"},
        {"source": "api-gateway", "target": "catalog-service", "protocol": "grpc", "status": "normal"},
        {"source": "api-gateway", "target": "checkout-service", "protocol": "http", "status": "normal"},
        {"source": "checkout-service", "target": "payment-service", "protocol": "http", "status": "normal"},
        {"source": "auth-service", "target": "redis-cache", "protocol": "tcp", "status": "normal"},
        {"source": "checkout-service", "target": "postgres-db", "protocol": "tcp", "status": "normal"},
        {"source": "catalog-service", "target": "postgres-db", "protocol": "tcp", "status": "normal"},
    ]

    return {"nodes": nodes, "edges": edges}


def get_correlated_trace(trace_id: str, duration_ms: float = 350.0, error: bool = False) -> Dict[str, Any]:
    """Generate correlated distributed trace spans matching the microservice topology."""
    return {
        "trace_id": trace_id,
        "duration_ms": duration_ms,
        "spans": [
            {
                "span_id": "span-01",
                "parent_id": None,
                "service": "api-gateway",
                "name": "POST /api/v1/checkout",
                "start_time_offset_ms": 0,
                "duration_ms": duration_ms,
                "status": "ERROR" if error else "OK",
            },
            {
                "span_id": "span-02",
                "parent_id": "span-01",
                "service": "auth-service",
                "name": "VerifyJWTToken",
                "start_time_offset_ms": 5,
                "duration_ms": 25,
                "status": "OK",
            },
            {
                "span_id": "span-03",
                "parent_id": "span-01",
                "service": "checkout-service",
                "name": "ProcessOrder",
                "start_time_offset_ms": 32,
                "duration_ms": duration_ms - 40,
                "status": "ERROR" if error else "OK",
            },
            {
                "span_id": "span-04",
                "parent_id": "span-03",
                "service": "payment-service",
                "name": "ChargeCard",
                "start_time_offset_ms": 50,
                "duration_ms": duration_ms - 70,
                "status": "ERROR" if error else "OK",
            },
        ],
    }
