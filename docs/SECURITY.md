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
