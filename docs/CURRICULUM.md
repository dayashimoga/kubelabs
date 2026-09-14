# KubeLabs Curriculum & Tracks Reference

## 1. 18-Element Canonical Pedagogical Structure
Every canonical subtopic in the KubeLabs curriculum is verified across all 18 essential pedagogical dimensions:
$$\text{What} \rightarrow \text{Why} \rightarrow \text{Architecture} \rightarrow \text{Internals} \rightarrow \text{Commands} \rightarrow \text{Configuration} \rightarrow \text{Worked Example} \rightarrow \text{Cheatsheet} \rightarrow \text{Guided Lab} \rightarrow \text{Independent Lab} \rightarrow \text{Break/Fix} \rightarrow \text{Common Errors} \rightarrow \text{Troubleshooting} \rightarrow \text{Production Design} \rightarrow \text{Security} \rightarrow \text{Performance} \rightarrow \text{Incident} \rightarrow \text{Quiz / Interview}$$

Audit results: **92 canonical subtopics across 24 tracks with 100% Quality-Approved artifacts (1,656 verified artifacts)** certified in `curriculum_learning_quality.json` and `curriculum_learning_quality.html`.

## 2. Mastery Depth Classification
Subtopics are categorized into progressive depth tiers based on rigorous exercise density:
- **`INTRODUCED`**: Conceptual foundations with basic syntax and guided walkthroughs.
- **`PRACTICED`**: Hands-on single-command exercises and parameter variations.
- **`OPERATIONAL`**: Multi-step operations, deployment manifests, and configuration management.
- **`PRODUCTION-MASTERY`**: Deep failure scenarios, cascading outages, telemetry correlation, and root cause analysis across:
  - Kubernetes Core & Advanced Networking
  - Linux Systems & Kernel Tracing
  - Docker & Container Runtimes
  - Terraform State & Drift Management
  - CI/CD & Automated Security Scanning
  - GitOps (Argo CD) & Declarative Reconciliation
  - Observability (Prometheus, PromQL, Grafana, OpenTelemetry)
  - Service Mesh (Istio Envoy xDS & Traffic Shifting)
  - AWS / EKS Cloud Infrastructure
  - Site Reliability Engineering & Incident Command

## 3. Prerequisite Knowledge Graph (Validated DAG)
The curriculum enforces a validated Directed Acyclic Graph (DAG) with **0 circular dependencies** and **0 missing prerequisites**:
```
Linux Systems & Kernel --------> Docker / OCI Containers --------> Kubernetes Core
      |                                    |                              |
      v                                    v                              v
Linux Networking & DNS --------> Git & CI/CD Security ----------> Helm & Kustomize
      |                                                                   |
      v                                                                   v
TCP, HTTP, TLS Protocols ---------------------------------------> Argo CD & GitOps
                                                                          |
                                                                          v
                                                             Observability & Service Mesh
                                                                          |
                                                                          v
                                                             Production SRE Incidents
```
Learners have a coherent path from zero knowledge to production troubleshooting, with unrestricted navigation supported at any stage.

## 4. 12 Mini-Production Systems Mapping
All 12 mini-production application systems run genuine multi-container processes with observable telemetry and faults:
1. **E-Commerce Checkout Pipeline** (Frontend, Gateway, Order API, Inventory, Redis, Postgres)
2. **FinTech Transaction Ledger** (API, Idempotency Cache, Transaction Worker, Ledger DB)
3. **Telemetry & Observability Stack** (OTel Collector, Prometheus, Loki, Grafana)
4. **Cloud-Native Identity SSO** (OIDC Broker, Redis Session Store, Directory)
5. **Global Edge CDN & Gateway** (Nginx Reverse Proxy, WAF, Origin Services)
6. **IoT Event Stream Ingestion** (MQTT Broker, Stream Processor, Time-Series Store)
7. **Istio Zero-Trust Service Mesh** (mTLS SPIFFE Identity, Envoy Sidecars, Telemetry)
8. **GitOps CD Continuous Delivery** (Gitea, Argo CD, Deployment Targets)
9. **Serverless Event Bus** (Webhook Ingestion, Redis Pub/Sub, Asynchronous Workers)
10. **Loki Log Aggregation & Tracing** (Promtail, Loki Ring, Jaeger Tracing)
11. **Machine Learning Inference Fleet** (FastAPI Torch Model Serving, Redis Queue)
12. **Multi-Region Disaster Recovery** (Active-Passive Replication, Health Check Failover)
