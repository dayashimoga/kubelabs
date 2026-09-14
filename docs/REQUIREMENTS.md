# KubeLabs System Requirements & Operational Specifications

## 1. Executive Summary
KubeLabs is an enterprise-grade, hands-on DevOps and Site Reliability Engineering (SRE) training and troubleshooting platform. Unlike passive video tutorials or basic multiple-choice quizzes, KubeLabs enforces active learning following the cycle:
$$\text{Learn} \longrightarrow \text{Practice} \longrightarrow \text{Break} \longrightarrow \text{Troubleshoot} \longrightarrow \text{Fix} \longrightarrow \text{Validate} \longrightarrow \text{Explain} \longrightarrow \text{Assess} \longrightarrow \text{Master}$$

## 2. Functional Requirements

### 2.1 Core Learning Tracks
The platform provides comprehensive coverage of 12 core engineering tracks, spanning:
1. **Linux Internals**: VFS, Inodes, Process Table, Namespaces, Cgroups v2, Page Cache, Systemd.
2. **Networking**: TCP 3-way handshake, socket states (TIME_WAIT), MTU, DNS hierarchy, TLS 1.3.
3. **Containers & Runtimes**: OCI, Podman/Docker, BuildKit, multi-stage builds, PID 1 signal forwarding.
4. **Kubernetes Core**: Controllers, Kubelet, Scheduler, Endpoints, Probes, StorageClasses, CNI.
5. **Helm & Kustomize**: Chart templates, hooks, release secrets, strategic merge patches, JSON 6902.
6. **Terraform**: HCL, remote S3 backends, DynamoDB state locks, drift remediation, moved blocks.
7. **Ansible**: Agentless SSH execution, idempotency verification, handlers, Ansible Vault.
8. **Git & CI/CD**: Commit graph, reflog recovery, GitHub Actions matrix builds, secrets hygiene.
9. **GitOps & Argo CD**: Declarative reconciliation, self-healing, sync waves, schema validation.
10. **Observability Stack**: Prometheus metrics, PromQL, Alertmanager, Loki, OpenTelemetry SDK & Collector.
11. **Service Mesh (Istio)**: Envoy xDS dynamic discovery, mTLS SPIFFE, traffic splitting, circuit breaking.
12. **Cloud & AWS EKS**: IAM IRSA, VPC CNI IP allocation, Security Groups, ALB Ingress controllers.

### 2.2 Declarative Lab Engine
- All labs are defined declaratively in YAML with strict schema validation (`LabSpec`).
- Verification must test **final state** (file attributes, running processes, socket states, YAML structures, metric values, HTTP response codes) rather than shell command matching.
- Every lab provides 5-tier layered hints: Conceptual $\rightarrow$ Inspection Area $\rightarrow$ Diagnostic Command $\rightarrow$ Strong Clue $\rightarrow$ Full Solution.

### 2.3 Interactive Troubleshooting Advisor
- Responds contextually to canonical learner queries:
  - *What should I inspect next?*
  - *Why did this fail?*
  - *Which command should I run?*
  - *Explain this output.*
  - *Show another possible root cause.*
  - *Show the correct solution.*

### 2.4 SEV-1 / SEV-2 Incident Simulator
- Simulates realistic multi-service cascading failures with interactive topology, alerts, metrics jitter, log streams, and distributed traces.
- Evaluates SRE performance across 6 standard dimensions:
  `Detection | Investigation | Root Cause | Fix Correctness | Verification | Prevention`.

## 3. Non-Functional & Security Requirements
- **Container Isolation**: Sandboxes must execute via rootless Podman with dropped capabilities (`cap-drop=ALL`), strict cgroup memory and CPU limits, and non-root execution.
- **Auto-Cleanup & TTL**: Stale sandboxes must automatically terminate after 30 minutes.
- **Latency**: PTY WebSocket streaming input latency $< 20\text{ms}$.
- **Accessibility**: Keyboard navigable, high-contrast dark theme, zero distracting gamification.
