# KubeLabs Security Policies & Sandbox Hardening

## 1. Security Philosophy
KubeLabs allows learners to execute arbitrary shell commands inside dedicated sandboxes. The platform assumes all learner code is potentially untrusted or malicious. Consequently, safety is enforced via **defense-in-depth kernel isolation** rather than command blacklisting.

## 2. Sandbox Container Isolation Profile
Every learner container is launched with strict constraints:
1. **Rootless Execution**: Podman runs inside user namespaces; UID 0 inside the container maps to unprivileged UID 1000 on the host. Container escape bugs cannot compromise host root.
2. **Dropped Capabilities**: Containers start with `--cap-drop=ALL`. Only strictly necessary capabilities (e.g. `NET_BIND_SERVICE`) are selectively added.
3. **No New Privileges**: `--security-opt=no-new-privileges` prevents binaries with SUID/SGID bits from elevating privileges inside the container.
4. **Cgroup Quotas**:
   - `--memory=512m` (prevents host RAM exhaustion)
   - `--cpus=1.0` (prevents CPU starvation)
   - `--pids-limit=100` (blocks fork bombs)
5. **No Host Sockets**: Host Docker/Podman sockets (`/var/run/docker.sock` or `podman.sock`) are **NEVER** mounted inside learner containers.
6. **TTL Automatic Cleanup**: Containers terminate automatically after 30 minutes.

## 3. Vulnerability Management
- Automated dependency scanning in CI via `safety` and `pip-audit`.
- Container base images scanned with `trivy` and pinned by digest.
- Secrets detection via `gitleaks` in pre-commit and CI workflows.

## 4. Automated Adversarial Verification Suite (`tests/adversarial/`)
All security defenses are continually verified by automated integration tests:
- **Path Traversal Defense**: Confirms that path traversal attempts (e.g. `../../../../etc/shadow`) are sanitized and rejected.
- **Socket Isolation**: Verifies `/var/run/docker.sock` and `/run/podman/podman.sock` are absent in container filesystems.
- **Capability Drops**: Asserts that containers cannot invoke privileged kernel syscalls or gain root capabilities outside user namespaces.
- **Malformed Spec Rejection**: Asserts that invalid YAML configurations or malicious schemas are safely rejected with 422 HTTP responses.

## 5. Zero-Residue & Ephemeral Lifecycle Proofs
Every session termination undergoes strict residue auditing:
- Containers are killed with `SIGTERM` followed by `SIGKILL` if unresponsive.
- Temporary bridge networks (`kubelabs-net-<id>`) are purged.
- Podman metadata labels (`kubelabs.sandbox_id`) are queried; `verify_zero_residue()` guarantees 0 orphaned artifacts remain.

## 6. Multi-Container Network Bridge Isolation
Multi-container microservice environments run on isolated bridge networks:
- Inter-container communication is restricted strictly to peers within the same sandbox session.
- Containers on different sandbox sessions cannot cross-communicate or inspect adjacent learner traffic.
- Bridge networks are automatically torn down immediately upon session expiry or termination.

