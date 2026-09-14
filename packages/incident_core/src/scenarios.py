"""
Comprehensive catalog of 12 production-grade SEV-1/SEV-2 incident scenarios.
"""

from typing import Dict, List
from .models import IncidentSpec, IncidentSeverity, AlertEvent, IncidentHypothesis


INCIDENTS: List[IncidentSpec] = [
    IncidentSpec(
        id="checkout-latency-spike",
        title="Checkout Latency Spike and 504 Gateway Timeouts",
        severity=IncidentSeverity.SEV1,
        summary="Users experiencing checkout button spinning indefinitely with 504 Gateway Timeout responses.",
        impact="Direct customer checkout failure: 42% basket abandonment rate spike on global storefront.",
        initial_symptoms=[
            "P99 latency on /api/v2/checkout increased from 180ms to 4200ms",
            "Elevated 504 responses from edge Cloudflare / ALB",
            "Database CPU is normal (18%), but order-service pod memory is climbing",
        ],
        topology={
            "nodes": [
                {"id": "alb", "label": "AWS ALB Ingress", "type": "alb", "status": "degraded"},
                {"id": "edge", "label": "Edge Envoy Gateway", "type": "gateway", "status": "degraded"},
                {"id": "checkout", "label": "Checkout Service", "type": "service", "status": "failed"},
                {"id": "inventory", "label": "Inventory Service", "type": "service", "status": "slow"},
                {"id": "redis", "label": "Redis Lock Cache", "type": "cache", "status": "healthy"},
                {"id": "aurora", "label": "Amazon Aurora Postgres", "type": "database", "status": "healthy"},
            ],
            "edges": [
                {"source": "alb", "target": "edge", "status": "slow"},
                {"source": "edge", "target": "checkout", "status": "broken"},
                {"source": "checkout", "target": "inventory", "status": "slow"},
                {"source": "checkout", "target": "redis", "status": "normal"},
                {"source": "checkout", "target": "aurora", "status": "normal"},
            ],
        },
        affected_services=["checkout-service", "inventory-service", "api-gateway"],
        root_cause_explanation="Inventory service introduced a synchronous unindexed SKU reservation query during flash sale, causing its thread pool to saturate. Checkout service did not set an HTTP client read timeout on downstream calls to inventory-service, causing its own incoming HTTP worker pool to deadlock waiting on hung sockets.",
        remediation_steps=[
            "Deploy hotfix configuring strict 500ms timeout with circuit breaker fallback on checkout -> inventory client",
            "Add composite index on inventory_items(sku_id, warehouse_id, status)",
            "Restart checkout service deployment to drain stuck thread workers",
        ],
        prevention_measures=[
            "Mandate explicit socket/read timeouts and circuit breakers for all inter-service RPC clients via service mesh",
            "Enforce slow-query linters in CI for all PR database migrations",
            "Set up automated SLO burn alerts on downstream client call latencies",
        ],
        alerts=[
            AlertEvent(
                id="alt-01",
                name="HighHttp5xxErrorRate",
                severity="critical",
                status="firing",
                started_at="2026-09-14T09:42:00Z",
                description="ALB 5xx error rate exceeded 15% threshold for >3 minutes",
                labels={"service": "checkout-service", "cluster": "prod-us-east-1"},
            ),
            AlertEvent(
                id="alt-02",
                name="CheckoutServiceP99LatencyBurnRate",
                severity="critical",
                status="firing",
                started_at="2026-09-14T09:43:10Z",
                description="SLO error budget burning at 14.4x rate (P99 > 3.0s)",
                labels={"service": "checkout-service"},
            ),
        ],
        hypotheses=[
            IncidentHypothesis(
                id="hyp-1",
                statement="Aurora PostgreSQL master instance is undergoing CPU saturation or deadlocks",
                plausible=True,
                evidence_required="Check CloudWatch RDS CPU utilization and pg_stat_activity active locks",
                disproven_by="Aurora CPU is 18%, 0 deadlocks recorded in pg_stat_database",
            ),
            IncidentHypothesis(
                id="hyp-2",
                statement="Downstream Inventory Service is saturating and Checkout Service lacks client timeout",
                plausible=True,
                evidence_required="Inspect checkout-service thread dump and Jaeger trace spans on inventory call",
            ),
        ],
        diagnostic_commands=[
            {"cmd": "kubectl logs -l app=checkout-service --tail=50", "description": "Inspect checkout service container logs"},
            {"cmd": "kubectl get hpa checkout-service", "description": "Check if HPA reached max pods limit"},
            {"cmd": "curl -s http://inventory-service/healthz", "description": "Check inventory service health endpoint latency"},
        ],
        mitigation_command="kubectl rollout restart deployment/checkout-service && kubectl set env deployment/checkout-service INVENTORY_CLIENT_TIMEOUT_MS=500",
        verification_check="curl -o /dev/null -s -w '%{http_code} %{time_total}' http://api-gateway/api/v2/checkout/healthz",
    ),
    IncidentSpec(
        id="deployment-503-bad-gateway",
        title="503 Service Unavailable After Blue-Green Deployment",
        severity=IncidentSeverity.SEV1,
        summary="Immediately following blue-green deployment of the user-profile service, 100% of user traffic received HTTP 503.",
        impact="All authenticated users cannot load profile or session data; login fails.",
        initial_symptoms=[
            "Service-level 503 response code spike immediately following release v2.4.0",
            "Kubernetes pods show Running and 1/1 Ready",
            "Kubernetes Service shows 0 active endpoints",
        ],
        topology={
            "nodes": [
                {"id": "ingress", "label": "Nginx Ingress", "type": "ingress", "status": "failed"},
                {"id": "svc", "label": "user-profile-svc", "type": "service", "status": "failed"},
                {"id": "pod1", "label": "user-profile-v2-7b89f", "type": "pod", "status": "healthy"},
                {"id": "pod2", "label": "user-profile-v2-4c22e", "type": "pod", "status": "healthy"},
            ],
            "edges": [
                {"source": "ingress", "target": "svc", "status": "broken"},
                {"source": "svc", "target": "pod1", "status": "dropped"},
                {"source": "svc", "target": "pod2", "status": "dropped"},
            ],
        },
        affected_services=["user-profile-service", "nginx-ingress"],
        root_cause_explanation="The deployment manifest modified pod template labels from 'app: user-profile' to 'app.kubernetes.io/name: user-profile', but the Kubernetes Service spec selector was left pointing to 'app: user-profile'. Consequently, the service selector matched 0 pods, leaving the Service endpoint list empty.",
        remediation_steps=[
            "Patch Service selector to match new pod labels or revert deployment label key",
            "Verify endpoints population via 'kubectl get endpoints user-profile-svc'",
        ],
        prevention_measures=[
            "Use Helm or Kustomize with shared metadata templates to prevent selector/label divergence",
            "Run automated pre-traffic endpoint validation in the CI/CD deployment pipeline before switching ingress weight",
        ],
        alerts=[
            AlertEvent(
                id="alt-03",
                name="ZeroEndpointsActive",
                severity="critical",
                status="firing",
                started_at="2026-09-14T09:10:00Z",
                description="Kubernetes service 'user-profile-svc' has 0 available endpoints",
                labels={"service": "user-profile-svc", "namespace": "prod"},
            ),
        ],
        hypotheses=[
            IncidentHypothesis(
                id="hyp-3",
                statement="New container version crashed immediately upon receiving traffic",
                plausible=True,
                evidence_required="Check pod restarts count and logs",
                disproven_by="Pod status is Running with 0 restarts and ready 1/1",
            ),
            IncidentHypothesis(
                id="hyp-4",
                statement="Kubernetes Service selector label mismatch with Deployment pod template labels",
                plausible=True,
                evidence_required="Compare 'kubectl get svc user-profile -o yaml' selector with pod labels",
            ),
        ],
        diagnostic_commands=[
            {"cmd": "kubectl get endpoints user-profile-svc", "description": "Check if endpoints are registered for the service"},
            {"cmd": "kubectl get pods --show-labels", "description": "Inspect labels on active pods"},
            {"cmd": "kubectl describe svc user-profile-svc", "description": "Inspect service selector definition"},
        ],
        mitigation_command="kubectl patch svc user-profile-svc -p '{\"spec\":{\"selector\":{\"app.kubernetes.io/name\":\"user-profile\"}}}'",
        verification_check="kubectl get endpoints user-profile-svc | grep -v '<none>'",
    ),
    IncidentSpec(
        id="coredns-intermittent-resolution-failure",
        title="Intermittent Cluster-Wide DNS Resolution Timeouts",
        severity=IncidentSeverity.SEV1,
        summary="Microservices intermittently fail to resolve internal service names and external APIs, causing 500 error blips across the cluster.",
        impact="Approximately 8% of all inter-service requests fail with 'Name or service not known' or timeout.",
        initial_symptoms=[
            "Microservices logging 'java.net.UnknownHostException' and 'dial tcp: lookup auth-service: i/o timeout'",
            "Errors correlate with high traffic periods",
            "CoreDNS pods CPU utilization at 100%",
        ],
        topology={
            "nodes": [
                {"id": "coredns1", "label": "CoreDNS Pod 1", "type": "pod", "status": "failed"},
                {"id": "coredns2", "label": "CoreDNS Pod 2", "type": "pod", "status": "failed"},
                {"id": "app", "label": "Microservices", "type": "service", "status": "degraded"},
                {"id": "upstream", "label": "VPC DNS (10.0.0.2)", "type": "gateway", "status": "healthy"},
            ],
            "edges": [
                {"source": "app", "target": "coredns1", "status": "slow"},
                {"source": "app", "target": "coredns2", "status": "slow"},
                {"source": "coredns1", "target": "upstream", "status": "normal"},
            ],
        },
        affected_services=["coredns", "all-microservices"],
        root_cause_explanation="Default Alpine and glibc /etc/resolv.conf contains 'ndots:5' and 3 search domains. Every single external API call (e.g. s3.amazonaws.com) triggered 4 sequential failing internal domain lookups before trying the external query. When traffic increased 2x, CoreDNS query volume multiplied 5x, saturating the 2 CoreDNS pods.",
        remediation_steps=[
            "Autoscale CoreDNS deployment from 2 to 6 replicas",
            "Configure NodeLocal DNSCache daemonset to handle local caching",
            "Append trailing dots to fully qualified external hostnames (e.g. s3.amazonaws.com.)",
        ],
        prevention_measures=[
            "Deploy NodeLocal DNSCache across all Kubernetes node groups",
            "Set dnsConfig with ndots:2 on high-throughput microservices",
            "Implement CoreDNS auto-scaler daemon",
        ],
        alerts=[
            AlertEvent(
                id="alt-04",
                name="CoreDNSLatencyHigh",
                severity="critical",
                status="firing",
                started_at="2026-09-14T08:15:00Z",
                description="CoreDNS 99th percentile request duration > 1000ms",
                labels={"job": "coredns"},
            ),
        ],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl get pods -n kube-system -l k8s-app=kube-dns", "description": "Check CoreDNS pod count and state"},
            {"cmd": "kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100", "description": "Inspect CoreDNS error logs"},
            {"cmd": "kubectl top pods -n kube-system", "description": "Inspect CoreDNS CPU and memory consumption"},
        ],
        mitigation_command="kubectl scale deployment coredns -n kube-system --replicas=6",
        verification_check="kubectl get deployment coredns -n kube-system -o jsonpath='{.status.readyReplicas}'",
    ),
    IncidentSpec(
        id="postgres-connection-pool-exhaustion",
        title="PostgreSQL Max Connection Saturation and Thread Starvation",
        severity=IncidentSeverity.SEV1,
        summary="Backend workers failing to acquire database connections; transactions queuing indefinitely.",
        impact="Payment transactions and ledger writes completely blocked.",
        initial_symptoms=[
            "FATAL: remaining connection slots are reserved for non-superuser connections",
            "Active database connection count is 200/200",
            "Workers logging 'HikariPool-1 - Connection is not available, request timed out after 30000ms'",
        ],
        topology={
            "nodes": [
                {"id": "workers", "label": "Payment Workers (x20)", "type": "service", "status": "failed"},
                {"id": "pgbouncer", "label": "PgBouncer (Missing)", "type": "gateway", "status": "failed"},
                {"id": "postgres", "label": "PostgreSQL Primary", "type": "database", "status": "failed"},
            ],
            "edges": [
                {"source": "workers", "target": "postgres", "status": "broken"},
            ],
        },
        affected_services=["payment-service", "postgresql"],
        root_cause_explanation="Each of the 20 payment-worker pods had connection pool maxPoolSize configured to 25 (total 500 potential connections), while PostgreSQL max_connections was limited to 200. Furthermore, an unhandled exception in the webhook handler held connection leases open without releasing back to the pool.",
        remediation_steps=[
            "Deploy PgBouncer connection pooler in transaction pooling mode",
            "Reduce application pool size from 25 to 8 per pod",
            "Terminate idle-in-transaction connections via pg_terminate_backend()",
        ],
        prevention_measures=[
            "Enforce connection pool mathematics (Pool size per pod * Max replicas <= PgBouncer max connections)",
            "Mandate PgBouncer for all Kubernetes database workloads",
            "Set idle_in_transaction_session_timeout = 10000 in postgresql.conf",
        ],
        alerts=[
            AlertEvent(
                id="alt-05",
                name="PostgresConnectionExhaustion",
                severity="critical",
                status="firing",
                started_at="2026-09-14T07:22:00Z",
                description="Postgres connection utilization at 100%",
                labels={"database": "payments_prod"},
            ),
        ],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "psql -c 'SELECT count(*), state FROM pg_stat_activity GROUP BY state;'", "description": "Check connection states in postgres"},
            {"cmd": "psql -c 'SHOW max_connections;'", "description": "Check max connections limit"},
        ],
        mitigation_command="kubectl set env deployment/payment-worker DB_POOL_MAX_SIZE=5",
        verification_check="psql -c 'SELECT count(*) FROM pg_stat_activity;'",
    ),
    IncidentSpec(
        id="retry-storm-cpu-saturation",
        title="Cascading Retry Storm and CPU Thrashing",
        severity=IncidentSeverity.SEV1,
        summary="A brief 100ms blip in authentication service triggered a continuous retry storm that overwhelmed upstream servers, preventing self-recovery.",
        impact="Authentication and dependent services running at 100% CPU, rejecting all legitimate traffic.",
        initial_symptoms=[
            "CPU utilization on auth-service jumped to 100% across all 15 pods",
            "Traffic volume spiked 12x above normal baseline without increase in user requests",
            "Incoming request headers show retry-attempt count: 12, 13, 14...",
        ],
        topology={
            "nodes": [
                {"id": "mobile-app", "label": "Client Apps", "type": "client", "status": "degraded"},
                {"id": "gateway", "label": "API Gateway", "type": "gateway", "status": "degraded"},
                {"id": "auth-svc", "label": "Auth Service", "type": "service", "status": "failed"},
            ],
            "edges": [
                {"source": "mobile-app", "target": "gateway", "status": "slow"},
                {"source": "gateway", "target": "auth-svc", "status": "broken"},
            ],
        },
        affected_services=["auth-service", "api-gateway"],
        root_cause_explanation="Client libraries were configured with immediate retries on HTTP 500 without exponential backoff, jitter, or maximum retry budget. When the database briefly paused for vacuuming, 500 errors were returned, causing 10,000 clients to immediately retry simultaneously every 100ms in an infinite loop.",
        remediation_steps=[
            "Enable rate limiting and shed load on API Gateway using token bucket policy",
            "Deploy circuit breaker on Gateway to fail fast on auth service errors",
            "Enforce client-side exponential backoff with full jitter in SDK update",
        ],
        prevention_measures=[
            "Configure Envoy retry budgets (retry max 20% of total traffic)",
            "Adopt 'Decorrelated Jitter' backoff algorithms in all client libraries",
            "Implement adaptive concurrency limits",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl logs -l app=api-gateway | grep -c 'retry-attempt'", "description": "Count retry requests"},
        ],
        mitigation_command="kubectl apply -f /infra/gateway-ratelimit-circuitbreaker.yaml",
        verification_check="kubectl get envoyfilter -n istio-system gateway-ratelimit",
    ),
    IncidentSpec(
        id="mtls-certificate-expiry",
        title="Service Mesh mTLS Intermediate Certificate Expiration",
        severity=IncidentSeverity.SEV1,
        summary="Cluster-wide Envoy sidecar communication abruptly severed due to expired Citadel / cert-manager root CA certificate.",
        impact="Complete outage of internal microservice mesh RPCs with SSL handshake errors.",
        initial_symptoms=[
            "Envoy proxy logs: 'SSL routines:OPENSSL_internal:SSLV3_ALERT_CERTIFICATE_EXPIRED'",
            "Pods cannot reach neighboring pods over service mesh ports (15001/15006)",
        ],
        topology={
            "nodes": [
                {"id": "certmgr", "label": "Cert-Manager", "type": "operator", "status": "failed"},
                {"id": "istiod", "label": "Istiod Control Plane", "type": "control-plane", "status": "failed"},
                {"id": "svc-a", "label": "Frontend Pod", "type": "pod", "status": "failed"},
                {"id": "svc-b", "label": "Backend Pod", "type": "pod", "status": "failed"},
            ],
            "edges": [
                {"source": "svc-a", "target": "svc-b", "status": "broken"},
            ],
        },
        affected_services=["istiod", "all-mesh-services"],
        root_cause_explanation="The intermediate CA secret 'cacerts' in istio-system expired after 1 year. The automated certificate renewal CronJob had failed silently 3 weeks prior due to an RBAC permission error and had not alerted on-call engineers.",
        remediation_steps=[
            "Regenerate cluster CA certificates and update 'cacerts' secret",
            "Restart Istiod control plane to broadcast new trusted certificate chain",
            "Trigger sidecar proxy secret rotation",
        ],
        prevention_measures=[
            "Implement Prometheus x509-certificate-exporter with alerts at 30, 14, and 7 days prior to expiry",
            "Use automated ACME/Vault dynamic short-lived certificates",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl get secret -n istio-system cacerts -o jsonpath='{.data.ca-cert\\.pem}' | base64 -d | openssl x509 -noout -enddate", "description": "Check expiration date of mesh CA certificate"},
        ],
        mitigation_command="kubectl rollout restart deployment/istiod -n istio-system",
        verification_check="openssl x509 -checkend 86400",
    ),
    IncidentSpec(
        id="gitops-argocd-outofsync-loop",
        title="Argo CD GitOps Endless Sync Loop & Schema Rejection",
        severity=IncidentSeverity.SEV2,
        summary="Production Argo CD application entered continuous sync-failed loop, locking deployment pipeline.",
        impact="Engineers unable to deploy hotfixes; cluster state stuck in degraded reconciliation.",
        initial_symptoms=[
            "Argo CD shows Application 'payment-pipeline' in status 'Degraded / OutOfSync'",
            "Sync error: 'Schema validation error: unknown field \"resources.limit.cpu\" (did you mean \"limits.cpu\"?)'",
        ],
        topology={
            "nodes": [
                {"id": "git", "label": "Git Repo (Main)", "type": "git", "status": "healthy"},
                {"id": "argocd", "label": "Argo CD Server", "type": "gitops", "status": "degraded"},
                {"id": "k8s-api", "label": "K8s API Server", "type": "control-plane", "status": "healthy"},
            ],
            "edges": [
                {"source": "git", "target": "argocd", "status": "normal"},
                {"source": "argocd", "target": "k8s-api", "status": "broken"},
            ],
        },
        affected_services=["argocd", "payment-pipeline"],
        root_cause_explanation="A developer merged a typo in the Kubernetes deployment manifest ('resources.limit.cpu' instead of 'resources.limits.cpu'). The Kubernetes API server rejected the schema, but auto-sync was enabled, causing Argo CD to attempt reconciliation every 10 seconds in an infinite loop.",
        remediation_steps=[
            "Correct typo in Git repository manifest and commit fix to main",
            "Trigger manual sync in Argo CD",
        ],
        prevention_measures=[
            "Add pre-commit kubeconform and kube-linter checks in CI to reject invalid manifests before merge",
            "Disable automated retry loops on schema rejection errors",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "argocd app get payment-pipeline", "description": "Check Argo CD application health status"},
        ],
        mitigation_command="git commit -am 'fix: correct resources.limits typo' && git push && argocd app sync payment-pipeline",
        verification_check="argocd app wait payment-pipeline --health",
    ),
    IncidentSpec(
        id="opentelemetry-buffer-overflow",
        title="OpenTelemetry Collector Span Drop and Memory Pressure",
        severity=IncidentSeverity.SEV2,
        summary="Distributed trace spans disappearing; 80% of traces missing in Grafana Tempo.",
        impact="Engineers unable to inspect spans or root causes during ongoing latency investigations.",
        initial_symptoms=[
            "Tempo receiving only 20% of expected trace volume",
            "OpenTelemetry Collector metric 'otelcol_exporter_enqueue_failed_spans' spiking",
            "Collector pods restarting due to OOMKilled",
        ],
        topology={
            "nodes": [
                {"id": "apps", "label": "App Pods (OTel SDK)", "type": "service", "status": "healthy"},
                {"id": "collector", "label": "OTel Collector", "type": "service", "status": "failed"},
                {"id": "tempo", "label": "Grafana Tempo", "type": "storage", "status": "healthy"},
            ],
            "edges": [
                {"source": "apps", "target": "collector", "status": "slow"},
                {"source": "collector", "target": "tempo", "status": "broken"},
            ],
        },
        affected_services=["opentelemetry-collector", "tempo"],
        root_cause_explanation="Upstream microservice enabled verbose HTTP client span instrumentation without sampling. The OTel Collector batch processor queue size was set too small (256) while memory limiter was misconfigured, leading to buffer overflow and queue drops under high volume.",
        remediation_steps=[
            "Configure tail-based sampling processor in OTel Collector to drop 90% of HTTP 200 health check spans",
            "Increase batch processor queue_size from 256 to 4096",
            "Increase collector pod memory limit to 1Gi",
        ],
        prevention_measures=[
            "Always enforce memory_limiter processor as first processor in collector pipeline",
            "Implement head-based sampling at the SDK level for high-frequency health probes",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl logs -l app=opentelemetry-collector --tail=50", "description": "Check collector log output"},
        ],
        mitigation_command="kubectl apply -f /infra/otel-collector-optimized.yaml",
        verification_check="kubectl rollout status deployment/opentelemetry-collector",
    ),
    IncidentSpec(
        id="eks-cni-ip-exhaustion-node-notready",
        title="AWS EKS VPC CNI IP Address Exhaustion and Pending Pods",
        severity=IncidentSeverity.SEV1,
        summary="New pods stuck in Pending state indefinitely; worker nodes failing to allocate ENIs.",
        impact="Autoscaling cannot scale up services; deployment rollouts halted.",
        initial_symptoms=[
            "FailedCreatePodSandBox: 'failed to assign an IP address to container'",
            "Pods stuck in Pending status with event '0/12 nodes are available: insufficient pods'",
            "AWS VPC Subnet available IP count is 0",
        ],
        topology={
            "nodes": [
                {"id": "vpc", "label": "AWS VPC Subnet (10.0.1.0/24)", "type": "network", "status": "failed"},
                {"id": "nodes", "label": "EKS Worker Nodes", "type": "node", "status": "degraded"},
                {"id": "pending-pods", "label": "Pending Pods (x45)", "type": "pod", "status": "failed"},
            ],
            "edges": [
                {"source": "vpc", "target": "nodes", "status": "broken"},
                {"source": "nodes", "target": "pending-pods", "status": "dropped"},
            ],
        },
        affected_services=["aws-vpc-cni", "eks-cluster"],
        root_cause_explanation="The EKS cluster was deployed in a small /24 subnet (251 usable IPs). aws-vpc-cni pre-allocates warm secondary IP addresses for each Elastic Network Interface (ENI). As the cluster scaled to 10 m5.xlarge instances, the warm pool consumed all available subnet IPs, leaving zero addresses for new pods.",
        remediation_steps=[
            "Configure WARM_IP_TARGET=3 and MINIMUM_IP_TARGET=5 on aws-node daemonset",
            "Associate secondary CIDR block (100.64.0.0/16) to VPC for pod networking (Custom Networking)",
        ],
        prevention_measures=[
            "Always calculate VPC subnet sizing considering ENI warm IP allocation formulas",
            "Use VPC CNI Custom Networking for high-density pod clusters",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "aws ec2 describe-subnets --subnet-ids subnet-01234 --query 'Subnets[0].AvailableIpAddressCount'", "description": "Check available IPs in subnet"},
        ],
        mitigation_command="kubectl set env daemonset aws-node -n kube-system WARM_IP_TARGET=2",
        verification_check="kubectl get pods -A --field-selector=status.phase=Pending",
    ),
    IncidentSpec(
        id="networkpolicy-silent-drop-payment",
        title="Default-Deny NetworkPolicy Silently Dropping Ingress Traffic",
        severity=IncidentSeverity.SEV1,
        summary="Payment gateway integration abruptly failing after security team applied cluster-wide hardening policies.",
        impact="All credit card transactions timing out with connection refused / packet drop.",
        initial_symptoms=[
            "Checkout service cannot connect to payment-service:443",
            "tcpdump inside payment-service pod shows zero incoming SYN packets",
            "DNS resolves correctly to 10.96.24.110",
        ],
        topology={
            "nodes": [
                {"id": "checkout", "label": "Checkout Service", "type": "service", "status": "healthy"},
                {"id": "calico", "label": "Network Policy Engine", "type": "cni", "status": "failed"},
                {"id": "payment", "label": "Payment Service", "type": "service", "status": "isolated"},
            ],
            "edges": [
                {"source": "checkout", "target": "calico", "status": "normal"},
                {"source": "calico", "target": "payment", "status": "dropped"},
            ],
        },
        affected_services=["payment-service", "calico"],
        root_cause_explanation="Security team applied a 'default-deny-all' NetworkPolicy in the prod namespace. They intended to allow checkout -> payment traffic, but forgot to specify the namespaceSelector and port in the ingress rule, silently dropping all packets at the Linux iptables/eBPF layer.",
        remediation_steps=[
            "Update payment NetworkPolicy to explicitly whitelist ingress from pods with label 'app: checkout' on port 8443",
        ],
        prevention_measures=[
            "Test NetworkPolicies in staging using Calico policy-tracer or Cilium Hubble before production enforcement",
            "Mandate automated policy regression tests in CI",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl get networkpolicies -n prod", "description": "List active network policies in namespace"},
            {"cmd": "kubectl describe networkpolicy default-deny-all -n prod", "description": "Inspect network policy rules"},
        ],
        mitigation_command="kubectl apply -f /infra/allow-checkout-to-payment.yaml",
        verification_check="kubectl exec -it deployment/checkout-service -- curl -k https://payment-service:8443/healthz",
    ),
    IncidentSpec(
        id="canary-traffic-spillover-istio",
        title="Canary Weight Spillover via Istio Route Misconfiguration",
        severity=IncidentSeverity.SEV1,
        summary="Unstable experimental canary release receiving 90% of production traffic instead of 5%.",
        impact="Widespread user crashes on frontend due to untested schema in canary build.",
        initial_symptoms=[
            "Error rate skyrocketed from 0.1% to 34% immediately after triggering canary pipeline",
            "Istio telemetry shows canary subset receiving 9x the traffic volume of stable baseline",
        ],
        topology={
            "nodes": [
                {"id": "ingress", "label": "Istio Ingress Gateway", "type": "gateway", "status": "healthy"},
                {"id": "stable", "label": "Stable v1 (Desired 95%)", "type": "service", "status": "healthy"},
                {"id": "canary", "label": "Canary v2 (Desired 5%)", "type": "service", "status": "failed"},
            ],
            "edges": [
                {"source": "ingress", "target": "stable", "label": "10%", "status": "slow"},
                {"source": "ingress", "target": "canary", "label": "90%", "status": "broken"},
            ],
        },
        affected_services=["istio-ingress", "frontend-canary"],
        root_cause_explanation="In VirtualService YAML, route weights were inverted: weight 90 was assigned to subset: canary and weight 10 was assigned to subset: stable.",
        remediation_steps=[
            "Invert weights: subset stable = 100, subset canary = 0 immediately",
            "Validate traffic shift in Kiali / Grafana dashboard",
        ],
        prevention_measures=[
            "Use automated progressive delivery operators like Flagger or Argo Rollouts rather than manual VirtualService edits",
            "Enforce strict automated canary rollback on error rate exceeding 1%",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl get virtualservice frontend -o yaml", "description": "Check Istio VirtualService route weights"},
        ],
        mitigation_command="kubectl patch virtualservice frontend --type merge -p '{\"spec\":{\"http\":[{\"route\":[{\"destination\":{\"subset\":\"stable\"},\"weight\":100},{\"destination\":{\"subset\":\"canary\"},\"weight\":0}]}]}}'",
        verification_check="kubectl get virtualservice frontend -o jsonpath='{.spec.http[0].route[*].weight}'",
    ),
    IncidentSpec(
        id="nodejs-memory-leak-oom-cascade",
        title="V8 Heap Leak and Cgroup OOMKilled Cascade",
        severity=IncidentSeverity.SEV1,
        summary="Node.js API servers progressively crashing every 20 minutes under steady load, causing rolling outage.",
        impact="Intermittent 502 Bad Gateway errors as pods get killed by Linux kernel OOM killer in round-robin fashion.",
        initial_symptoms=[
            "Pod restart count steadily incrementing (restarts: 4, 5, 6)",
            "Last termination reason: OOMKilled (Exit Code 137)",
            "Memory graph shows classic linear sawtooth pattern",
        ],
        topology={
            "nodes": [
                {"id": "alb", "label": "ALB Load Balancer", "type": "alb", "status": "degraded"},
                {"id": "node-api", "label": "Node.js API (x6)", "type": "service", "status": "failed"},
            ],
            "edges": [
                {"source": "alb", "target": "node-api", "status": "slow"},
            ],
        },
        affected_services=["node-api-service"],
        root_cause_explanation="An unbounded in-memory JavaScript cache `const cache = {}` was storing user JWT authentication tokens without eviction (TTL or LRU max size). Under continuous traffic, V8 heap consumed the container's 512Mi cgroup limit, triggering kernel SIGKILL 137.",
        remediation_steps=[
            "Temporarily raise container memory limit to 2Gi to give headway",
            "Deploy hotfix replacing in-memory dictionary with Redis or LRU cache with max 1,000 entries",
        ],
        prevention_measures=[
            "Configure Node.js '--max-old-space-size' parameter safely below container cgroup limit",
            "Ban unbounded in-memory collections in static analysis rules",
            "Add heapdump diagnostic endpoints",
        ],
        alerts=[],
        hypotheses=[],
        diagnostic_commands=[
            {"cmd": "kubectl describe pod -l app=node-api | grep -i oomkilled", "description": "Verify OOMKilled terminations"},
            {"cmd": "kubectl top pods -l app=node-api", "description": "Check current memory usage per pod"},
        ],
        mitigation_command="kubectl set resources deployment/node-api --limits=memory=2Gi",
        verification_check="kubectl get deployment node-api -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'",
    ),
]


class IncidentCatalog:
    """Catalog and index of incident scenarios."""

    def __init__(self):
        self._incidents = {inc.id: inc for inc in INCIDENTS}

    def list_all(self) -> List[IncidentSpec]:
        return list(self._incidents.values())

    def get(self, incident_id: str) -> IncidentSpec:
        return self._incidents.get(incident_id)
