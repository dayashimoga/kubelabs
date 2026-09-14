# KubeLabs Technical Design Document

## 1. Domain Modeling & Schema Architecture

### 1.1 Lab Definition Schema
Every lab is declared in an independent, versioned YAML specification conforming to `LabSpec`:
```yaml
id: string (slug e.g. 'linux-inode-exhaustion')
version: string (semver '1.0.0')
title: string
track: string
difficulty: enum ['beginner', 'intermediate', 'advanced', 'production']
estimated_minutes: integer
validation_status: enum ['PROVEN', 'SIMULATION-PROVEN', 'IMPLEMENTED-UNPROVEN', 'HARDWARE/CLOUD-REQUIRED']
environment: EnvironmentSpec
initial_state: InitialStateSpec
tasks: List[TaskSpec]
cleanup_policy: CleanupPolicy
scoring: ScoringSpec
```

### 1.2 State Verification Protocol
Verification operates on **actual system state** rather than command string matching. Naive platforms search `.bash_history` or regex command inputs, which fails when users use alternative commands (e.g., `awk` instead of `cut`, or editing a file with `vi` vs `sed`).

The KubeLabs `ValidatorEngine` invokes specialized domain validators:
- `CommandValidator`: Executes non-mutating validation check inside container; asserts exit code, stdout/stderr regex.
- `FileValidator`: Inspects path existence, permissions (octal), size, SHA-256 hash, and content substrings.
- `YamlValidator` & `JsonValidator`: Evaluates JMESPath / dot-notation key paths against parsed YAML/JSON documents.
- `HttpValidator`: Sends HTTP GET/POST requests, asserts response status code, headers, and body snippets.
- `TcpValidator`: Opens raw socket connection with timeout to verify port listening state.
- `DnsValidator`: Queries DNS records (`socket.gethostbyname`) to verify hostname resolution.
- `ContainerValidator`: Queries container runtime (`podman inspect`) for status, restart count, and OOMKilled state.
- `KubernetesValidator`: Evaluates Pod phase, Ready conditions, Endpoints presence, and PVC binding.
- `GitValidator`: Evaluates clean worktree, branch head, and commit history.
- `PrometheusValidator`: Evaluates PromQL vector thresholds (`operator: '>', threshold: 10`).
- `OpenTelemetryValidator`: Queries distributed trace spans for operation name and error tags.

## 2. Sandbox Security Architecture

```
+-------------------------------------------------------------+
| Host OS (Linux / Windows Host)                              |
+-------------------------------------------------------------+
| Podman Rootless Engine                                      |
|   User Namespace Mapping: UID 0 in container -> UID 1000 host|
+-------------------------------------------------------------+
| Container Security Profile:                                 |
|   --security-opt=no-new-privileges                          |
|   --cap-drop=ALL --cap-add=NET_BIND_SERVICE                 |
|   --memory=512m --cpus=1.0 --pids-limit=100                 |
|   --read-only (optional)                                    |
|   Labels: kubelabs.sandbox_id, kubelabs.ttl                 |
+-------------------------------------------------------------+
```

## 3. Incident Simulator State Machine
Incidents progress through a strict SRE lifecycle:
$$\text{Triggered} \longrightarrow \text{Acknowledged} \longrightarrow \text{Investigating} \longrightarrow \text{Mitigating} \longrightarrow \text{Resolved}$$

Telemetry perturbation is dynamically computed:
- When status is `Triggered` or `Investigating`, metrics endpoints inject randomized 5xx error spikes (15-25%), elevated P99 latencies (3000-5000ms), and error logs.
- When valid mitigation is executed, the session enters `Mitigating`, returning metrics and log streams to baseline.
- When learner triggers `resolve`, the engine scores:
  $$S_{\text{total}} = \frac{S_{\text{detect}} + S_{\text{investigate}} + S_{\text{root\_cause}} + S_{\text{fix}} + S_{\text{verify}} + S_{\text{prevent}}}{6} - P_{\text{hints}}$$
