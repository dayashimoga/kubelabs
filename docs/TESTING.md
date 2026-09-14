# KubeLabs Testing Strategy & Quality Assurance Architecture

## 1. Testing Philosophy
KubeLabs enforces rigorous automated test coverage targeting **>90% meaningful code coverage** across unit, integration, sandbox security, adversarial, and end-to-end acceptance suites.

## 2. Test Suites Overview

### 2.1 Unit Tests (`tests/unit/`)
- Tests individual validator rules in isolation (Command, File, Regex, YAML, JSON, HTTP, TCP, DNS, Container, Kubernetes, Git, Prometheus, OpenTelemetry).
- Validates 100% of declarative YAML labs against the strict `LabSpec` Pydantic model.
- Tests scoring mathematics and layered hint penalty calculations.

### 2.2 Integration Tests (`tests/integration/`)
- Tests REST API endpoints for labs, sessions, execution, advice, validation, and assessments.
- Tests WebSocket terminal session handshake and streaming I/O.
- Verifies database ORM persistence and SQLite WAL concurrency.

### 2.3 Sandbox Security & Quota Tests (`tests/sandbox/`)
- Verifies rootless container execution, dropped capabilities (`cap-drop=ALL`), and `no-new-privileges`.
- Verifies cgroup memory and PID limits.
- Verifies background TTL sweeper automatically terminates expired sandboxes.

### 2.4 Adversarial & Stress Tests (`tests/adversarial/`)
- Malformed YAML lab specifications.
- Fork bombs and infinite CPU loops.
- Command injection and directory traversal attacks (`../../etc/shadow`).
- Network timeout handling on unreachable endpoints.

### 2.5 End-to-End Acceptance Runner (`scripts/verify_acceptance.py`)
Executes full user journeys from lab start to solution verification and scorecard generation.

## 3. Running Test Suites
```bash
# Run all tests
pytest tests/ -v

# Run with coverage gate (fails if < 90%)
pytest tests/ --cov=packages --cov=apps.api.src --cov-fail-under=90

# Run only sandbox security tests
pytest tests/sandbox/ -v
```
