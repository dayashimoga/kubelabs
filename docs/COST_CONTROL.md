# KubeLabs Cloud Cost Optimization & Resource Governance

## 1. Cloud Cost Management Philosophy
Hands-on sandbox platforms frequently suffer from runaway cloud infrastructure costs caused by uncollected resources, orphaned cloud VPCs, running EKS clusters, and idle database instances. KubeLabs adopts a **zero-waste deterministic architecture**.

## 2. Cost Control Strategies

### 2.1 Dual-Engine Architecture (Local vs Simulated)
- **Local Container Execution**: Containers run locally in rootless Podman on shared bare-metal or self-hosted worker nodes, costing $0 in per-minute cloud API fees.
- **High-Fidelity State Simulation**: For large cloud topologies (AWS EKS, multi-AZ VPCs, ALB target groups), KubeLabs utilizes the `DeterministicSimulator`. This delivers realistic SRE troubleshooting experience without spinning up $200/month EKS control planes for each learner.

### 2.2 Strict TTL and Inactivity Quotas
- Every sandbox container is assigned a hard TTL (default 30 minutes / 1800 seconds).
- Background sweepers terminate containers whether or not the learner remembered to click "Finish Lab".
- CPU and Memory limits prevent noisy-neighbor server saturation on multi-tenant worker nodes.

### 2.3 Ephemeral Cloud Credentials
For labs that do interact with real cloud APIs (AWS/GCP):
- IAM permissions are strictly scoped to sandbox resources with tags (`kubelabs:session_id`).
- Cloud credentials expire automatically after 1 hour via AWS STS.
- Automated Lambda Janitor functions delete any tagged resource older than 2 hours.
