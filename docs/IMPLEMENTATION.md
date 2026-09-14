# KubeLabs Technical Implementation Details

## 1. Implementation Methodology
KubeLabs was developed sprint-by-sprint following a strict engineering workflow:
$$\text{inspect} \rightarrow \text{design} \rightarrow \text{implement} \rightarrow \text{test} \rightarrow \text{fix} \rightarrow \text{security-check} \rightarrow \text{E2E} \rightarrow \text{acceptance} \rightarrow \text{document} \rightarrow \text{update status} \rightarrow \text{gap analysis}$$

## 2. Core Implementation Highlights

### 2.1 State-Based Validation Engine (`packages/validator_core`)
Validators inspect final state instead of matching command strings:
```python
# CommandValidator evaluates exit code and regex
exit_code, stdout, stderr = executor.exec_command(container_id, rule.target)
passed = (exit_code == expected_exit_code)
if output_regex and not re.search(output_regex, stdout):
    passed = False
```
Similarly, `YamlValidator` parses manifests with `yaml.safe_load` and traverses nested paths (`spec.template.spec.containers.0.resources.limits.memory`) to assert precise values.

### 2.2 Podman Sandbox Security Hardening (`packages/sandbox_runtime`)
Containers are spawned with security profiles:
```python
cmd = [
    "podman", "run", "-d",
    "--name", container_name,
    f"--memory={env_spec.memory_limit}",
    f"--cpus={env_spec.cpu_limit}",
    f"--pids-limit={env_spec.pids_limit}",
    "--security-opt=no-new-privileges",
    "--cap-drop=ALL",
    f"--label=kubelabs.sandbox_id={sandbox_id}",
    f"--label=kubelabs.ttl={ttl_seconds}",
]
```

### 2.3 WebSocket PTY Streaming (`apps/api/src/api/terminal.py`)
Provides interactive shell I/O streaming with ANSI terminal rendering, escape sequence processing, backspace handling, and command execution in containers or simulators.

### 2.4 Frontend Workspace Assembly (`apps/web`)
Combines xterm.js, Monaco Editor, interactive SVG topology viewer, real-time metric jitter simulators, and interactive `SkillGraph` into a cohesive, responsive multi-panel SRE command center.

### 2.5 Multi-Provider Environment Broker (`packages/sandbox_runtime/src/broker.py`)
Orchestrates heterogeneous execution backends transparently:
- **`SingleContainerProvider`**: Rootless Podman container with `--cap-drop=ALL` and cgroup quotas.
- **`MultiContainerPodProvider`**: Spawns isolated bridge networks (`kubelabs-net-<id>`) with interconnected microservice containers (e.g. frontend, gateway, auth, database) with internal DNS discovery.
- **`SimulationProvider`**: Deterministic state machine simulating kernel syscalls, Kubernetes clusters, and cloud telemetry.

### 2.6 Dynamic Fault Injection Engine (`packages/sandbox_runtime/src/scenario_injector.py`)
Injects real and simulated failure modes:
- Filesystem: Inode filling, disk block saturation.
- Networking: DNS resolution breakage, TCP port contention, latency injection.
- Orchestration: Kubernetes zero endpoint services, readiness probe mismatches, CrashLoopBackOff.
- Observability: Prometheus high-cardinality explosions, Istio mTLS handshake rejections.

### 2.7 Cross-Platform Atomic File Staging via Stdin Streaming (`executor.py`)
To prevent Windows path mangling during `podman cp`, files are staged atomically over standard input:
```python
cmd = [self.podman, "exec", "-i", container_id, "sh", "-c", f"mkdir -p {target_dir} && cat > '{target_path}'"]
subprocess.run(cmd, input=content, text=True, check=True, timeout=15)
```

### 2.8 Curriculum Scenario Factory across 24 Tracks (`packages/lab_schema/src/scenario_factory.py`)
Generates standardized, pedagogically complete failure scenarios adhering to the 13-part curriculum model with 5-tier layered hints and state validator rules.

### 2.9 Automated SRE Post-Mortem Generator (`packages/incident_core/src/engine.py`)
Analyzes learner investigation timelines and generates structured Markdown post-mortems computing Time-To-Detect (TTD), Time-To-Mitigate (TTM), Time-To-Resolve (TTR), and 6D SRE scorecards.

### 2.10 Zero-Residue Lifecycle Verification (`manager.py`)
Guarantees clean tear down by synchronizing container stopping, network purging, and inspecting Podman labels (`kubelabs.sandbox_id`) to certify zero leftover artifacts.
