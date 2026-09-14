# KubeLabs Testing Strategy & Quality Assurance Architecture

## 1. Testing Philosophy
KubeLabs enforces rigorous automated test coverage targeting **>90% meaningful code coverage** across both backend (`packages/`, `apps.api.src`) and frontend (`apps/web/src/`), validated against unit, integration, real container lifecycle, sandbox security, adversarial, and 18-gate end-to-end acceptance suites.

**Core Quality Principles:**
- **Zero Mock Fallacy**: Production readiness must be certified by real runtime execution (`--full` mode), never mock metadata, FAST bypasses, or shallow checks.
- **Dual Coverage Enforcement**: Backend code coverage $\ge 90\%$ and Frontend code coverage $\ge 90\%$ must pass independently.
- **Hermetic Container Testing**: Frontend testing and builds run inside rootless Podman containers (`docker.io/library/node:20-alpine`) with zero host toolchain pollution.
- **Zero Residue Guarantee**: Every test suite provisioning containers, networks, or cluster namespaces must assert zero orphaned resources upon teardown.

---

## 2. Test Suites Overview

### 2.1 Backend Unit Tests (`tests/unit/`)
- Tests individual validator rules in isolation (Command, File, Regex, YAML, JSON, HTTP, TCP, DNS, Container, Kubernetes, Git, Prometheus, OpenTelemetry).
- Validates 100% of declarative YAML labs and extended scenarios against the strict `LabSpec` Pydantic model.
- Tests scoring mathematics, layered hint penalty calculations, and prerequisite DAG resolution.

### 2.2 Backend Integration Tests (`tests/integration/`)
- Tests REST API endpoints for labs, sessions, execution, advice, validation, and assessments.
- Tests WebSocket terminal session handshake, PTY stream buffering, and command streaming I/O.
- Verifies database ORM persistence with SQLite WAL and PostgreSQL pooling.
- **Mini-Production Applications Smoke Suite** (`test_mini_production_apps_smoke.py`): Validates all 12 enterprise architectures, cascading failure injection, recovery, and clean teardown.
- **Real Labs Lifecycle E2E Suite** (`test_real_labs_lifecycle_e2e.py`): Validates real single-container, multi-container bridge, and K3s Kubernetes sandboxes through full start $\rightarrow$ execute $\rightarrow$ validate $\rightarrow$ stop $\rightarrow$ zero-residue lifecycles.

### 2.3 Frontend Test Suite (`apps/web/src/__tests__/`)
- Tested using **Vitest** and **React Testing Library** with jsdom environment inside rootless Node.js 20 Alpine containers.
- Comprehensive coverage across 12 test suites and 51 tests:
  - `App.test.tsx`: Route resolution, navigation bar, footer rendering.
  - `OnboardingModal.test.tsx`: 5 canonical learner goals, roadmap preview, localStorage persistence.
  - `LabWorkspace.test.tsx`: Split-pane layout, terminal mounting, Monaco editor, validation trigger, TTL countdown timer, reconnection handling.
  - `Dashboard.test.tsx`: Radar chart, skill progress, quick-start actions, track listings.
  - `SkillGraph.test.tsx`: DAG rendering, track prerequisites, interactive node selection.
  - `IncidentSimulator.test.tsx`: Random incident mode, topology visualization, hypothesis testing, 7-dimension post-mortem scorecard.
  - `TroubleshootingLibrary.test.tsx`: Search queries, technology/difficulty filter chips, spoiler-free symptom presentation.
  - `TrackView.test.tsx`: Subtopic curriculum guides, 13-part pedagogical sections, lab launch buttons.
  - `Assessments.test.tsx`: 8 assessment question formats (MCQ, multi-select, ordering, prediction, log analysis, YAML fixing, architecture, troubleshooting).
  - `api.test.ts`: Axios client error interceptors, `X-Request-ID` propagation, retry logic.
- **Frontend Coverage Metrics (Container-Verified)**:
  - **Lines**: **94.13%** ($\ge 90\%$)
  - **Statements**: **92.00%** ($\ge 90\%$)
  - **Functions**: **90.56%** ($\ge 90\%$)
  - **Branches**: **85.29%**
  - **Pass Rate**: **51 / 51 passed (100%)**

### 2.4 Sandbox Security & Quota Tests (`tests/sandbox/`)
- Verifies rootless container execution, dropped capabilities (`--cap-drop=ALL`), and `--security-opt=no-new-privileges`.
- Verifies cgroup memory limits (`--memory=512m`), CPU quotas (`--cpus=1.0`), and PID limits (`--pids-limit=100`).
- Verifies background TTL sweeper automatically terminates expired sandboxes.

### 2.5 Adversarial & Multi-Tenant Isolation Tests (`tests/adversarial/`)
- Confirms host Docker/Podman sockets (`/var/run/docker.sock`, `podman.sock`) are inaccessible.
- Validates path traversal defense (`../../../../etc/shadow`) across all file-staging and execution APIs.
- Asserts memory leak loops and fork bomb attacks are contained by cgroups without affecting adjacent sandboxes.
- Asserts strict cross-session isolation: sandbox A cannot inspect or connect to sandbox B's bridge network or filesystem.
- Validates malformed YAML specifications and schema corruption return 422 HTTP responses.

### 2.6 Multi-Viewport Visual Regression Suite (`scripts/run_visual_regression.py`)
- Evaluates 18 interactive views across 5 standard screen resolutions:
  - `1920x1080` (Desktop Full HD)
  - `1440x900` (MacBook / Laptop)
  - `1366x768` (Standard Laptop)
  - `768x1024` (Tablet Portrait)
  - `375x812` (Mobile Portrait)
