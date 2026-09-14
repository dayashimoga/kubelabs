# KubeLabs Curriculum & Tracks Reference

## 1. Curriculum Structure
The KubeLabs curriculum follows a rigorous 13-part pedagogical format for every engineering discipline:
$$\text{What} \rightarrow \text{Why} \rightarrow \text{Architecture} \rightarrow \text{Internals} \rightarrow \text{Commands} \rightarrow \text{Configuration} \rightarrow \text{Hands-on Lab} \rightarrow \text{Common Errors} \rightarrow \text{Troubleshooting} \rightarrow \text{Production Design} \rightarrow \text{Security} \rightarrow \text{Performance} \rightarrow \text{Interview Scenarios}$$

## 2. Track Catalog

| Track | Level | Core Topics Covered | Associated Labs & Scenarios |
| :--- | :--- | :--- | :--- |
| **Linux** | Beginner $\rightarrow$ Advanced | Inodes, VFS, Cgroups v2, Namespaces, Zombie reaping, TCP sockets, Page cache | `linux-inode-exhaustion`, `linux-zombie-hunting`, `linux-port-conflict` |
| **Networking** | Intermediate | TCP 3-way handshake, TIME_WAIT, ndots:5, DNS resolution, TLS 1.3 | `networking-ndots-loop`, `networking-mtu-blackhole` |
| **Docker / OCI** | Beginner $\rightarrow$ Advanced | BuildKit, PID 1 signal forwarding, Multi-stage caching, Distroless, Rootless | `docker-bad-dockerfile`, `docker-volume-permission`, `docker-oom-killed` |
| **Kubernetes** | Intermediate $\rightarrow$ Production | Controllers, Kubelet, Probes, Services, Endpoints, CNI, Scheduling, PDBs | `k8s-crashloop-probe`, `k8s-zero-endpoints`, `k8s-pending-pvc` |
| **Helm & Kustomize** | Intermediate | Go templates, nindent, hooks, Strategic Merge Patch, JSON 6902, drift | `helm-template-indentation`, `kustomize-overlay-conflict` |
| **Terraform** | Intermediate $\rightarrow$ Advanced | HCL, S3 backends, DynamoDB state locks, drift import, moved blocks | `terraform-state-lock`, `terraform-drift-import` |
| **Ansible** | Beginner $\rightarrow$ Intermediate | Agentless SSH, Idempotency, Handlers, Ansible Vault, Roles | `ansible-non-idempotent-fix` |
| **Git & CI/CD** | Beginner $\rightarrow$ Advanced | Commit graphs, Git reflog, GitHub Actions matrix, Gitleaks security scans | `git-reflog-recovery` |
| **Argo CD / GitOps** | Intermediate $\rightarrow$ Production | Declarative reconciliation, self-healing, sync waves, schema validation | `argocd-outofsync-schema` |
| **Observability** | Advanced | Prometheus TSDB, PromQL, Cardinality, Alertmanager, OTel traces | `prometheus-cardinality-explosion`, `otel-broken-trace` |
| **Service Mesh (Istio)** | Advanced | Envoy xDS, mTLS SPIFFE, traffic shifting, retry budgets, circuit breakers | `istio-circuit-breaker-retry-storm` |
| **AWS & EKS** | Advanced $\rightarrow$ Production | IAM IRSA, VPC CNI IP allocation, Security Groups, ALB controllers | `aws-eks-cni-ip-exhaustion` |
| **SRE & Incidents** | Production | SLO/SLI mathematics, multi-window burn rate alerts, SEV-1 incident commander | 12 Live Incident Simulator scenarios |
| **Capstones** | Production | End-to-end multi-tier pipeline: Git $\rightarrow$ CI $\rightarrow$ K8s $\rightarrow$ Argo $\rightarrow$ Istio $\rightarrow$ OTel $\rightarrow$ Recovery | `capstone-end-to-end-sre-pipeline` |

## 3. Prerequisite Graph
```
Linux Internals --------> Docker / OCI --------> Kubernetes Core
      |                         |                      |
      v                         v                      v
Networking & DNS -------> Git & CI/CD -----------> Helm & Kustomize
                                                       |
                                                       v
                                            Argo CD & GitOps
                                                       |
                                                       v
                                   Observability & Service Mesh
                                                       |
                                                       v
                                            Full Production Capstone
```
Learners can explore any topic freely, but following the prerequisite graph ensures strong foundational concepts before confronting complex distributed failure modes.
