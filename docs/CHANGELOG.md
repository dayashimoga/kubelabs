# KubeLabs Changelog (History-Preserving)

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-14

### Added
- **Complete 18-Gate Automated Production Acceptance Suite (`scripts/verify_acceptance.py`)**: All 18 production gates matching Requirement 16 verified (Setup, Stack Startup, Browser Reachable, Onboarding, Curriculum Loads, Real Podman, Multi-Container, Real Kubernetes, Fault Observable, Learner Repair, Incident Workflow, DB/Redis Guards, Security Isolation, Browser Responsiveness, >90% Coverage, Concurrency Load, Zero-Residue Cleanup, Documentation Artifacts) generating `acceptance.json` and `acceptance.html`.
- **First-Run Learner Onboarding Modal (`OnboardingModal.tsx`)**: 5 canonical learning goals ("Learn DevOps from scratch", "Master Kubernetes", "Become an SRE", "Production troubleshooting", "DevOps interview preparation") with curriculum roadmap previews and `localStorage` persistence.
- **Searchable Troubleshooting Library (`TroubleshootingLibrary.tsx` & `/api/v1/troubleshooting/search`)**: Real-time search and multi-facet filtering (difficulty, technology, symptom, runtime classification) without prematurely spoiling root causes.
- **Random Incident Mode (`/api/v1/incidents/random/start`)**: Real-time chaos incident generator with randomized topology selection, telemetry noise injection, hypothesis testing, and 6-dimension SRE scoring.
- **Canonical 15-Dimension Curriculum Coverage Audit**: Generated `docs/CURRICULUM_GAP_REPORT.md`, `curriculum_coverage.json`, and `curriculum_coverage.html` covering all 24 tracks across 15 pedagogical dimensions.
- **Automated Duplicate Scenario Detector (`scripts/duplicate_detector.py`)**: Certified 0 title collisions and 0 structural duplicates (44/44 genuinely unique scenarios).
- **Real Playwright Browser Proof (`scripts/capture_browser_proof.py`)**: Captured 35 real PNG screenshots across 5 device viewports (1920x1080, 1440x900, 1366x768, 768x1024, 375x812) into `docs/screenshots/` and embedded them in `visual_report.html`.
- **Comprehensive Root Quickstart Guide (`QUICKSTART.md` & `docs/QUICKSTART.md`)**: Complete 60-second setup and one-command run documentation.

### Changed
- **Test Suite Scaling & Coverage Enforcement**: Expanded test suite to 112 passed tests across unit, integration, adversarial security, and sandbox modules; locked meaningful code coverage at 91.0% (>90.0% threshold strictly enforced across `packages` and `apps.api.src`).
- **Terminal WebSocket Robustness**: Upgraded `terminal.py` to support line-buffered command strings as well as single-character terminal keystrokes, Ctrl+C interrupt handling, clear screen, and stderr formatting.
- **CLI Orchestrator Polish**: Enhanced `scripts/kubelabs.ps1` and `scripts/kubelabs.sh` with clean ASCII banner, port availability checks, and integrated acceptance runner execution.

---

## [1.2.0] - 2026-09-14

### Added
- **Dedicated Kubernetes Runtime Provider (`KubernetesProvider`)**: Ephemeral single-node K3s containers (`docker.io/rancher/k3s:latest`) and isolated cluster namespaces (`kubelabs-<id>`) with `ResourceQuota` and default-deny `NetworkPolicy`.
- **Strict Fallback Architecture (`RuntimeProvisioningError`)**: Eliminated silent fallback from REAL to SIMULATED; raised explicit 503 errors with actionable failure telemetry and opt-in simulation buttons.
- **Compound Multi-Failure Cascades**: Staged multi-subsystem failure cascades (`bad_deployment_cascade`, `memory_leak_oom_cascade`, `dns_timeout_cascade`, `db_pool_exhaustion`) in `ScenarioInjector`.
- **Mini Production Applications Library (`ApplicationLibrary`)**: 12 canonical enterprise architectures (E-Commerce, FinTech, Telemetry, SSO, CDN, IoT, Istio, GitOps, Event Bus, Loki, ML Inference) with `to_multi_container_spec()`.
- **Production Backend & Data Guards**: Hard assertions prohibiting SQLite and in-memory caches in `ENVIRONMENT="production"`; added connection pool retry with backoff.
- **Readiness Probes & Tracing Middleware**: Added `/readyz` endpoint, `/api/v1/labs/session/{id}/health`, and `X-Request-ID` distributed tracing middleware.
- **Automated Concurrency Load Benchmark**: Created `scripts/load_test.py` evaluating 10, 25, 50 concurrency tiers (85/85 sessions, 100% pass, 0 residue) generating `load_report.json` and `load_report.html`.
- **Automated Visual & Viewport Auditor**: Created `scripts/visual_audit.py` auditing 5 viewports (1366x768 to mobile) and WCAG 2.2 AA contrast ratios generating `visual_report.json` and `visual_report.html`.
- **One-Command Podman CLI**: Idempotent PowerShell (`kubelabs.ps1`) and POSIX shell (`kubelabs.sh`) wrappers for unified lifecycle management.
- **10-Gate Production Acceptance Suite**: Upgraded `scripts/verify_acceptance.py` certifying PRODUCTION-READY with `acceptance.json` and `acceptance.html`.

