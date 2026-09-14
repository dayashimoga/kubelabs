# Docker, OCI & Container Runtimes Curriculum

## 1. What
Docker and OCI (Open Container Initiative) compliant runtimes (Podman, containerd, CRI-O, runc) package applications with their runtime dependencies into immutable image layers, executing them as isolated Linux processes.

## 2. Why
Containers provide consistency across development and production. However, incorrect base images, bloated build contexts, unhandled PID 1 signals, improper volume permissions, and missing resource limits lead to container crashes, vulnerability exposure, and production outages.

## 3. Architecture
```
+-------------------------------------------------------------+
| CLI Client: podman / docker                                 |
+-------------------------------------------------------------+
| High-Level Runtime: containerd / CRI-O / Podman daemonless |
+-------------------------------------------------------------+
| Low-Level Runtime (OCI Spec): runc / crun                   |
+-------------------------------------------------------------+
| Linux Kernel: Namespaces | Cgroups v2 | Seccomp | OverlayFS |
+-------------------------------------------------------------+
```

## 4. Internals
- **Overlay2 Storage Driver**: Consists of `lowerdir` (read-only image layers), `upperdir` (read-write container layer), and `merged` (unified mount point). Copy-on-Write (CoW) duplicates modified files into `upperdir`.
- **PID 1 and Signal Forwarding**: The process running as PID 1 in a container does not receive default Linux kernel signal handlers (like `SIGTERM`). If the entrypoint script does not use `exec` (e.g. `CMD ["npm", "start"]` vs `CMD ["node", "server.js"]` or `tini` / dumb-init), the application ignores `SIGTERM` on shutdown, hangs for 10 seconds, and gets killed abruptly with `SIGKILL`.
- **Rootless Containers (Podman)**: Uses user namespaces (`subuid` / `subgid`) to map UID 0 inside the container to an unprivileged UID (e.g. 1000) on the host, preventing container escape privilege escalations.
- **OCI Image Spec**: Consists of manifest JSON, configuration JSON (environment, entrypoint, architecture), and tarball layer diffs hashed with SHA256.

## 5. Commands
- Inspection & diagnostics:
  - `podman ps -a` / `docker ps -a`
  - `podman inspect <container_id> --format '{{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}'`
  - `podman logs --tail=100 -f <container_id>`
  - `podman top <container_id> -eo pid,ppid,user,args`
  - `podman stats --no-stream`
  - `podman diff <container_id>` (inspect files modified in upperdir)
- Multi-stage build and image scanning:
  - `podman build -t myapp:latest --target production -f Dockerfile .`
  - `podman history --no-trunc myapp:latest`
  - `trivy image myapp:latest`

## 6. Configuration
- Hardened Production Dockerfile:
  ```dockerfile
  # Build stage
  FROM golang:1.22-alpine AS builder
  WORKDIR /build
  COPY go.mod go.sum ./
  RUN go mod download
  COPY . .
  RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o api .

  # Production runtime stage
  FROM gcr.io/distroless/static-debian12:nonroot
  WORKDIR /app
  COPY --from=builder /build/api /app/api
  USER nonroot:nonroot
  EXPOSE 8080
  ENTRYPOINT ["/app/api"]
  ```

## 7. Hands-on Lab
- **Lab 1: Diagnosing Zombie PID 1 & Signal Ignored**: Create container where shell script traps SIGTERM improperly; observe graceful shutdown failure; fix using `exec` in shell entrypoint.
- **Lab 2: Volume Permission Denied (EACCES)**: Container running as non-root user (UID 1001) mounted to host directory owned by root; diagnose and fix using `chown` and `securityContext.fsGroup`.
- **Lab 3: BuildKit Multi-Stage Cache Invalidation**: Optimize bloated 1.2GB image down to 24MB distroless image while ensuring dependencies cache across CI runs.

## 8. Common Errors
- `Exit Code 137`: Killed by Linux Out-Of-Memory (OOM) killer or forced `kill -9`.
- `Exit Code 126`: Command invoked cannot execute (permission problem or not executable).
- `Exit Code 127`: Command not found (missing binary or wrong shell in minimal Alpine image).
- `OCI runtime create failed: container_linux.go: exec: "...": executable file not found in $PATH`.

## 9. Troubleshooting
1. Check container exit code and termination reason: `podman inspect <name>`.
2. Inspect standard output and error streams: `podman logs --tail=100 <name>`.
3. Check cgroup memory limits and host dmesg: `dmesg -T | grep -i oom`.
4. Validate binary dependencies: `ldd /path/to/binary` inside base image.

## 10. Production Design
- Never run containers as root; use distroless or non-root alpine users.
- Enforce immutable tags (digest pinning e.g. `image@sha256:...`) in production.
- Keep build context minimal with `.dockerignore`.

## 11. Security
- Drop all capabilities: `--cap-drop=ALL` with selective additions.
- Read-only root filesystem: `--read-only` with ephemeral `tmpfs` mounts for temporary writes.
- Continuous vulnerability scanning in CI/CD pipeline via Trivy / Grype.

## 12. Performance
- Utilize multi-stage builds to discard build tools (compilers, SDKs).
- Order Dockerfile instructions from least frequently changing (base dependencies) to most frequently changing (app source code) to maximize layer cache hits.

## 13. Interview Scenarios
- **Scenario**: A container running Node.js crashes with exit code 137. The container limit is set to 512MB. Node.js heap limit is default (1.4GB on 64-bit). Why did it crash and how do you fix it?
  - **Answer**: By default, Node.js V8 heap sizing does not automatically constrain itself to container cgroup limits. The V8 heap grew toward its 1.4GB default, exceeding the container's 512MB cgroup limit. The kernel OOM killer sent SIGKILL (137). Remediation: Pass `--max-old-space-size=384` to `node` in the container entrypoint, leaving sufficient headroom for non-heap native buffers.
