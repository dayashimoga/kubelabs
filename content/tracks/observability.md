# Observability: Metrics, Logs, Traces & OpenTelemetry Curriculum

## 1. What
Observability is the degree to which the internal state of complex distributed systems can be inferred solely from their external telemetry outputs: Metrics (aggregatable numbers), Logs (structured event records), and Traces (request lifecycles through distributed services).

## 2. Why
Modern distributed systems fail in unpredictable, multi-service cascading ways. High cardinality explosions, dropped scrape targets, broken trace context propagation, misconfigured Alertmanager routing, and log buffer overflows blind engineers during high-severity incidents.

## 3. Architecture
```
Application Pods (OTel SDK)
      |
      +---> OTLP (gRPC: 4317 / HTTP: 4318)
      |
      v
[OpenTelemetry Collector (Receivers -> Processors -> Exporters)]
      |
      +---> Metrics ---> [Prometheus / Thanos / Mimir] <---> [Grafana]
      +---> Logs    ---> [Loki / Fluentbit / Vector]   <---> [Grafana]
      +---> Traces  ---> [Tempo / Jaeger]              <---> [Grafana]
                               |
                       [Alertmanager] ---> (PagerDuty / Slack)
```

## 4. Internals
- **Prometheus Metric Types**:
  - `Counter`: Monotonically increasing value (e.g. `http_requests_total`). Evaluated with `rate()` or `increase()`.
  - `Gauge`: Value that goes up and down (e.g. `memory_usage_bytes`, `active_connections`).
  - `Histogram`: Samples observations (usually request durations) into cumulative configurable buckets with `_count` and `_sum`. Evaluated with `histogram_quantile()`.
  - `Summary`: Calculates client-side quantiles.
- **Cardinality Explosion**: When dynamic high-entropy labels (e.g. `user_id`, `email`, `timestamp`, or raw request URL with query parameters) are added to metric labels. Every unique combination of label keys and values creates a new time series in memory, exhausting Prometheus RAM and crashing the TSDB.
- **W3C Trace Context Propagation**: Propagates `traceparent` header (`version-trace_id-parent_id-trace_flags`, e.g. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`) across HTTP/gRPC boundaries to stitch spans into a single waterfall DAG. If an intermediate proxy strips this header, the distributed trace is severed.
- **Alertmanager Routing**: Evaluates alert rules periodically (`evaluation_interval`). Groups alerts (`group_by: ['alertname', 'cluster']`), deduplicates, inhibits secondary alerts (e.g. suppressing pod alerts if node is down), and routes to receivers with `repeat_interval`.

## 5. Commands
- PromQL queries:
  - Error rate %: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
  - P99 latency: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
  - Node memory pressure: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- OpenTelemetry & Prometheus debugging:
  - `curl http://localhost:9090/api/v1/targets` (inspect scrape target health)
  - `curl http://localhost:9090/api/v1/status/tsdb` (find top 10 highest cardinality labels)
  - `amtool alert --alertmanager.url=http://alertmanager:9093` (list active firing alerts)

## 6. Configuration
- Production OpenTelemetry Collector Pipeline (`otel-collector-config.yaml`):
  ```yaml
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

  processors:
    memory_limiter:
      check_interval: 1s
      limit_percentage: 75
      spike_limit_percentage: 20
    batch:
      timeout: 1s
      send_batch_size: 1024
    tail_sampling:
      decision_wait: 10s
      expected_new_traces_per_sec: 2000
      policies:
        - name: drop-healthchecks
          type: string_attribute
          string_attribute:
            key: http.target
            values: ["/healthz", "/metrics"]
            enabled_regex_matching: false
            invert_match: true

  exporters:
    prometheus:
      endpoint: "0.0.0.0:8889"
    otlp/tempo:
      endpoint: "tempo:4317"
      tls:
        insecure: true

  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [memory_limiter, tail_sampling, batch]
        exporters: [otlp/tempo]
      metrics:
        receivers: [otlp]
        processors: [memory_limiter, batch]
        exporters: [prometheus]
  ```

## 7. Hands-on Lab
- **Lab 1: Diagnosing Prometheus Cardinality Explosion**: Investigate Prometheus out-of-memory crash; inspect TSDB top series using `/api/v1/status/tsdb`; discover bad `user_id` label in application metrics; strip label via `metric_relabel_configs`.
- **Lab 2: Broken Trace Context Propagation**: Fix missing HTTP header injection in Go HTTP client to restore broken trace span waterfalls in Jaeger/Tempo.
- **Lab 3: Multi-Tier Alertmanager Routing & Inhibition**: Configure alert inhibition to silence PodCrashLooping alerts when NodeNotReady fires.

## 8. Common Errors
- Prometheus OOMKilled due to high-cardinality label explosion.
- Grafana dashboard showing `No Data` due to mismatched metric names or missing scrape labels.
- Severed trace waterfalls (root span duration does not match child spans).

## 9. Troubleshooting
1. Check Prometheus targets: `http://<prometheus>:9090/targets` (state UP vs DOWN).
2. Check collector logs for dropped data: `otelcol_exporter_enqueue_failed_spans`.
3. Test PromQL query directly in Prometheus Web UI before building Grafana panels.

## 10. Production Design
- Standardize OpenTelemetry Semantic Conventions across all languages.
- Deploy Prometheus Operator with ServiceMonitors and PodMonitors.
- Enforce SLO-based multi-window multi-burn-rate alerting.

## 11. Security
- Sanitize logs and trace attributes at the OTel Collector processor level to scrub PII (passwords, credit cards, tokens).
- Encrypt telemetry transport via mTLS.

## 12. Performance
- Implement tail-based sampling to retain 100% of error and high-latency traces while dropping 99% of normal 200 OK traffic.
- Configure TSDB compaction and retention policies.

## 13. Interview Scenarios
- **Scenario**: Why should you never use `user_id` or `email` as a label in Prometheus metrics?
  - **Answer**: Prometheus stores each unique combination of metric name and key-value label pairs as a separate time-series in its TSDB. If an application with 1,000,000 users records `http_requests_total{user_id="12345"}`, Prometheus must allocate and track 1,000,000 distinct time series in memory. This leads to a cardinality explosion, linear RAM exhaustion, and catastrophic crashing of the Prometheus server. User IDs should be logged in structured logs or trace attributes, not metric labels.
