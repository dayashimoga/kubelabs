# GitOps & Argo CD Reconciliation Curriculum

## 1. What
GitOps is an operational model where Git repositories serve as the single source of truth for declared infrastructure and application state. Argo CD is a declarative GitOps continuous delivery tool for Kubernetes.

## 2. Why
GitOps eliminates configuration drift, enforces peer-reviewed auditing, and automates rollouts. However, OutOfSync loops, schema validation rejections, failed health checks, sync waves deadlocks, and Helm/Kustomize rendering errors can halt production releases.

## 3. Architecture
```
Git Repository (Desired State) <---+
                                    |
                                    v
                           [Argo CD Repo Server] (renders Helm/Kustomize)
                                    |
                                    v
                           [Argo CD Application Controller]
                                    |
                           (Reconciliation Loop)
                                    |
                                    v
                        [Kubernetes Live Cluster] (Actual State)
```

## 4. Internals
- **Reconciliation Loop**: The Application Controller continuously polls Git (or receives webhooks) and compares rendered manifests against the live Kubernetes cluster state via the Kubernetes API server.
- **Sync Status**: `Synced` vs `OutOfSync`.
- **Health Status**: Evaluated by Lua health check scripts. Values: `Healthy`, `Progressing`, `Degraded`, `Suspended`, `Missing`.
- **Sync Waves & Hooks**: Annotations (`argocd.argoproj.io/sync-wave: "1"`) order the application of manifests. Negative waves execute first (e.g. CRDs, Namespaces), followed by wave 0 (Deployments), and positive waves (Ingress).
- **Self-Healing & Automated Prune**: `selfHeal: true` automatically reverts manual out-of-band `kubectl` edits in the cluster. `prune: true` deletes cluster resources that were removed from Git.

## 5. Commands
- Argo CD CLI:
  - `argocd app list`
  - `argocd app get <app_name>`
  - `argocd app diff <app_name>` (inspect differences between Git and live cluster)
  - `argocd app sync <app_name> --prune`
  - `argocd app rollback <app_name> <history_id>`
  - `argocd app wait <app_name> --health`

## 6. Configuration
- Production Argo CD Application Manifest:
  ```yaml
  apiVersion: argoproj.io/v1alpha1
  kind: Application
  metadata:
    name: payment-service
    namespace: argocd
  spec:
    project: default
    source:
      repoURL: 'https://github.com/corp/gitops-prod.git'
      targetRevision: HEAD
      path: apps/payment/overlays/production
    destination:
      server: 'https://kubernetes.default.svc'
      namespace: payment
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
      syncOptions:
        - CreateNamespace=true
        - ApplyOutOfSyncOnly=true
      retry:
        limit: 5
        backoff:
          duration: 5s
          factor: 2
          maxDuration: 3m
  ```

## 7. Hands-on Lab
- **Lab 1: Argo CD OutOfSync Loop Resolution**: Manifest has an immutable field modification; observe infinite sync retry loop; fix Git manifest and trigger clean sync.
- **Lab 2: Custom Health Check for Custom Resource**: Write a Lua health check for a custom database operator CRD that was reporting `Progressing` indefinitely.
- **Lab 3: Git Drift Reversion via Self-Heal**: Manually edit deployment replicas with `kubectl scale`; observe Argo CD self-healing controller detect drift and revert to Git-defined replica count.

## 8. Common Errors
- `ComparisonError: failed to generate manifests: ...`: Helm or Kustomize rendering syntax error in repo-server.
- `SyncFailed: Schema validation error`: Kubernetes API server rejected field format.
- Application status stuck in `Degraded`: Underlyling Pods CrashLooping or PVC unbound.

## 9. Troubleshooting
1. Inspect live diff: `argocd app diff <app_name>`.
2. Review Argo CD Application Controller logs: `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller`.
3. Check repo-server render output: `argocd app manifests <app_name>`.

## 10. Production Design
- Adopt the "App of Apps" or Argo CD ApplicationSet pattern for multi-tenant and multi-cluster management.
- Store sensitive values outside Git using SealedSecrets or External Secrets Operator with AWS Secrets Manager / Vault.

## 11. Security
- Implement Argo CD SSO via OIDC (Okta, GitHub, Google).
- Enforce strict RBAC policies in `argocd-rbac-cm` ConfigMap.
- Restrict destination cluster permissions to unprivileged namespaces.

## 12. Performance
- Configure Git webhooks instead of short polling intervals (default 3m polling interval causes rate limiting on GitHub API).
- Enable manifest caching in Redis.

## 13. Interview Scenarios
- **Scenario**: An SRE runs `kubectl edit deployment` in production to fix a critical outage. Five seconds later, the change is wiped out and the old broken config returns. Why?
  - **Answer**: Argo CD was configured with `selfHeal: true`. The reconciliation controller detected cluster drift from the declared Git repository state and automatically reapplied the Git manifest. In a GitOps workflow, emergency hotfixes must be committed directly to Git (or selfHeal must be temporarily suspended via `argocd app set --self-heal=false`).
