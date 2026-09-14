# KubeLabs Codebase Navigation & Architecture Map

## 1. Monorepo Organization
This document provides a guided tour for engineers onboarding to the KubeLabs codebase.

### 1.1 `apps/api/` (Backend Application)
- `src/main.py`: Application entrypoint, FastAPI instance, middleware, and router mounts.
- `src/core/config.py`: Settings class loading environment variables and monorepo path boots.
- `src/core/database.py`: SQLAlchemy database engine with SQLite WAL pragmas.
- `src/models/db_models.py`: ORM schemas for users, lab attempts, and incident attempts.
- `src/services/lab_service.py`: High-level service coordinating lab registry, sandbox sessions, and validator engine.
- `src/services/troubleshooting_service.py`: Contextual diagnostic assistant providing tiered guidance and answering canonical SRE questions.
- `src/services/assessment_service.py`: Quiz grader across 8 question formats.
- `src/api/`: Versioned REST and WebSocket route handlers (`labs.py`, `incidents.py`, `assessments.py`, `dashboard.py`, `telemetry.py`, `terminal.py`).

### 1.2 `apps/web/` (Frontend Application)
- `src/App.tsx`: Main navigation frame, sidebar, and view router.
- `src/styles/index.css`: Cyberpunk dark-mode CSS design system and glassmorphism tokens.
- `src/components/Terminal/TerminalView.tsx`: xterm.js terminal integration with fit addon.
- `src/components/Editor/CodeEditor.tsx`: Monaco editor integration with language highlighting and save callbacks.
- `src/components/Topology/TopologyViewer.tsx`: Interactive SVG service graph with animated traffic edges.
- `src/components/Telemetry/TelemetryViewer.tsx`: Real-time metric cards, log streams, and OTel trace waterfalls.
- `src/components/Hints/LayeredHintsDialog.tsx`: 5-tier hint disclosure and SRE question assistant.
- `src/components/Validation/ValidationPanel.tsx`: State-based validation results and feedback cards.
- `src/pages/`: Route views (`Dashboard.tsx`, `TrackView.tsx`, `LabWorkspace.tsx`, `IncidentSimulator.tsx`, `Assessments.tsx`).

### 1.3 `packages/` (Core Engines)
- `packages/lab_schema/`: Pydantic models for declarative YAML specs (`LabSpec`, `TaskSpec`, `ValidatorRule`).
- `packages/validator_core/`: 14 state-based verification engines (`Command`, `File`, `Yaml`, `Json`, `Http`, `Tcp`, `Dns`, `Container`, `Kubernetes`, `Git`, `Prometheus`, `OpenTelemetry`).
- `packages/sandbox_runtime/`: Rootless Podman container manager and deterministic SRE state machine simulator.
- `packages/incident_core/`: Catalog of 12 SEV-1/SEV-2 cascading outages and SRE scoring engine.
