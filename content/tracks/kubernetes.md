# Kubernetes Architecture, Internals & Deep Troubleshooting Curriculum

## 1. What
Kubernetes is an open-source container orchestration platform designed to automate deploying, scaling, and operating application containers across distributed clusters.

## 2. Why
Kubernetes is the de facto operating system of the modern cloud. However, its declarative, asynchronous reconciliation loop introduces complex failure modes: CrashLoopBackOff, failed probes, scheduler starvation, selector mismatches, Evicted pods, CNI routing errors, and CoreDNS storms.

## 3. Architecture
```
+-----------------------------------------------------------------------+
| Control Plane:                                                        |
|   kube-apiserver (REST gateway) <---> etcd (distributed key-value)    |
|        ^                 ^                                            |
|        |                 |                                            |
|   kube-scheduler   kube-controller-manager (node, replica, endpoint)  |
+--------|-----------------|--------------------------------------------+
         |                 |
+--------v-----------------v--------------------------------------------+
| Worker Nodes:                                                         |
|   kubelet (node agent) <---> container runtime (containerd/CRI-O)     |
|   kube-proxy (iptables / IPVS packet routing)                         |
|   CNI Plugin (Calico / Cilium / AWS VPC CNI)                          |
+-----------------------------------------------------------------------+
```

## 4. Internals
- **Reconciliation Loop**: Level-triggered controllers continuously compare the `current state` in etcd with the `desired state` in the manifest, executing actions to converge the two.
- **Pod Lifecycle & Phases**: `Pending` -> `Running` -> `Succeeded` / `Failed` / `Unknown`. Conditions: `PodScheduled`, `Initialized`, `ContainersReady`, `Ready`.
- **Probes**:
  - `StartupProbe`: Inhibits liveness/readiness probes until the application completes initialization.
  - `LivenessProbe`: Determines if the container needs to be restarted. If it fails `failureThreshold` times, kubelet sends `SIGTERM`, then `SIGKILL` after `terminationGracePeriodSeconds`.
  - `ReadinessProbe`: Determines if the Pod should receive traffic. If it fails, the Pod IP is removed from the Service Endpoints object (traffic stops without killing the pod).
- **Service Routing (kube-proxy)**:
  - `iptables mode`: Generates chains for each Service and Endpoint. Packets to ClusterIP are DNAT'ed via probabilistic matching (`-m statistic --mode random`) to one of the pod IPs.
  - `IPVS mode`: Uses Linux kernel IP Virtual Server with hash tables ($O(1)$ lookup), ideal for clusters with >1,000 services.
- **Scheduler Algorithms**:
  - Filtering (Predicates): Checks node resources (`PodFitsResources`), node taints/tolerations, node affinity, host ports.
  - Scoring (Priorities): Optimizes pod spreading across failure domains (`topologySpreadConstraints`, `NodeResourcesBalancedAllocation`).
- **Storage Subsystem (CSI)**: Volume lifecycle: Provision -> Attach (Controller) -> Mount (Kubelet via CSI node driver). If a PVC cannot bind to a PV, the pod remains in `Pending` state.

## 5. Commands
- Pod and cluster inspection:
  - `kubectl get pods -A -o wide --show-labels`
  - `kubectl describe pod <pod_name>` (inspect Events section!)
  - `kubectl logs <pod_name> -c <container> --previous --tail=100` (inspect previous crashed instance logs!)
  - `kubectl get events --sort-by='.metadata.creationTimestamp' -A`
  - `kubectl get endpoints <service_name>` / `kubectl get endpointslices`
  - `kubectl top nodes` / `kubectl top pods`
  - `kubectl debug node/<node_name> -it --image=busybox` (node triage)

## 6. Configuration
- High-Availability Production Deployment Manifest:
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: order-service
    labels:
      app.kubernetes.io/name: order-service
  spec:
    replicas: 3
    selector:
      matchLabels:
        app.kubernetes.io/name: order-service
    template:
      metadata:
        labels:
          app.kubernetes.io/name: order-service
      spec:
        terminationGracePeriodSeconds: 30
        containers:
        - name: app
          image: registry.corp.com/order-service:v1.4.0
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          startupProbe:
            httpGet:
              path: /healthz/startup
              port: 8080
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: 8080
            periodSeconds: 5
            failureThreshold: 2
          livenessProbe:
            httpGet:
              path: /healthz/live
              port: 8080
            periodSeconds: 10
            failureThreshold: 3
  ```

## 7. Hands-on Lab
- **Lab 1: CrashLoopBackOff via Liveness Probe Mismatch**: Application requires 40 seconds to warm up database connection; aggressive 5s liveness probe kills container repeatedly; fix using `startupProbe`.
- **Lab 2: Service with Zero Endpoints**: Service selector has label typo; verify `kubectl get endpoints` reports `<none>`; fix selector to match pod template labels.
- **Lab 3: Pod Stuck in Pending State**: Pod requests 8 CPUs on a 4-CPU node group; inspect `kubectl describe pod` scheduler failure event; adjust resource requests.

## 8. Common Errors
- `CrashLoopBackOff`: Container starts and terminates repeatedly (check `kubectl logs --previous` and exit code).
- `ImagePullBackOff` / `ErrImagePull`: Invalid registry URL, missing image tag, or missing `imagePullSecrets`.
- `OOMKilled` (Exit Code 137): Container exceeded `resources.limits.memory`.
- `CreateContainerConfigError`: Missing ConfigMap or Secret referenced in `envFrom` or `volumeMounts`.
- `0/N nodes available: node(s) had untolerated taint`: Scheduler cannot find a node matching taints.

## 9. Troubleshooting
1. Query Pod status and phase: `kubectl get pods`.
2. Inspect lifecycle events: `kubectl describe pod <name>` (scroll to bottom `Events:`).
3. If CrashLoopBackOff: `kubectl logs <name> --previous` to see why the prior container died.
4. If Pending: inspect scheduler events (`kubectl describe pod`) for resource/taint/PVC failures.
5. If traffic not reaching pod: check `kubectl get endpoints <svc>` and `kubectl describe svc`.

## 10. Production Design
- Always define both `requests` and `limits` for CPU and Memory (Guaranteed or Burstable QoS class).
- Implement `PodDisruptionBudgets` (`PDB`) to guarantee minimum availability during cluster upgrades.
- Enforce Pod Anti-Affinity or `topologySpreadConstraints` to distribute pods across availability zones.

## 11. Security
- Enforce Kubernetes RBAC with least privilege; avoid `cluster-admin` bindings.
- Enable Pod Security Standards (`restricted` profile via namespace label `pod-security.kubernetes.io/enforce: restricted`).
- Block untrusted egress using Calico/Cilium NetworkPolicies.

## 12. Performance
- Configure Horizontal Pod Autoscaler (`HPA`) with custom metrics (Prometheus Adapter).
- Deploy NodeLocal DNSCache to eliminate DNS latency and conntrack exhaustion.

## 13. Interview Scenarios
- **Scenario**: A deployment rollout hangs indefinitely. Existing pods remain running, and new pods are created but never receive traffic. What are the common causes?
  - **Answer**: 
    1. New pods are failing their `readinessProbe` (endpoints are never updated).
    2. Insufficient cluster capacity prevents new pods from scheduling (Pending).
    3. `imagePullBackOff` on the new image.
    4. Quota or LimitRange restrictions exceeded in the namespace.
