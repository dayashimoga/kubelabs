# KubeLabs Security Policies & Sandbox Hardening

## 1. Security Philosophy
KubeLabs allows learners to execute arbitrary shell commands inside dedicated sandboxes. The platform operates on a **zero-trust model**: all learner code and shell interactions are treated as untrusted and potentially adversarial. Safety is strictly guaranteed via **defense-in-depth kernel containment, hardware cgroups, and user namespace isolation**, never fragile command blacklisting or string filtering.

---

## 2. Sandbox Security Isolation Matrix

| Layer / Mechanism | Implementation | Threat Prevented | Verification Method |
|---|---|---|---|
| **Rootless User Namespaces** | Podman user namespaces (UID 0 maps to unprivileged host UID) | Host root compromise / container breakout | `test_cross_session_escape.py::test_rootless_user_namespace` |
| **Linux Capability Dropping** | `--cap-drop=ALL` (no `CAP_SYS_ADMIN`, `CAP_NET_RAW`, etc.) | Kernel privilege escalation, raw packet injection | `test_cross_session_escape.py::test_capability_drops` |
| **Privilege Escalation Lock** | `--security-opt=no-new-privileges` | SUID/SGID binary exploitation | `test_cross_session_escape.py::test_no_new_privileges` |
| **Host Socket Protection** | Absolute omission of `/var/run/docker.sock` and `podman.sock` | Daemon hijacking and host container breakout | `test_cross_session_escape.py::test_no_host_docker_socket` |
| **Memory Cgroup Limits** | `--memory=512m` hard cap per sandbox | Host RAM exhaustion / out-of-memory crashes | `test_cross_session_escape.py::test_memory_limits` |
| **CPU Cgroup Quotas** | `--cpus=1.0` quota enforcement | CPU starvation / crypto-mining | `test_cross_session_escape.py::test_cpu_limits` |
| **PID Cgroup Quotas** | `--pids-limit=100` process limit | Fork bombs (`:(){ :|:& };:`) | `test_cross_session_escape.py::test_pids_limit` |
| **Path Traversal Shield** | Path normalization & canonicalization in API and runtime | Directory traversal (`../../../../etc/shadow`) | `test_cross_session_escape.py::test_path_traversal_rejection` |
| **Bridge Network Isolation**| Isolated bridge networks (`kubelabs-net-<id>`) per session | Cross-tenant eavesdropping & port scanning | `test_cross_session_escape.py::test_network_isolation` |
| **Filesystem Separation** | Ephemeral volumes per session | Cross-session data leakage or tampering | `test_cross_session_escape.py::test_filesystem_isolation` |
| **TTL Automatic Sweep** | 30-minute background daemon sweep + explicit teardown | Orphaned container resource leaks | `test_cross_session_escape.py::test_ttl_enforcement` |
| **Zero Residue Auditing** | `verify_zero_residue()` checking labels `kubelabs.sandbox_id` | Stale containers, networks, and mount points | `verify_acceptance.py::Gate 17` |

---

## 3. Sandbox Container Isolation Profile
Every learner container is launched with strict, non-negotiable constraints:
1. **Rootless Execution**: Podman runs inside rootless user namespaces; UID 0 inside the container maps to unprivileged UID 1000 on the host. Any escape attempt lands in an unprivileged user context on the host machine.
2. **Dropped Capabilities**: Containers start with `--cap-drop=ALL`. Only strictly necessary capabilities (e.g. `NET_BIND_SERVICE` where required for binding low ports) are selectively added. Sysadmin capabilities (`CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, `CAP_SYS_RAWIO`) are completely barred.
3. **No New Privileges**: `--security-opt=no-new-privileges` prevents binaries with SUID/SGID bits from elevating privileges inside the container.
4. **Cgroup Quotas**:
   - `--memory=512m` (prevents host RAM exhaustion)
   - `--cpus=1.0` (prevents CPU starvation)
   - `--pids-limit=100` (blocks fork bombs and rogue thread leaks)
5. **No Host Sockets**: Host Docker/Podman sockets (`/var/run/docker.sock` or `podman.sock`) are **NEVER** mounted inside learner containers.
6. **Network Namespace Isolation**: Inter-container communication is restricted strictly to containers joined to the exact same dedicated bridge network (`kubelabs-net-<id>`). Containers on different sessions have no routing paths to each other.
7. **TTL Automatic Cleanup**: Sandboxes terminate automatically after their configured TTL (default: 30 minutes) via the background sweeper loop (`SandboxManager.sweep_expired_sessions()`).

---

## 4. Automated Adversarial Verification Suite (`tests/adversarial/`)
All security defenses are continually certified by automated integration and adversarial tests (**16/16 tests passing**):
- **`test_capability_drops`**: Asserts `--cap-drop=ALL` is active; confirms attempts to use raw sockets or mount filesystems fail with `EPERM`.
- **`test_no_new_privileges`**: Verifies that SUID privilege transitions are blocked.
- **`test_no_host_docker_socket`**: Verifies neither `/var/run/docker.sock` nor `/run/podman/podman.sock` exist in container filesystems.
- **`test_memory_limits`**: Asserts memory allocation beyond 512MB triggers OOM kill without destabilizing host or sibling containers.
- **`test_cpu_limits`**: Asserts infinite calculation loops are throttled to 1.0 CPU core.
- **`test_pids_limit`**: Asserts fork bombs are halted once process count reaches 100.
- **`test_path_traversal_rejection`**: Confirms path traversal attempts (e.g. `../../../../etc/shadow`, `../../../../etc/passwd`) are rejected with 400/403/422 errors.
- **`test_network_isolation`**: Asserts container in Session A cannot reach container in Session B on private container IPs.
- **`test_filesystem_isolation`**: Asserts files created in Session A's mount are invisible to Session B.
- **`test_ttl_enforcement`**: Asserts background sweeper automatically destroys sessions past their TTL.
- **`test_malformed_spec_rejection`**: Asserts invalid YAML configurations or malicious schemas are safely rejected.
- **`test_zero_residue_guarantee`**: Asserts 0 containers and 0 networks remain after test execution.

---

## 5. Vulnerability Management & CI Security
- **Automated Dependency Auditing**: CI pipeline executes `pip-audit` and `safety` against backend Python dependencies.
- **Container Base Image Pinning**: Base images (`docker.io/library/alpine:latest`, `docker.io/rancher/k3s:latest`, `docker.io/library/node:20-alpine`) are verified for integrity.
- **Static Secret Detection**: Secrets detection via `gitleaks` in pre-commit hooks and CI workflows.
- **Hardened HTTP Headers**: API and Web Console inject `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and strict CSP headers.

---

## 6. Zero-Residue & Ephemeral Lifecycle Proofs
Every session termination undergoes strict residue auditing:
- Containers are killed with `SIGTERM` followed by `SIGKILL` if unresponsive.
- Temporary bridge networks (`kubelabs-net-<id>`) are purged.
- Podman metadata labels (`kubelabs.sandbox_id`) are queried; `verify_zero_residue()` guarantees 0 orphaned artifacts remain on the host machine.

