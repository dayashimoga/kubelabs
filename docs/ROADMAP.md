# KubeLabs Product & Engineering Roadmap

## 1. Phase 1: Core Foundation & Monorepo (Completed)
- [x] Establish modular monorepo layout (`apps/`, `packages/`, `labs/`, `content/`, `docs/`, `tests/`).
- [x] Implement declarative YAML lab schema with Pydantic v2 validation.
- [x] Build 14 state-based verification engines in `packages/validator_core`.
- [x] Build rootless Podman executor and deterministic SRE simulator in `packages/sandbox_runtime`.
- [x] Build FastAPI modular monolith with WebSocket terminal streaming.
- [x] Build React 18 + Vite + TypeScript frontend with xterm.js, Monaco editor, and dark-mode aesthetic.

## 2. Phase 2: Curriculum Depth & Scenarios (Completed)
- [x] Author comprehensive 13-part curriculum tracks across all 12 core disciplines.
- [x] Implement catalog of 13 declarative YAML hands-on labs with real failure modes.
- [x] Implement catalog of 12 production SEV-1/SEV-2 incident simulator scenarios.
- [x] Implement 8 assessment question formats (MCQ, multi-select, ordering, prediction, log analysis, YAML fixing, architecture, troubleshooting).
- [x] Implement Grand Capstone: End-to-End GitOps to Incident Recovery Pipeline.

## 3. Phase 3: Scale & Multi-Node Cluster Orchestration (Next)
- [ ] Ephemeral Kind/k3d multi-node cluster provisioning daemon.
- [ ] OIDC SSO integration with GitHub Enterprise, Google Workspace, and Okta.
- [ ] Distributed Redis cluster support for WebSocket session scale-out across multiple API nodes.
- [ ] Automated eBPF network trace capture and packet inspection inside web console.
- [ ] Integration with real AWS Sandbox accounts with short-lived STS credentials and automated Lambda Janitor sweepers.
