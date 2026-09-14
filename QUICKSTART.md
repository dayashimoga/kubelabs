# KubeLabs Quickstart Guide

Get up and running with KubeLabs in under 60 seconds with zero host tool dependencies beyond Podman.

---

## 1. Prerequisites

* **Podman** 4.0+ (Rootless recommended) or **Docker**
* **PowerShell 7+** (Windows) or **Bash / POSIX shell** (Linux / macOS)
* Web Browser (Chrome, Firefox, Edge, Safari)

No local Node.js, Python, or database installations are required. Everything executes inside isolated container sandboxes.

---

## 2. Launching KubeLabs (One Command)

### On Windows (PowerShell):
```powershell
# 1. Clone repository
git clone https://github.com/dayashimoga/kubelabs.git
cd kubelabs

# 2. Start full stack (Web UI, API, PostgreSQL, Redis, Worker)
.\scripts\kubelabs.ps1 up
```

### On Linux / macOS (Bash):
```bash
# 1. Clone repository
git clone https://github.com/dayashimoga/kubelabs.git
cd kubelabs

# 2. Make executable & start full stack
chmod +x scripts/kubelabs.sh
./scripts/kubelabs.sh up
```

---

## 3. Platform Endpoints

Once initialized, the orchestrator prints the live health banner:

```text
======================================================================
  KubeLabs Production SRE & Kubernetes Learning Platform READY
======================================================================

  Web UI:       http://localhost:3000
  API Gateway:  http://localhost:8000
  API Docs:     http://localhost:8000/docs
  Metrics:      http://localhost:8000/metrics

  Web           [HEALTHY]
  API           [HEALTHY]
  PostgreSQL    [HEALTHY]
  Redis         [HEALTHY]
  Lab Worker    [HEALTHY]
  Podman        [HEALTHY]
  Kubernetes    [AVAILABLE]
======================================================================
```

---

## 4. First-Run Learner Workflow

1. **Open Web UI**: Navigate to [http://localhost:3000](http://localhost:3000)
2. **Choose Your Learning Goal**: The interactive onboarding modal presents 5 focused tracks:
   * *Learn DevOps from scratch* (Linux, Git, Containers, CI/CD fundamentals)
   * *Master Kubernetes* (Core objects, scheduling, networking, storage, Helm)
   * *Become an SRE* (SLO/SLI, observability, incident response, chaos testing)
   * *Production Troubleshooting* (CrashLoopBackOff, OOMKilled, DNS, locks)
   * *DevOps Interview Prep* (Realistic scenario break/fix and architecture design)
3. **Start Your First Lab**:
   * Inspect the diagnostic symptoms in the lab panel.
   * Open the interactive terminal directly in the browser.
   * Troubleshoot using real diagnostic commands (`kubectl describe`, `df -i`, `curl`, `dmesg`).
   * Apply corrective actions.
   * Click **Validate Task** for automated real-time state validation.
4. **Try Random Incident Mode**:
   * Click **Incidents** in navigation → **Start Random Incident**.
   * Resolve live outages scored across 6 SRE dimensions (*Detection, Investigation, Root Cause, Fix, Verification, Prevention*).
   * Receive an automated production Post-Mortem.

---

## 5. CLI Management Commands

| Command | PowerShell (`kubelabs.ps1`) | Bash (`kubelabs.sh`) | Description |
| :--- | :--- | :--- | :--- |
| **Setup** | `.\scripts\kubelabs.ps1 setup` | `./scripts/kubelabs.sh setup` | Prepares container images and networks |
| **Up** | `.\scripts\kubelabs.ps1 up` | `./scripts/kubelabs.sh up` | Starts all services with health verification |
| **Status** | `.\scripts\kubelabs.ps1 status` | `./scripts/kubelabs.sh status` | Checks health of all stack components |
| **Logs** | `.\scripts\kubelabs.ps1 logs` | `./scripts/kubelabs.sh logs` | Streams consolidated logs across containers |
| **Test** | `.\scripts\kubelabs.ps1 test` | `./scripts/kubelabs.sh test` | Runs unit, integration & sandbox tests |
| **Acceptance** | `.\scripts\kubelabs.ps1 acceptance` | `./scripts/kubelabs.sh acceptance` | Validates all 18 production gates |
| **Reset** | `.\scripts\kubelabs.ps1 reset` | `./scripts/kubelabs.sh reset` | Resets all active lab environments |
| **Cleanup** | `.\scripts\kubelabs.ps1 cleanup` | `./scripts/kubelabs.sh cleanup` | Removes stale sandbox containers/networks |
| **Down** | `.\scripts\kubelabs.ps1 down` | `./scripts/kubelabs.sh down` | Stops stack with zero residual footprints |

---

## 6. Verification and Quality Gates

Execute the full production acceptance test:
```bash
python scripts/verify_acceptance.py
```
This generates `acceptance.json` and `acceptance.html` verifying:
* Zero-residue sandbox lifecycle
* Socket isolation and capability drops
* 15-dimension curriculum coverage
* >90% code coverage across application and packages
* WCAG 2.2 AA accessibility across 5 device viewports
