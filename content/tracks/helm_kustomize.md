# Helm & Kustomize Configuration Management Curriculum

## 1. What
Helm is the package manager for Kubernetes (using Go template rendering and Chart archives). Kustomize is a template-free configuration customization tool that applies patches and overlays onto base manifests.

## 2. Why
Modern microservices must run across staging, canary, and multi-region production with differing replicas, ingress domains, and secrets without duplicating entire YAML definitions. Brittle templates or conflicting patches lead to deployment failures and environment drift.

## 3. Architecture
```
Helm Flow:
  Chart.yaml + values.yaml + templates/*.yaml ---> [Helm Engine (Go Template)] ---> Rendered Manifests ---> K8s API

Kustomize Flow:
  base/ (kustomization.yaml + deployment.yaml)
       ^
       |-- overlays/staging/ (kustomization.yaml + patch.yaml)
       |-- overlays/prod/    (kustomization.yaml + patch.yaml) ---> [Kustomize Engine] ---> Rendered Manifests
```

## 4. Internals
- **Helm Secret Storage**: Helm tracks release state in Kubernetes Secrets (`sh.helm.release.v1.<release-name>.v<revision>`). Upgrades create revision $N+1$. Rollbacks read revision $N$ and apply desired state.
- **Helm Hooks Lifecycle**: `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `post-delete`, `test`. Hooks run as standalone Kubernetes Jobs before or after the main release manifests are submitted.
- **Kustomize Strategic Merge Patch vs JSON 6902**:
  - Strategic Merge Patch: Merges maps and lists using schema keys (e.g. merging a container environment variable into an existing container list matching `name: app`).
  - JSON 6902 Patch: Explicit array operations (`op: replace`, `path: /spec/replicas`, `value: 5`).

## 5. Commands
- Helm:
  - `helm template <release> ./mychart -f values-prod.yaml --debug` (render locally without installing)
  - `helm lint ./mychart`
  - `helm upgrade --install <release> ./mychart --values values-prod.yaml --wait --timeout 5m`
  - `helm history <release>`
  - `helm rollback <release> <revision>`
- Kustomize:
  - `kustomize build overlays/production`
  - `kubectl apply -k overlays/production`

## 6. Configuration
- Helm `values.yaml` and `templates/deployment.yaml` with `toYaml`, `nindent`, and `required` validation:
  ```yaml
  # templates/deployment.yaml
  spec:
    replicas: {{ .Values.replicaCount | default 1 }}
    template:
      spec:
        containers:
        - name: {{ .Chart.Name }}
          image: "{{ required "image.repository is required!" .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          {{- with .Values.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
  ```

## 7. Hands-on Lab
- **Lab 1: Helm Go Template Indentation Syntax Error**: Debug `error converting YAML to JSON: line 24: did not find expected key` caused by `nindent 8` instead of `nindent 10`; fix and test with `helm template`.
- **Lab 2: Kustomize Strategic Merge Conflict**: Fix broken Kustomize overlay where JSON 6902 patch targeted nonexistent container index `/spec/template/spec/containers/1`.
- **Lab 3: Failed Helm Upgrade Rollback**: Simulate failed post-upgrade hook blocking rollout; inspect `helm history`; perform clean rollback to revision 1.

## 8. Common Errors
- `error converting YAML to JSON`: Template rendered invalid whitespace or unindented multi-line block.
- `UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress`: Deadlock in Helm release secret status (`pending-upgrade`).
- `invalid: spec.selector: Invalid value: field is immutable`: Attempted to change deployment selector labels in an existing deployment via Helm upgrade.

## 9. Troubleshooting
1. Render template locally to inspect raw YAML output: `helm template ... --debug` or `kustomize build ...`.
2. Lint chart: `helm lint .`.
3. If release is stuck in `pending-upgrade`, inspect release secrets: `kubectl get secrets -l owner=helm`.

## 10. Production Design
- Store Helm charts and Kustomize overlays in GitOps repositories (Argo CD / Flux).
- Validate all manifests in CI with `kubeconform -strict` against Kubernetes JSON schemas.

## 11. Security
- Sign Helm charts using Cosign or GPG provenance files.
- Store sensitive values in ExternalSecrets (Vault, AWS Secrets Manager) rather than unencrypted `values.yaml`.

## 12. Performance
- Use `.Release.Revision` or Git SHA in image tags to ensure immutable rollouts.
- Limit release history retention in Helm (`--history-max 10`).

## 13. Interview Scenarios
- **Scenario**: Why does `kubectl apply` fail with `field is immutable` when upgrading a Helm chart that changed pod labels?
  - **Answer**: In Kubernetes `apps/v1` Deployments, `spec.selector` is immutable after creation. If a chart change alters the selector matchLabels, Kubernetes rejects the update. To resolve, the deployment must be deleted and recreated, or the selector change must be rolled back.