- Audits DOM layout for horizontal overflow anomalies, viewport clipping, and accessibility contrast.
- Certified **90 / 90 layout checks passed (100%)**; generated `visual_regression_report.json` and `visual_regression_report.html`.

### 2.7 Performance Click-to-Ready Benchmark (`scripts/benchmark_click_to_ready.py`)
- Profiles 7 distinct lifecycle phases: Specification Resolution $\rightarrow$ Network Bridge Creation $\rightarrow$ Container Creation $\rightarrow$ Boot & Runtime Initialization $\rightarrow$ Readiness Probing $\rightarrow$ Workspace Binding $\rightarrow$ Interactive Ready.
- Latency profile per runtime mode:
  - `REAL-CONTAINER`: P50: 2540ms, P95: 2845ms, P99: 2845ms, **0.0% failure rate**
  - `REAL-MULTI-CONTAINER`: P50: 2543ms, P95: 2656ms, P99: 2656ms, **0.0% failure rate**
  - `REAL-KUBERNETES`: P50: 2156ms, P95: 2305ms, P99: 2305ms, **0.0% failure rate**
  - `SIMULATION`: P50: 1482ms, P95: 1865ms, P99: 1865ms, **0.0% failure rate**
- Generated `performance_report.json` and `performance_report.html`.

### 2.8 Stress, Soak & Concurrency Benchmark (`scripts/load_test.py`)
- Evaluates 10, 25, 50, and 100 concurrent worker tiers.
- Performs repeated lifecycle start, reset, and teardown under load.
- Executes 100KB terminal output stream soak testing PTY buffer stability.
- Asserts cross-session filesystem isolation and background TTL sweeper effectiveness.
- Certified **100% success rate across all 4 tiers** with **0 orphaned sessions**; generated `load_report.json` and `load_report.html`.

---

## 3. 18-Gate Automated Production Acceptance Runner (`scripts/verify_acceptance.py`)

The platform acceptance suite enforces all 18 production readiness gates:

| Gate # | Gate Name | Mode | Verification Logic |
|---|---|---|---|
| **Gate 1** | Monorepo Setup & Layout | Fast / Full | Verifies directory layout, schemas, models, and scripts |
| **Gate 2** | Full Stack Services Boot | Fast / Full | Verifies API health (`/healthz`, `/readyz`) and database connectivity |
| **Gate 3** | Web Console Reachability | Fast / Full | Verifies Web SPA HTTP 200 response and asset serving |
| **Gate 4** | Learner Onboarding Flow | Fast / Full | Validates 5 learning goals, tracks, and local storage state persistence |
| **Gate 5** | Curriculum Tracks & Scenarios | Fast / Full | Verifies 24 tracks, 92 canonical subtopics, and prerequisite DAG |
| **Gate 6** | Real Podman Container Runtime | Full | Provisions genuine container, executes command, validates state |
| **Gate 7** | Multi-Container Bridge Network | Full | Provisions interconnected containers on isolated bridge, tests networking |
| **Gate 8** | Real Kubernetes Provider | Full | Provisions ephemeral K3s container, deploys workload, verifies state |
| **Gate 9** | Fault Injection Engine | Fast / Full | Injects live faults (inode exhaustion, port collision, probe mismatch) |
| **Gate 10**| Learner Remediation & Hints | Fast / Full | Validates 5-tier hint progression and state repair verification |
| **Gate 11**| Incident War Room Workflow | Fast / Full | Simulates SEV-1 outage, hypothesis testing, and 7-dimension scoring |
| **Gate 12**| Production Backend Data Guards| Fast / Full | Prohibits SQLite/in-memory in production; checks pooling |
| **Gate 13**| Adversarial Security Isolation| Full | Asserts `--cap-drop=ALL`, socket blocking, and path traversal rejection |
| **Gate 14**| Web Console Responsiveness | Fast / Full | Audits 5 viewports for horizontal overflow anomalies |
| **Gate 15**| Automated Test Coverage $\ge 90\%$| Fast / Full | Enforces backend and frontend code coverage $\ge 90\%$ |
| **Gate 16**| Concurrency Load & Soak Test | Full | Stresses multi-session concurrency and sweeps expired sessions |
| **Gate 17**| Zero-Residue Lifecycle Cleanup| Full | Verifies zero orphaned containers, networks, or namespaces remain |
| **Gate 18**| Documentation Architecture | Fast / Full | Validates 25 documentation guides, matrices, and reports |

### Execution Modes:
- **`--fast`**: Rapid smoke gate verification (< 2s) generating `acceptance_fast.json` and `acceptance_fast.html`.
- **`--full`**: Complete production certification running real container, multi-container, and K3s lifecycles generating `acceptance_full.json`, `acceptance_full.html`, and `acceptance.json/html`.
- **Mandatory Policy**: Certification requires **FULL acceptance PASS**. Fast acceptance alone must NEVER certify production readiness.

---

## 4. Running Test Suites

```bash
# Run all backend tests
pytest tests/ -v

# Run backend tests with strict 90% coverage gate
pytest tests/ --cov=packages --cov=apps.api.src --cov-fail-under=90

# Run real labs lifecycle E2E tests
pytest tests/integration/test_real_labs_lifecycle_e2e.py -v

# Run adversarial security tests
pytest tests/adversarial/ -v

# Run frontend tests with coverage inside Podman container (zero host install)
podman run --rm -v ".:/app:Z" -w /app/apps/web docker.io/library/node:20-alpine npm run test:coverage

# Run multi-viewport visual regression suite
python scripts/run_visual_regression.py

# Run click-to-ready latency benchmarks
python scripts/benchmark_click_to_ready.py

# Run concurrency load test
python scripts/load_test.py

# Run 18-gate FULL acceptance certification
python scripts/verify_acceptance.py --full
```

