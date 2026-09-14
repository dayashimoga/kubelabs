"""
Mini Production Applications Library for KubeLabs.
Provides 12 canonical, lightweight, pre-defined multi-tier architectures for
realistic distributed system troubleshooting, chaos injection, and incident response.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from packages.lab_schema import MultiContainerSpec, ContainerNodeSpec


class ServiceNode(BaseModel):
    """Specification of an individual microservice node within a production system."""
    name: str
    role: str
    image: str = "docker.io/library/alpine:latest"
    ports: List[int] = Field(default_factory=list)
    memory_limit: str = "256m"
    cpu_limit: str = "0.5"
    command: Optional[str] = "sleep 86400"
    environment: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    health_path: Optional[str] = "/healthz"


class ProductionApp(BaseModel):
    """Canonical multi-tier application topology."""
    id: str
    name: str
    category: str
    description: str
    services: List[ServiceNode]
    traffic_flow: List[Dict[str, str]]
    supported_faults: List[str]

    def to_multi_container_spec(self) -> MultiContainerSpec:
        """Translates topology into a MultiContainerSpec for EnvironmentBroker deployment."""
        containers = [
            ContainerNodeSpec(
                name=s.name,
                image=s.image,
                ports=[str(p) for p in s.ports] if s.ports else [],
                environment=s.environment,
                command=s.command,
            )
            for s in self.services
        ]
        return MultiContainerSpec(
            network_name="kubelabs-net",
            containers=containers,
        )


class ApplicationLibrary:
    """Registry of prebuilt canonical production architectures."""

    _SYSTEMS: Dict[str, ProductionApp] = {
        "ecommerce-microservices": ProductionApp(
            id="ecommerce-microservices",
            name="E-Commerce OmniStore Microservices",
            category="retail-cloud",
            description="8-tier canonical distributed store with order processing, inventory sync, and ACID payments.",
            services=[
                ServiceNode(name="web-frontend", role="frontend", ports=[80], dependencies=["api-gateway"]),
                ServiceNode(name="api-gateway", role="gateway", ports=[8080], dependencies=["auth-service", "order-service"]),
                ServiceNode(name="auth-service", role="auth", ports=[5000], dependencies=["user-db"]),
                ServiceNode(name="catalog-service", role="catalog", ports=[5001], dependencies=["cache-redis"]),
                ServiceNode(name="order-service", role="orders", ports=[5002], dependencies=["payment-service", "catalog-service"]),
                ServiceNode(name="payment-service", role="payment", ports=[5003], dependencies=["order-db"]),
                ServiceNode(name="cache-redis", role="cache", ports=[6379]),
                ServiceNode(name="order-db", role="database", ports=[5432]),
            ],
            traffic_flow=[
                {"from": "web-frontend", "to": "api-gateway"},
                {"from": "api-gateway", "to": "auth-service"},
                {"from": "api-gateway", "to": "order-service"},
                {"from": "order-service", "to": "catalog-service"},
                {"from": "order-service", "to": "payment-service"},
                {"from": "catalog-service", "to": "cache-redis"},
                {"from": "payment-service", "to": "order-db"},
            ],
            supported_faults=["checkout_latency_spike", "db_pool_exhaustion", "payment_503_storm"],
        ),
        "fintech-payment-pipeline": ProductionApp(
            id="fintech-payment-pipeline",
            name="FinTech Real-Time Ledger & Fraud Pipeline",
            category="banking",
            description="Ultra-low-latency financial transaction pipeline with synchronous fraud validation and double-entry ledger.",
            services=[
                ServiceNode(name="pos-gateway", role="gateway", ports=[8443], dependencies=["fraud-detector"]),
                ServiceNode(name="fraud-detector", role="ml-screening", ports=[8000], dependencies=["ledger-core"]),
                ServiceNode(name="ledger-core", role="ledger", ports=[9000], dependencies=["sql-audit-db", "kafka-bus"]),
                ServiceNode(name="kafka-bus", role="event-stream", ports=[9092]),
                ServiceNode(name="sql-audit-db", role="immutable-store", ports=[5432]),
            ],
            traffic_flow=[
                {"from": "pos-gateway", "to": "fraud-detector"},
                {"from": "fraud-detector", "to": "ledger-core"},
                {"from": "ledger-core", "to": "sql-audit-db"},
                {"from": "ledger-core", "to": "kafka-bus"},
            ],
            supported_faults=["kafka_partition_lag", "ledger_deadlock", "fraud_timeout_cascade"],
        ),
        "streaming-telemetry-stack": ProductionApp(
            id="streaming-telemetry-stack",
            name="Observability Telemetry Pipeline",
            category="observability",
            description="OTel collector feeding high-throughput Kafka ingestion with Prometheus and Grafana dashboards.",
            services=[
                ServiceNode(name="otel-collector", role="collector", ports=[4317, 4318], dependencies=["kafka-ingest"]),
                ServiceNode(name="kafka-ingest", role="buffer", ports=[9092], dependencies=["stream-worker"]),
                ServiceNode(name="stream-worker", role="transformer", ports=[8080], dependencies=["prom-tsdb"]),
                ServiceNode(name="prom-tsdb", role="tsdb", ports=[9090], dependencies=["grafana-dash"]),
                ServiceNode(name="grafana-dash", role="ui", ports=[3000]),
            ],
            traffic_flow=[
                {"from": "otel-collector", "to": "kafka-ingest"},
                {"from": "kafka-ingest", "to": "stream-worker"},
                {"from": "stream-worker", "to": "prom-tsdb"},
                {"from": "grafana-dash", "to": "prom-tsdb"},
            ],
            supported_faults=["cardinality_explosion", "collector_queue_drop", "promql_oom_crash"],
        ),
        "identity-sso-gateway": ProductionApp(
            id="identity-sso-gateway",
            name="Enterprise Zero-Trust IAM & SSO Gateway",
            category="security",
            description="OAuth2/OIDC proxy with Keycloak identity provider, MFA token verification, and audit trail.",
            services=[
                ServiceNode(name="oauth-proxy", role="proxy", ports=[4180], dependencies=["keycloak-idp"]),
                ServiceNode(name="keycloak-idp", role="idp", ports=[8080], dependencies=["postgres-user-db"]),
                ServiceNode(name="mfa-validator", role="mfa", ports=[8081]),
                ServiceNode(name="postgres-user-db", role="user-db", ports=[5432]),
            ],
            traffic_flow=[
                {"from": "oauth-proxy", "to": "keycloak-idp"},
                {"from": "keycloak-idp", "to": "mfa-validator"},
                {"from": "keycloak-idp", "to": "postgres-user-db"},
            ],
            supported_faults=["jwks_cert_expiry", "idp_rate_limited", "ldap_sync_timeout"],
        ),
        "content-delivery-network": ProductionApp(
            id="content-delivery-network",
            name="Multi-Tier Reverse Proxy & Edge Cache",
            category="networking",
            description="Edge Nginx reverse proxy with Varnish caching tier and origin API server.",
            services=[
                ServiceNode(name="edge-nginx", role="reverse-proxy", ports=[80, 443], dependencies=["varnish-cache"]),
                ServiceNode(name="varnish-cache", role="caching-proxy", ports=[6081], dependencies=["origin-api"]),
                ServiceNode(name="origin-api", role="backend-app", ports=[8080]),
            ],
            traffic_flow=[
                {"from": "edge-nginx", "to": "varnish-cache"},
                {"from": "varnish-cache", "to": "origin-api"},
            ],
            supported_faults=["cache_stampede", "tls_handshake_timeout", "origin_502_bad_gateway"],
        ),
        "iot-sensor-ingestion": ProductionApp(
            id="iot-sensor-ingestion",
            name="Industrial IoT Event Stream Processor",
            category="iot",
            description="MQTT broker ingesting telemetry from millions of edge devices into TimescaleDB.",
            services=[
                ServiceNode(name="mqtt-broker", role="mqtt", ports=[1883], dependencies=["ingest-dispatcher"]),
                ServiceNode(name="ingest-dispatcher", role="worker", ports=[8080], dependencies=["timescale-db", "alert-engine"]),
                ServiceNode(name="alert-engine", role="evaluator", ports=[9090]),
                ServiceNode(name="timescale-db", role="time-series-sql", ports=[5432]),
            ],
            traffic_flow=[
                {"from": "mqtt-broker", "to": "ingest-dispatcher"},
                {"from": "ingest-dispatcher", "to": "timescale-db"},
                {"from": "ingest-dispatcher", "to": "alert-engine"},
            ],
            supported_faults=["backpressure_buffer_overflow", "mqtt_socket_leak", "timescale_chunk_lock"],
        ),
        "kubernetes-control-plane": ProductionApp(
            id="kubernetes-control-plane",
            name="Kubernetes Core Control Plane",
            category="kubernetes",
            description="Kube-apiserver, etcd quorum cluster, controller-manager, and scheduler.",
            services=[
                ServiceNode(name="kube-apiserver", role="api", ports=[6443], dependencies=["etcd-node"]),
                ServiceNode(name="etcd-node", role="raft-store", ports=[2379, 2380]),
                ServiceNode(name="kube-scheduler", role="scheduler", ports=[10259], dependencies=["kube-apiserver"]),
                ServiceNode(name="kube-controller-manager", role="controller", ports=[10257], dependencies=["kube-apiserver"]),
            ],
            traffic_flow=[
                {"from": "kube-apiserver", "to": "etcd-node"},
                {"from": "kube-scheduler", "to": "kube-apiserver"},
                {"from": "kube-controller-manager", "to": "kube-apiserver"},
            ],
            supported_faults=["etcd_quorum_loss", "apiserver_cert_expiry", "scheduler_leader_loss"],
        ),
        "service-mesh-istio": ProductionApp(
            id="service-mesh-istio",
            name="Istio Service Mesh with Mutual TLS",
            category="service-mesh",
            description="Envoy sidecar proxies enforcing mTLS, traffic splitting, and circuit breaking between microservices.",
            services=[
                ServiceNode(name="istio-ingressgateway", role="gateway", ports=[80, 443], dependencies=["orders-envoy"]),
                ServiceNode(name="orders-envoy", role="sidecar-proxy", ports=[15001, 15006], dependencies=["payments-envoy"]),
                ServiceNode(name="payments-envoy", role="sidecar-proxy", ports=[15001, 15006]),
            ],
            traffic_flow=[
                {"from": "istio-ingressgateway", "to": "orders-envoy"},
                {"from": "orders-envoy", "to": "payments-envoy"},
            ],
            supported_faults=["mtls_handshake_mismatch", "circuit_breaker_trip", "retry_budget_storm"],
        ),
        "cicd-gitops-pipeline": ProductionApp(
            id="cicd-gitops-pipeline",
            name="GitOps Automated Delivery Engine",
            category="gitops",
            description="Gitea repository triggering container builds, image push, and Argo CD reconciliation.",
            services=[
                ServiceNode(name="git-server", role="vcs", ports=[3000], dependencies=["ci-runner"]),
                ServiceNode(name="ci-runner", role="builder", ports=[8080], dependencies=["image-registry"]),
                ServiceNode(name="image-registry", role="oci-store", ports=[5000], dependencies=["argocd-server"]),
                ServiceNode(name="argocd-server", role="gitops-sync", ports=[8080]),
            ],
            traffic_flow=[
                {"from": "git-server", "to": "ci-runner"},
                {"from": "ci-runner", "to": "image-registry"},
                {"from": "argocd-server", "to": "git-server"},
                {"from": "argocd-server", "to": "image-registry"},
            ],
            supported_faults=["outofsync_loop", "registry_auth_failure", "kustomize_build_failure"],
        ),
        "serverless-event-pipeline": ProductionApp(
            id="serverless-event-pipeline",
            name="Event-Driven Cloud Workload Pipeline",
            category="cloud-architecture",
            description="SQS queue consumer invoking function handlers with DynamoDB persistence and SNS notification.",
            services=[
                ServiceNode(name="queue-broker", role="sqs-bus", ports=[9324], dependencies=["event-worker"]),
                ServiceNode(name="event-worker", role="function-runner", ports=[8080], dependencies=["nosql-table"]),
                ServiceNode(name="nosql-table", role="kv-store", ports=[8000]),
            ],
            traffic_flow=[
                {"from": "queue-broker", "to": "event-worker"},
                {"from": "event-worker", "to": "nosql-table"},
            ],
            supported_faults=["dlq_saturation", "visibility_timeout_loop", "dynamodb_throttling"],
        ),
        "log-aggregation-system": ProductionApp(
            id="log-aggregation-system",
            name="Log Aggregation & Search Cluster",
            category="logging",
            description="Fluent Bit daemon collecting container stdout/stderr shipping to Loki and Alertmanager.",
            services=[
                ServiceNode(name="fluent-bit", role="shipper", ports=[2020], dependencies=["loki-ingest"]),
                ServiceNode(name="loki-ingest", role="log-tsdb", ports=[3100], dependencies=["alertmanager"]),
                ServiceNode(name="alertmanager", role="alerts", ports=[9093]),
            ],
            traffic_flow=[
                {"from": "fluent-bit", "to": "loki-ingest"},
                {"from": "loki-ingest", "to": "alertmanager"},
            ],
            supported_faults=["log_rate_limit_exceeded", "parser_regex_drop", "alert_notification_backoff"],
        ),
        "ml-inference-cluster": ProductionApp(
            id="ml-inference-cluster",
            name="High-Throughput ML Model Serving Fleet",
            category="ai-infrastructure",
            description="Triton inference server receiving batched predictions, querying Redis feature store.",
            services=[
                ServiceNode(name="inference-gateway", role="proxy", ports=[8000], dependencies=["model-serving"]),
                ServiceNode(name="model-serving", role="triton", ports=[8001], dependencies=["feature-store-redis"]),
                ServiceNode(name="feature-store-redis", role="feature-cache", ports=[6379]),
            ],
            traffic_flow=[
                {"from": "inference-gateway", "to": "model-serving"},
                {"from": "model-serving", "to": "feature-store-redis"},
            ],
            supported_faults=["gpu_memory_saturation", "dynamic_batch_timeout", "feature_drift_skew"],
        ),
    }

    @classmethod
    def list_applications(cls) -> List[ProductionApp]:
        """Returns all 12 canonical production applications."""
        return list(cls._SYSTEMS.values())

    @classmethod
    def get_all_apps(cls) -> List[ProductionApp]:
        """Alias for list_applications."""
        return list(cls._SYSTEMS.values())

    @classmethod
    def get_by_id(cls, app_id: str) -> Optional[ProductionApp]:
        """Fetch specific application architecture by ID."""
        return cls._SYSTEMS.get(app_id)
