# Linux Internals & SRE Troubleshooting Curriculum

## 1. What
Linux is the foundational operating system kernel powering modern cloud-native infrastructure, containers, and hypervisors. It manages CPU scheduling, virtual memory, network stacks, block devices, and process isolation.

## 2. Why
Modern containers (Docker, Podman, containerd, CRI-O) do not run an isolated OS—they are simply standard Linux processes bounded by Linux kernel primitives: namespaces, cgroups, seccomp, and LSMs (AppArmor/SELinux). Troubleshooting cloud-native failures requires mastering the underlying Linux kernel behaviors.

## 3. Architecture
```
+-------------------------------------------------------------+
|                      User Space                             |
|  Applications | Shells | Daemons (systemd, kubelet, dockerd) |
|  C Library (glibc / musl libc)                              |
+-------------------------------------------------------------+
|               System Call Interface (syscalls)              |
+-------------------------------------------------------------+
|                      Kernel Space                           |
|  Process Scheduler (CFS/EEVDF) | Memory Manager (Page Table)|
|  VFS (Virtual Filesystem)     | Network Stack (TCP/IP/eBPF)|
|  IPC | Device Drivers         | Cgroups & Namespaces        |
+-------------------------------------------------------------+
|                      Hardware Layer                         |
|  CPU | Physical RAM | Block Storage (NVMe/SSD) | NICs       |
+-------------------------------------------------------------+
```

## 4. Internals
- **Namespaces**: PID (process tree), NET (IP addresses, routing tables, iptables), MNT (isolated mount points), IPC (System V / POSIX message queues), UTS (hostnames), USER (UID/GID mappings), CGROUP (virtualized cgroup view).
- **Cgroups (v1 vs v2)**: Cgroups v2 uses a unified hierarchy under `/sys/fs/cgroup`. Controllers: `memory.max`, `cpu.max`, `pids.max`, `io.weight`. OOM Killer triggers when `memory.current` exceeds `memory.max` or system RAM is exhausted.
- **Inodes**: A data structure on a filesystem (ext4, xfs) describing a filesystem object such as a file or directory. Each inode stores size, permissions, owner, timestamps, and block pointers. A filesystem has a fixed number of inodes allocated at creation (`mkfs`). When inodes are exhausted, no new files or directories can be created, even if gigabytes of raw block capacity remain.
- **VFS and Page Cache**: Dirty pages are flushed by `flusher` kernel threads. Memory pressure invokes `kswapd` to reclaim inactive file pages and swap anonymous pages.
- **Zombie Processes**: A process that has finished execution (via `exit()`) but still has an entry in the process table because its parent has not yet read its exit status via `wait()` / `waitpid()`. Zombies consume process IDs (PIDs). If PID space (`/proc/sys/kernel/pid_max`) is exhausted, no new processes can be spawned.

## 5. Commands
- Diagnostic triage:
  - `top`, `htop`, `vmstat 1 5`, `mpstat -P ALL 1`
  - `free -m`, `cat /proc/meminfo`, `slabtop`
  - `df -h` (block space), `df -i` (inode utilization)
  - `lsof -i :<port>`, `ss -tlpn`, `netstat -s`
  - `pidof`, `pgrep`, `ps aux --sort=-%mem | head -n 15`
  - `strace -p <PID> -f -e trace=network,file`
  - `perf top`, `dmesg -T | grep -E -i "oom|killed|error"`
  - `journalctl -u <service> --no-pager -n 100`

## 6. Configuration
- `/etc/security/limits.conf` (nofile, nproc, memlock)
- `/etc/sysctl.conf`:
  - `vm.max_map_count = 262144` (Elasticsearch/Kafka requirements)
  - `vm.overcommit_memory = 1`
  - `net.core.somaxconn = 65535`
  - `net.ipv4.ip_local_port_range = 10240 65535`
  - `net.ipv4.tcp_tw_reuse = 1`
  - `fs.file-max = 2097152`
  - `fs.inotify.max_user_watches = 524288`

## 7. Hands-on Lab
- **Lab 1: Inode Exhaustion Remediation**: Diagnose disk write errors with 40GB free disk space; use `df -i` to locate millions of zero-byte session spool files in `/var/spool/clientmqueue`; remediate using safe xargs/find deletion.
- **Lab 2: Zombie Process Hunting**: Locate zombie processes (`Z` state in `ps aux`), trace parent PID (PPID), send `SIGCHLD` to parent, and gracefully reap child entries.
- **Lab 3: Ephemeral Port Exhaustion**: Diagnose `dial tcp: cannot assign requested address` under high load; inspect `ss -s` TIME_WAIT sockets; tune `net.ipv4.tcp_tw_reuse` and port ranges.

## 8. Common Errors
- `No space left on device` despite `df -h` showing available blocks (Inode exhaustion or unlinked open files held by processes).
- `fork: retry: Resource temporarily unavailable` (`pids.max` or `ulimit -u` exceeded).
- `Too many open files` (`ulimit -n` or `fs.file-max` reached).
- `Killed` (Linux kernel OOM Killer SIGKILL 137).

## 9. Troubleshooting
1. Observe symptom: command error message, exit code, or alert.
2. Check resource saturation: CPU (`uptime`, `vmstat`), Memory (`free -m`), Disk blocks (`df -h`), Inodes (`df -i`), Open file descriptors (`lsof | wc -l`), PIDs (`ps aux | wc -l`).
3. Inspect kernel ring buffer: `dmesg -T` for OOM notifications or hardware I/O errors.
4. Formulate hypothesis $\rightarrow$ Run specific diagnostic probe $\rightarrow$ Execute fix $\rightarrow$ Verify with non-mutating check.

## 10. Production Design
- Isolate system services from application workloads using dedicated cgroup slices (`system.slice` vs `user.slice`).
- Allocate separate mount points for `/var/log`, `/var/lib/docker`, `/tmp`, and data directories to prevent cascading root partition lockup.
- Configure logrotate with maxsize and retention constraints on all high-throughput services.

## 11. Security
- Enforce least privilege: Run daemons under non-root service accounts.
- Restrict kernel capabilities (`cap_drop=ALL`).
- Apply seccomp profiles to block dangerous syscalls (`ptrace`, `reboot`, `kexec_load`).
- Keep kernel updated for privilege escalation CVEs (Dirty COW, Dirty Pipe, etc.).

## 12. Performance
- Utilize eBPF tools (`bcc`, `bpftrace`, `execsnoop`, `opensnoop`, `tcprtt`) for zero-overhead kernel telemetry.
- Choose appropriate I/O schedulers (`mq-deadline`, `kyber`, `none` for fast NVMe storage).
- Configure Transparent Huge Pages (`madvise` mode) for memory-intensive databases.

## 13. Interview Scenarios
- **Scenario**: A web server is returning 500 errors. `df -h` shows `/var/log` is 100% full. You run `rm /var/log/app.log`, but `df -h` still reports 100% used. Why?
  - **Answer**: The file was unlinked from the directory tree, but the application daemon still holds an active file descriptor open to the inode. The filesystem cannot free the allocated disk blocks until all active descriptors are closed. Run `lsof | grep deleted` to find the process and execute `kill -HUP <PID>` or `truncate -s 0 /proc/<PID>/fd/<FD>`.
- **Scenario**: What happens when a process allocates memory beyond the container's cgroup limit?
  - **Answer**: The kernel cgroup memory controller detects that `memory.current > memory.max`. If page reclaim fails to free memory below the limit, `oom-killer` is invoked. The kernel calculates the badness score (primarily memory proportion) and sends `SIGKILL` (signal 9, exit code 137) to the offending process.
