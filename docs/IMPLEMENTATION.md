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
Combines xterm.js, Monaco Editor, interactive SVG topology viewer, and real-time metric jitter simulators into a cohesive, responsive multi-panel SRE command center.
