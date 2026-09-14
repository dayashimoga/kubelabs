# KubeLabs STRIDE Threat Model & Attack Vector Analysis

## 1. STRIDE Analysis Matrix

| Threat Category | Potential Attack Vector | Applied Platform Mitigation |
| :--- | :--- | :--- |
| **Spoofing** | Attacker impersonating another learner's sandbox session ID | Cryptographically secure random UUIDs (128-bit entropy); sessions tied to authenticated cookies/tokens. |
| **Tampering** | Modifying lab definitions or validation rules from the terminal | Lab definitions are loaded read-only by the backend from disk. The learner container has zero access to host workspace files. |
| **Repudiation** | Denying execution of malicious commands or resource exhaustion | Centralized audit logging of all commands executed through WebSocket terminal and REST exec endpoints. |
| **Information Disclosure**| Container escape exposing host environment variables or AWS credentials | Rootless container isolation; dropped Linux capabilities; no host volumes mounted into containers. Cloud labs use simulated credentials or strictly scoped STS tokens. |
| **Denial of Service** | Fork bombs (`:(){ :|:& };:`) or memory leak bombs (`malloc` loops) | Cgroup limits enforce `pids.max=100` and `memory.max=512Mi`. Fork bombs immediately fail with `Resource temporarily unavailable`. Memory leaks trigger kernel OOMKilled without impacting host. |
| **Elevation of Privilege** | Using SUID binaries inside container to gain host root | `--security-opt=no-new-privileges` + `--cap-drop=ALL` + Rootless user namespace mapping. |

## 2. Blast Radius Containment
If a malicious student attempts to launch a port scan, crypto miner, or network flood:
- Network namespace is isolated on an internal bridge with egress bandwidth limits.
- Background TTL sweeper terminates the container after 30 minutes.
- The host supervisor process terminates any sandbox process that exceeds CPU or RAM budgets.
