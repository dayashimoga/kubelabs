# Service Mesh & Istio Traffic Engineering Curriculum

## 1. What
A Service Mesh is a dedicated infrastructure layer that controls, secures, and observes service-to-service communication in microservice architectures using lightweight sidecar proxies (Envoy) deployed alongside application containers.

## 2. Why
Service meshes provide uniform mTLS encryption, traffic shifting, canary rollouts, fault injection, and circuit breaking without modifying application source code. However, misconfigured route weights, cascading retry storms, sidecar memory leaks, and authorization policy denials can induce wide-scale outages.

## 3. Architecture
```
Control Plane:
   [istiod] (compiles K8s CRDs into Envoy xDS configuration: LDS, RDS, CDS, EDS)
      |
      |-- gRPC xDS Discovery (Port 15012)
      |
Data Plane (Inside Pods):
   +-----------------------------------------------------------+
   | Pod: order-service                                        |
   |                                                           |
   | [App Container (8080)] <--- localhost ---> [Envoy (15001)]|
   +-----------------------------------------------------------+
                                   ^
                                   | (mTLS, Spiffe ID)
                                   v
   +-----------------------------------------------------------+
   | Pod: payment-service                                      |
   |                                                           |
   | [App Container (8080)] <--- localhost ---> [Envoy (15006)]|
   +-----------------------------------------------------------+
```

## 4. Internals
- **xDS Configuration Protocol**: Envoy dynamically pulls configuration from `istiod` via gRPC:
  - `LDS` (Listener Discovery Service): Inbound/outbound ports (15001, 15006).
  - `RDS` (Route Discovery Service): VirtualService routing rules and URL path matching.
  - `CDS` (Cluster Discovery Service): Upstream service definitions (DestinationRules).
  - `EDS` (Endpoint Discovery Service): Live pod IP addresses.
- **Mutual TLS (mTLS) with SPIFFE**: Istiod acts as a Certificate Authority (CA) issuing short-lived x509 certificates to Envoy sidecars. Identity is encoded in the SAN: `spiffe://cluster.local/ns/<namespace>/sa/<serviceaccount>`.
- **Circuit Breaking & Outlier Detection**: Envoy tracks upstream consecutive errors (5xx). If errors exceed thresholds, Envoy temporarily evicts the unhealthy host from the load balancing pool, preventing cascading failures.
- **Traffic Shifting**: VirtualService routes split traffic across DestinationRule subsets using integer percentage weights (e.g. 95% v1, 5% v2).

## 5. Commands
- Istioctl diagnostic commands:
  - `istioctl analyze` (validates mesh configuration syntax and detects conflicts)
  - `istioctl proxy-status` (checks sync state between istiod and all Envoy sidecars)
  - `istioctl proxy-config cluster <pod_name>` (inspects upstream clusters known to Envoy)
  - `istioctl proxy-config endpoints <pod_name>` (verifies active pod endpoints)
  - `istioctl proxy-config routes <pod_name>` (inspects HTTP route table)
  - `istioctl authn tls-check <pod_name> <service>` (verifies mTLS compatibility)

## 6. Configuration
- Production VirtualService and DestinationRule with Circuit Breaking:
  ```yaml
  apiVersion: networking.istio.io/v1beta1
  kind: DestinationRule
  metadata:
    name: order-service
  spec:
    host: order-service.prod.svc.cluster.local
    subsets:
      - name: stable
        labels:
          version: v1
      - name: canary
        labels:
          version: v2
    trafficPolicy:
      tls:
        mode: ISTIO_MUTUAL
      connectionPool:
        tcp:
          maxConnections: 100
        http:
          http1MaxPendingRequests: 10
          maxRequestsPerConnection: 10
      outlierDetection:
        consecutive5xxErrors: 3
        interval: 10s
        baseEjectionTime: 30s
        maxEjectionPercent: 50
  ```

## 7. Hands-on Lab
- **Lab 1: Investigating 503 Service Unavailable via istioctl analyze**: Discover misconfigured DestinationRule pointing to nonexistent subset; fix and verify routing.
- **Lab 2: Cascading Retry Storm Mitigation with EnvoyFilter**: Tune Envoy retry budgets to cap retries at 20% of traffic, stopping downstream CPU saturation.
- **Lab 3: Strict mTLS AuthorizationPolicy Denial**: Troubleshoot `RBAC: access denied` HTTP 403 between frontend and billing service; add correct Principal to `AuthorizationPolicy`.

## 8. Common Errors
- `503 Service Unavailable (UF / upstream connection failure)`: Destination host not listening, sidecar not injected, or mTLS mismatch (`PERMISSIVE` vs `STRICT`).
- `RBAC: access denied (403)`: Istio AuthorizationPolicy blocked request.
- Envoy sidecar CPU throttling due to too many xDS updates in a high-churn cluster.

## 9. Troubleshooting
1. Run `istioctl analyze -A` to catch obvious misconfigurations.
2. Check sync status: `istioctl proxy-status`.
3. Inspect Envoy access logs: look for response flags like `UF` (upstream failure), `NR` (no route), `UO` (upstream overflow).

## 10. Production Design
- Enable `Sidecar` resources in each namespace to restrict Envoy configuration to only relevant services (reduces Envoy memory footprint by 80%).
- Transition mesh mTLS from `PERMISSIVE` to `STRICT` once all workloads have sidecars.

## 11. Security
- Enforce strict `PeerAuthentication` (`STRICT` mode).
- Use `AuthorizationPolicy` with SPIFFE identities to enforce zero-trust network access.

## 12. Performance
- Configure connection pooling and HTTP keep-alives.
- Turn off access logging on internal sidecars and rely on distributed tracing to save CPU.

## 13. Interview Scenarios
- **Scenario**: An application deployed in an Istio mesh fails to connect to an external payment API with `503 Service Unavailable`. What is the likely cause?
  - **Answer**: By default, Istio may be configured with `meshConfig.outboundTrafficPolicy.mode: REGISTRY_ONLY`. In this mode, Envoy blocks all outbound connections to endpoints that are not explicitly registered in Istio's internal service registry. To resolve, define a `ServiceEntry` manifest for the external API host and port.
