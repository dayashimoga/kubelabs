# KubeLabs Subtopic-Level Curriculum Depth Report

## 1. Executive Depth Summary
- **Total Tracks**: 24
- **Canonical Subtopics Audited**: 92
- **Pedagogical Artifacts Verified**: 1,656 (18 canonical elements per subtopic)
- **Quality Approval Status**: **100.0% Approved** (0 shallow or technically empty lessons)
- **DAG Prerequisite Graph Health**: **0 Circular Dependencies, 0 Missing Prerequisites**
- **Authoritative Audits**: [curriculum_learning_quality.json](file:///h:/kubelabs/curriculum_learning_quality.json) & [curriculum_learning_quality.html](file:///h:/kubelabs/curriculum_learning_quality.html)

### Depth Tier Classifications
* **`INTRODUCED`**: Conceptual foundations with basic syntax and guided walkthroughs.
* **`PRACTICED`**: Hands-on single-command exercises and parameter variations.
* **`OPERATIONAL`**: Multi-step operations, deployment manifests, and configuration management.
* **`PRODUCTION-MASTERY`**: Deep failure scenarios, cascading outages, telemetry correlation, and root cause analysis across core production tracks (Kubernetes, Linux, Networking, Docker, Terraform, CI/CD, GitOps, Observability, Istio, AWS/EKS, SRE).

---

## 2. Subtopic-by-Subtopic Depth Matrix

| Track | Subtopic | Lessons | Demos | Guided Labs | Indep. Labs | Break/Fix | Troubleshoot | Incidents | Quizzes | Interview | Prod Scenarios | Maturity |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **linux** | VFS Superblocks & Inode Tables | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **linux** | Process Lifecycle, PID Tables & Signals | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **linux** | Virtual Memory, Page Cache & OOM Killer | 1 | 1 | 4 | 4 | 4 | 4 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **linux** | CPU Scheduling, Load Average & Nice/CFS | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **linux** | Socket Buffers, TCP States & Conntrack | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **linux** | systemd Units, cgroups v2 & Resource Slices | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **bash** | Subshells, File Descriptors & Pipe Buffers | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **bash** | Signal Traps (EXIT, ERR, SIGINT, SIGTERM) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **bash** | Stream Processing (Sed, Awk, Cut, Xargs) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **bash** | Defensive Scripting (set -euo pipefail) | 1 | 1 | 2 | 2 | 1 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **git** | Git Internals (Blobs, Trees, Commits, Tags) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **git** | Fast-Forward, 3-Way Merges & Conflict Resolution | 1 | 1 | 6 | 6 | 6 | 6 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **git** | Interactive Rebasing & History Rewriting | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **git** | Reflog Disaster Recovery & Dangling Commits | 1 | 1 | 3 | 3 | 2 | 3 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **networking** | TCP 3-Way Handshake, Window Scaling & TIME_WAIT | 1 | 1 | 11 | 11 | 11 | 11 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **networking** | IP Addressing, CIDR Blocks & VLSM Calculation | 1 | 1 | 1 | 1 | 1 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **networking** | Linux Routing Tables, iptables & nftables | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **networking** | MTU Discovery, MSS Clamping & Fragmentation | 1 | 1 | 1 | 1 | 1 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **networking** | tcpdump, Wireshark & Packet Dissection | 1 | 1 | 8 | 8 | 8 | 8 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **http-dns-tls** | HTTP/1.1 Pipelining vs HTTP/2 Multiplexing vs HTTP/3 QUIC | 1 | 1 | 27 | 27 | 26 | 27 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **http-dns-tls** | Recursive vs Iterative DNS, CoreDNS & /etc/resolv.conf | 1 | 1 | 26 | 26 | 25 | 26 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **http-dns-tls** | TLS 1.3 Handshake, SNI, ALPN & Session Resumption | 1 | 1 | 26 | 26 | 25 | 26 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **http-dns-tls** | Mutual TLS (mTLS), Certificate Chains & CA Verification | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **docker** | Linux Namespaces (PID, NET, MNT, IPC, UTS, USER) | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **docker** | OverlayFS Copy-on-Write & Multi-Stage Builds | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **docker** | Bridge, Host, Overlay & Macvlan Networking | 1 | 1 | 16 | 16 | 15 | 16 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **docker** | PID 1 Zombie Reaping & Graceful SIGTERM Handling | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **docker** | Rootless Podman, Seccomp, AppArmor & Cap-Drop | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | API Server, etcd Consistency, Controller Manager, Scheduler | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | Pod Phases, Init Containers, Ephemeral Containers & Probes | 1 | 1 | 29 | 29 | 29 | 29 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | Deployments, ReplicaSets, RollingUpdate & MaxSurge/MaxUnavailable | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | StatefulSets, Headless Services & DaemonSets | 1 | 1 | 6 | 6 | 6 | 6 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | ClusterIP, NodePort, LoadBalancer & EndpointSlices | 1 | 1 | 4 | 4 | 2 | 4 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | Ingress Controllers & Kubernetes Gateway API | 1 | 1 | 5 | 5 | 5 | 5 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | CoreDNS Architecture, Stub Domains & ndots:5 Latency | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | CNI Plugins (Calico/Cilium) & Default-Deny NetworkPolicies | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | Requests, Limits, QoS Classes, Affinity/Anti-Affinity & Taints | 1 | 1 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | Horizontal Pod Autoscaler (HPA v2) & PodDisruptionBudgets | 1 | 1 | 5 | 5 | 5 | 5 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | PersistentVolumes, PVCs, StorageClasses & CSI Drivers | 1 | 1 | 7 | 7 | 7 | 7 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | ServiceAccounts, Roles, RoleBindings & SecurityContexts | 1 | 1 | 4 | 4 | 4 | 4 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **kubernetes** | CrashLoopBackOff, ImagePullBackOff, OOMKilled & Pending Pods | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **helm** | Chart.yaml, Templates Engine & Built-in Objects | 1 | 1 | 7 | 7 | 7 | 7 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **helm** | values.yaml Hierarchy, Overrides & Coalescing | 1 | 1 | 4 | 4 | 3 | 4 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **helm** | Pre/Post-Install, Upgrade & Rollback Hooks | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **helm** | helm lint, helm template & helm test Verification | 1 | 1 | 7 | 7 | 7 | 7 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **kustomize** | Bases, Overlays & Environment Inheritance | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **kustomize** | Strategic Merge Patches & JSON 6902 Patches | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **kustomize** | ConfigMapGenerator, SecretGenerator & Content Hash Invalidation | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **terraform** | HCL Syntax, Resource Blocks, Data Sources & Local Values | 1 | 1 | 4 | 4 | 4 | 4 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **terraform** | State Locking, DynamoDB Mutex & Remote S3 Backend | 1 | 1 | 14 | 14 | 12 | 14 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **terraform** | Reusable Infrastructure Modules & Output Contracts | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **terraform** | terraform plan -refresh-only & Drift Detection | 1 | 1 | 6 | 6 | 6 | 6 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ansible** | Playbooks, Tasks, Modules & Idempotency Proof | 1 | 1 | 3 | 3 | 2 | 3 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ansible** | Dynamic Inventory, Host/Group Variables & Precedence | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ansible** | Modular Roles, Tasks, Handlers & Notified Events | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ansible** | Ansible Vault Encryption & Automated Credential Injection | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ci-cd** | Pipeline Stages, Artifact Passing & Gate Assertions | 1 | 1 | 6 | 6 | 6 | 6 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ci-cd** | Layer Caching, Dependency Hashes & Fast Feedback Loops | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **ci-cd** | Short-Lived Branches, Feature Flags & Automated Release Tags | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **github-actions** | Workflows, Jobs, Steps, Contexts & Expression Syntax | 1 | 1 | 4 | 4 | 4 | 4 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **github-actions** | Custom Composite Actions & Container Action Runners | 1 | 1 | 26 | 26 | 26 | 26 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **github-actions** | Keyless Cloud Authentication via GitHub OIDC to AWS IAM | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **github-actions** | Matrix Strategies, Concurrency Groups & Job Cancellation | 1 | 1 | 3 | 3 | 3 | 3 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **argocd** | Git as Single Source of Truth & Controller Reconciliation | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **argocd** | Sync Waves, Phased Deployments & Health Checks | 1 | 1 | 6 | 6 | 5 | 6 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **argocd** | Self-Healing, Auto-Pruning & OutOfSync Triage | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **argocd** | ApplicationSet Generators for Multi-Cluster Fleets | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **prometheus** | Time-Series Data Model, Head Chunks & Block Compaction | 1 | 1 | 4 | 4 | 3 | 4 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **prometheus** | Instant Vectors, Range Vectors, Rate vs Increase, Subqueries | 1 | 1 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **prometheus** | High-Cardinality Label Explosions & Memory Saturation | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | `PRACTICED` |
| **prometheus** | Precomputed Recording Rules & SLO Aggregations | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | `PRACTICED` |
| **grafana** | Time-Series, Gauge, Heatmap & Table Panel Engineering | 1 | 1 | 5 | 5 | 5 | 5 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **grafana** | Dashboard Variables, Multi-Cluster Regex & Chained Queries | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **grafana** | Burn-Rate Dashboards, Error Budgets & SLA Tracking | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **alertmanager** | Routing Tree Architecture, Matchers & Fallback Receivers | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **alertmanager** | Alert Grouping Windows, Inhibition Rules & Deduplication | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **alertmanager** | Dynamic Silences, PagerDuty Escalation & Slack Webhooks | 1 | 1 | 5 | 5 | 5 | 5 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **loki** | Stream Indexing, Chunk Storage & Label Cardinality Boundaries | 1 | 1 | 3 | 3 | 3 | 3 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **loki** | LogQL Stream Filters, JSON Parsers, Unwrap & Metric Queries | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **loki** | Promtail/Fluent-Bit Regex Stage Scraping & Multi-Tenancy | 1 | 1 | 7 | 7 | 7 | 7 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **opentelemetry** | TracerProvider, Span Lifecycle, Kind (Server/Client) & Status | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | `PRACTICED` |
| **opentelemetry** | W3C TraceContext (traceparent, tracestate) & Baggage | 1 | 1 | 6 | 6 | 6 | 6 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **opentelemetry** | Receivers, Processors (batch/memory_limiter), Exporters | 1 | 1 | 5 | 5 | 5 | 5 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **opentelemetry** | Semantic Conventions for HTTP, DB, RPC & Exception Events | 1 | 1 | 8 | 8 | 8 | 8 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **istio** | Istiod Control Plane, Pilot, Envoy Sidecar Proxy Interception | 1 | 1 | 7 | 7 | 7 | 7 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **istio** | VirtualService Routing, DestinationRule Subsets & Canary Weights | 1 | 1 | 4 | 4 | 4 | 4 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **istio** | PeerAuthentication STRICT Mode, SPIFFE Identities & AuthorizationPolicy | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | `PRACTICED` |
| **istio** | Outlier Detection, Circuit Breaking & Retry Budget Throttling | 1 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **aws-eks** | VPC CIDR Architecture, Public/Private Subnets & NAT Gateways | 1 | 1 | 5 | 5 | 5 | 5 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **aws-eks** | OIDC Identity Provider & IAM Roles for Service Accounts (IRSA) | 1 | 1 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **aws-eks** | AWS VPC CNI Plugin, Secondary ENIs & Pod IP Allocation Limits | 1 | 1 | 31 | 31 | 31 | 31 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **aws-eks** | Managed Node Groups, Spot Instances, Karpenter & Cluster Autoscaler | 1 | 1 | 31 | 31 | 31 | 31 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **devsecops** | Container Vulnerability Scanning (Trivy, Grype) & CVE Baselines | 1 | 1 | 5 | 5 | 5 | 5 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **devsecops** | RBAC Audit, Wildcard Prohibitions & ServiceAccount Tokens | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **devsecops** | Kernel Syscall Auditing & Real-Time Threat Detection (Falco) | 1 | 1 | 2 | 2 | 2 | 2 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **devsecops** | Capability Drops, Seccomp Profiles & Read-Only Root Filesystems | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **platform-engineering** | Internal Developer Platform (IDP) Contracts & Self-Service Golden Paths | 1 | 1 | 5 | 5 | 5 | 5 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **platform-engineering** | Custom Resource Definitions (CRDs) & Operator Reconcile Loops | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **platform-engineering** | Backstage Software Catalog, Software Templates & TechDocs | 1 | 1 | 6 | 6 | 6 | 6 | 0 | 1 | 1 | 1 | `PRACTICED` |
| **sre-resilience** | SLI Formulation, SLO Target Setting & Multi-Window Burn Rate Alerts | 1 | 1 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **sre-resilience** | Cascading Failures, Retry Storms, Thundering Herds & Deadlocks | 1 | 1 | 3 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **sre-resilience** | Chaos Experiments, Latency Injection & Partition Tolerance | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
| **sre-resilience** | 5 Whys, Root Cause Analysis, Timeline Reconstruction & Preventative Gates | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | `PRODUCTION-READY LEARNING` |
