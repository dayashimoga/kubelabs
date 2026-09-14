# KubeLabs Platform Observability & Internal Telemetry

## 1. Platform Telemetry Architecture
KubeLabs instruments its own internal operations using OpenTelemetry and Prometheus standards to ensure complete visibility into container lifecycles, API latencies, and validation accuracy.

## 2. Key Internal Metrics Exposed
Available at `http://localhost:8000/metrics` or `/api/v1/telemetry/metrics`:

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `kubelabs_active_sandboxes` | Gauge | `type="container\|simulator"` | Current number of active sandbox sessions |
| `kubelabs_api_request_duration_seconds`| Histogram | `endpoint, method, status` | API latency distribution |
| `kubelabs_validation_total` | Counter | `status="PASS\|PARTIAL\|FAIL"`| Count of validation executions |
| `kubelabs_sandbox_provision_duration_seconds` | Histogram | `engine="podman"` | Time taken to spin up and stage container |
| `kubelabs_ttl_cleaned_sandboxes_total` | Counter | `reason="expired"` | Number of sandboxes cleaned up by TTL sweeper |

## 3. Structured Logging
All backend logs are formatted in structured JSON via `structlog`:
```json
{
  "timestamp": "2026-09-14T10:20:00Z",
  "level": "INFO",
  "event": "sandbox_provisioned",
  "session_id": "8f3b2a",
  "lab_id": "linux-inode-exhaustion",
  "is_container": true,
  "duration_ms": 420
}
```

## 4. Distributed Tracing
Incoming HTTP and WebSocket requests are traced using OpenTelemetry ASGI middleware. Spans track database queries, Podman CLI executions, and validator evaluations.