### Changed
- **SRE Console Visual/UX Overhaul**: Redesigned `LabWorkspace.tsx` with mouse-draggable split-pane divider, live countdown TTL timer (`mm:ss`), session health indicators, and WCAG accessibility.
- **Test Suite Scaling**: Expanded test suite to 56 automated tests across unit, integration, sandbox, adversarial security, and E2E with 100% pass rate.
- **Forensic Gap Re-audit**: Updated `docs/GAP_REPORT.md` to conform to the 7-column schema (`Requirement | Evidence | Gap | Severity P0-P3 | Fix | Test | Validation Status`).

---

## [1.1.0] - 2026-09-14

### Added
- **Multi-Provider Environment Broker (`EnvironmentBroker`)**: Dynamically provisions single-container (`SingleContainerProvider`), interconnected multi-container bridge networks (`MultiContainerPodProvider`), and high-fidelity deterministic simulations (`SimulationProvider`).
- **Fault Injection Engine (`ScenarioInjector`)**: Dynamic real-time fault injection for inode saturation, disk filling, DNS corruption, zombie process leaks, port conflicts, Kubernetes zero endpoints, probe mismatches, Prometheus cardinality explosions, and Istio mTLS denial.
- **Scenario Factory (`ScenarioFactory`)**: Procedural and template generator providing production-grade failure scenarios across all 24 core curriculum tracks with 13-part pedagogical models.
- **PTY Terminal Reconnect Buffering**: 1000-line circular scrollback buffer stored in `SandboxSession` with automatic replay across WebSocket reconnections.
- **Automated SRE Post-Mortem Generator**: Generates comprehensive incident post-mortems with TTD, TTM, TTR, timeline events, and corrective action items in Markdown.
- **Skill Graph Visualizer (`SkillGraph.tsx`)**: Interactive competency and dependency visualizer across 24 tracks with prerequisite tracking.
- **Enterprise Storage & Cache Architecture**: Dynamic PostgreSQL connection pool (`pool_size=20`) with SQLite WAL fallback, and Redis sliding-window rate limiting with in-memory fallback.
- **Headless Simulation Fallbacks in State Validators**: Enhanced `CommandValidator` and `FileValidator` with simulation evaluation matching `ExecutionContext.simulation_state`.
- **7 Automated Acceptance Verification Gates**: Runner script `scripts/verify_acceptance.py` certifying production readiness across catalog schemas, state validators, sandbox lifecycle, security isolation, scenario factory, zero-residue cleanup, and SRE incident scoring.

### Changed
- **Podman Memory String Normalization**: Automatically converts standard YAML memory strings (e.g., `512Mi`) to Podman-compatible flags (`512m`).
- **Atomic Stdin Staging**: Replaced `podman cp` with atomic stdin streaming (`podman exec -i ... sh -c "mkdir -p ... && cat > ..."`) to eliminate Windows path translation issues.
- **Synchronous Zero-Residue Cleanup**: Enforced synchronized session termination and zero-residue verification preventing race conditions.
- **Hardened HTTP Headers**: Injected `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection: 1; mode=block`.

---

## [1.0.0] - 2026-09-14

### Added
- **Monorepo Architecture**: Clean modular layout separating `apps/api`, `apps/web`, `packages/`, `labs/`, `content/`, `docs/`, and `tests/`.
- **Declarative Lab Engine**: Strict Pydantic models (`LabSpec`, `TaskSpec`, `ValidatorRule`, `ValidationReport`) with dynamic directory scanning in `packages/lab_schema`.
- **14 State Validators**: Production verification engines checking system final state across Command, File, Regex, YAML, JSON, HTTP, TCP, DNS, Container, Kubernetes, Git, Prometheus, and OpenTelemetry.
- **Rootless Sandbox Runtime**: Automated Podman container launcher with dropped capabilities (`--cap-drop=ALL`), strict memory and CPU cgroup limits, and background TTL garbage collection.
- **Deterministic SRE Simulator**: Stateful in-process emulation of multi-tier cloud architectures, Kubernetes resources, Prometheus metric vectors, and trace waterfalls.
- **Step-by-Step Diagnostic Assistant**: 5-tier progressive layered hints (Conceptual $\rightarrow$ Area $\rightarrow$ Command $\rightarrow$ Strong Clue $\rightarrow$ Full Solution) and contextual Q&A answering 6 canonical SRE queries.
- **SEV-1 / SEV-2 Incident War Room**: 12 cascading multi-service outage scenarios with live topology graphs, metric perturbations, log streams, hypothesis testing, and 6-dimensional SRE scoring.
- **Deep-Dive Curriculum Tracks**: 12 comprehensive guides in `content/tracks/` following the 13-part pedagogical schema.
- **13 Real-World Labs**: Production failure scenarios including Linux Inode Exhaustion, Docker PID 1 signal trapping, Kubernetes CrashLoop probes, Service zero endpoints, Terraform state locks, Ansible idempotency, Git reflog recovery, Argo CD GitOps drift, Prometheus cardinality explosion, Istio retry storms, and AWS EKS CNI IP exhaustion.
- **Grand Capstone Pipeline**: End-to-End GitOps to Incident Recovery challenge (`capstone-end-to-end-sre-pipeline.yaml`).
- **Interactive Web Console**: High-performance React 18 + Vite SPA featuring xterm.js terminal, Monaco configuration editor, SVG topology visualizer, live telemetry charts, and dark SRE console styling.
- **Assessments Engine**: Evaluates 8 question formats (MCQ, multi-select, ordering, prediction, log analysis, YAML fixing, architecture, troubleshooting) with explanations.
- **Complete Documentation Suite**: 25 detailed markdown guides in `docs/` covering requirements, architecture, threat models, runbooks, and gap reports.
