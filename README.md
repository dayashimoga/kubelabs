# KubeLabs: Production-Ready DevOps & SRE Learning Platform

[![CI](https://github.com/dayan/kubelabs/actions/workflows/ci.yml/badge.svg)](https://github.com/dayan/kubelabs/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://python.org)
[![Node: 20+](https://img.shields.io/badge/Node-20+-green.svg)](https://nodejs.org)
[![Podman: 5.x](https://img.shields.io/badge/Podman-5.x-purple.svg)](https://podman.io)

KubeLabs is an enterprise-grade, hands-on learning, troubleshooting, and incident simulation platform designed to build real muscle memory for DevOps engineers, Cloud Architects, and Site Reliability Engineers (SREs).

$$\text{Learn} \longrightarrow \text{Practice} \longrightarrow \text{Break} \longrightarrow \text{Troubleshoot} \longrightarrow \text{Fix} \longrightarrow \text{Validate} \longrightarrow \text{Explain} \longrightarrow \text{Assess} \longrightarrow \text{Master}$$

---

## ⚡ Key Highlights

- **Declarative YAML Lab Engine**: Versioned, reproducible labs with state-based assertions across 14 domains (Command, File, Regex, YAML, JSON, HTTP, TCP, DNS, Container, Kubernetes, Git, Prometheus, OpenTelemetry).
- **Hardened Rootless Sandbox**: Automated Podman container launcher with dropped capabilities (`--cap-drop=ALL`), cgroup CPU/memory quotas, no host sockets, and automated 30-minute background TTL cleanup.
- **Deterministic SRE Simulator**: Stateful in-process emulation of multi-tier cloud architectures, Kubernetes control planes, PromQL metrics vectors, and trace waterfalls.
- **Step-by-Step Diagnostic Assistant**: Contextual guidance with 5 progressive hint tiers (Conceptual $\rightarrow$ Area $\rightarrow$ Command $\rightarrow$ Clue $\rightarrow$ Solution) and answering canonical SRE queries without spoiling solutions.
- **SEV-1 / SEV-2 Incident War Room**: 12 cascading multi-service production outages with live topology, real-time alert timelines, hypothesis testing, and 6-dimensional SRE scorecard evaluation (`Detection | Investigation | Root Cause | Fix | Verification | Prevention`).
- **Comprehensive Curriculum**: 12 in-depth guides following the 13-part pedagogical architecture across Linux, Networking, Docker, Kubernetes, Helm/Kustomize, Terraform, Ansible, Git/CI, Argo CD, Observability, Service Mesh, and AWS EKS.
- **Modern Web Console**: High-performance React 18 + Vite SPA featuring xterm.js terminal, Monaco configuration editor, SVG topology visualizer, live telemetry charts, and dark SRE console styling.

---

## 🚀 Quick Start

### 1. Start Backend API Server
```bash
python -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload
```
Open API docs at: `http://localhost:8000/docs`

### 2. Start Frontend Web Console
```bash
cd apps/web
npm install
npm run dev
```
Open Web Console at: `http://localhost:5173`

---

## 📚 Complete Documentation Suite

All 25 mandated technical documentation files are located in `docs/`:

1. [REQUIREMENTS.md](file:///h:/kubelabs/docs/REQUIREMENTS.md) - System functional and security specifications
2. [ARCHITECTURE.md](file:///h:/kubelabs/docs/ARCHITECTURE.md) - Component design and execution flow
3. [TECHNICAL_DESIGN.md](file:///h:/kubelabs/docs/TECHNICAL_DESIGN.md) - Deep-dive technical specifications
4. [CURRICULUM.md](file:///h:/kubelabs/docs/CURRICULUM.md) - 12-track curriculum overview & prerequisite graph
5. [LAB_ENGINE.md](file:///h:/kubelabs/docs/LAB_ENGINE.md) - Declarative lab execution and lifecycle state machine
6. [LAB_AUTHORING_GUIDE.md](file:///h:/kubelabs/docs/LAB_AUTHORING_GUIDE.md) - Guide for authoring YAML labs
7. [USER_GUIDE.md](file:///h:/kubelabs/docs/USER_GUIDE.md) - Learner guide to the 9-panel workspace
8. [DEVELOPER_GUIDE.md](file:///h:/kubelabs/docs/DEVELOPER_GUIDE.md) - Local development & contribution workflow
9. [ADMIN_GUIDE.md](file:///h:/kubelabs/docs/ADMIN_GUIDE.md) - Fleet operations, multi-tenancy, and capacity sizing
10. [SETUP.md](file:///h:/kubelabs/docs/SETUP.md) - Installation and runtime setup
11. [CONFIGURATION.md](file:///h:/kubelabs/docs/CONFIGURATION.md) - Environment variables and configuration options
12. [API.md](file:///h:/kubelabs/docs/API.md) - Complete REST & WebSocket API specification
13. [SECURITY.md](file:///h:/kubelabs/docs/SECURITY.md) - Sandbox isolation profiles and security boundaries
14. [THREAT_MODEL.md](file:///h:/kubelabs/docs/THREAT_MODEL.md) - STRIDE threat model & attack vector mitigations
15. [TESTING.md](file:///h:/kubelabs/docs/TESTING.md) - Automated testing strategy & coverage gates
16. [TROUBLESHOOTING.md](file:///h:/kubelabs/docs/TROUBLESHOOTING.md) - Platform runbooks and recovery steps
17. [OBSERVABILITY.md](file:///h:/kubelabs/docs/OBSERVABILITY.md) - Internal telemetry, PromQL metrics, and tracing
18. [DEPLOYMENT.md](file:///h:/kubelabs/docs/DEPLOYMENT.md) - Production Kubernetes deployment manifests
19. [OPERATIONS.md](file:///h:/kubelabs/docs/OPERATIONS.md) - Day-2 maintenance, backups, and emergency runbooks
20. [COST_CONTROL.md](file:///h:/kubelabs/docs/COST_CONTROL.md) - Cloud cost governance and zero-waste policy
21. [CODE_UNDERSTANDING.md](file:///h:/kubelabs/docs/CODE_UNDERSTANDING.md) - Monorepo structure and code navigation
22. [ROADMAP.md](file:///h:/kubelabs/docs/ROADMAP.md) - Product development phases and upcoming features
23. [PROJECT_STATUS.md](file:///h:/kubelabs/docs/PROJECT_STATUS.md) - Capability matrix and release readiness
24. [IMPLEMENTATION.md](file:///h:/kubelabs/docs/IMPLEMENTATION.md) - Technical implementation details
25. [TODO.md](file:///h:/kubelabs/docs/TODO.md) - Append-only task history log
26. [CHANGELOG.md](file:///h:/kubelabs/docs/CHANGELOG.md) - History-preserving release log
27. [GAP_REPORT.md](file:///h:/kubelabs/docs/GAP_REPORT.md) - System verification classification audit

---

## 🧪 Automated Testing
```bash
# Run test suite
pytest tests/ -v

# Run acceptance verification
python scripts/verify_acceptance.py
```
