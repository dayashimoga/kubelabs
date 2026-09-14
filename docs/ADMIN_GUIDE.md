# KubeLabs Administrator & Fleet Operations Guide

## 1. System Administration
Platform administrators oversee user progress, manage compute capacity for container sandboxes, enforce security boundaries, and monitor background TTL garbage collection.

## 2. Podman Container Host Configuration
To enable rootless container execution for learners:
```bash
# Verify user namespaces and subuids
cat /etc/subuid
cat /etc/subgid

# Verify Podman socket and machine status
podman machine list
podman system info
```

## 3. TTL Garbage Collection & Cleanup Policy
The platform runs an automated background thread (`SandboxManager._ttl_sweeper_loop`) that runs every 30 seconds:
- Identifies sandboxes where `now > expires_at` (default TTL: 30 minutes / 1800s).
- Terminates container processes via `podman rm -f`.
- Removes temporary staged directories in `/tmp`.
- Prunes abandoned bridge networks and volumes.

## 4. Manual Fleet Hygiene Commands
In case of host reboot or hard daemon crashes, run the manual prune script:
```bash
# Remove all containers labeled with kubelabs.sandbox_id
podman rm -f $(podman ps -aq --filter "label=kubelabs.sandbox_id")

# Prune anonymous volumes
podman volume prune -f
```

## 5. Multi-User Concurrency Sizing
- **Memory**: Allocate 1GB host RAM per concurrent active sandbox container.
- **CPU**: Allocate 0.25 physical cores per active learner.
- **PIDs**: Ensure `/proc/sys/kernel/pid_max` is set to at least `65536`.
