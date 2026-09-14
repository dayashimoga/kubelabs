# KubeLabs Platform Troubleshooting & Diagnostic Runbook

## 1. Diagnostic Triage Workflow
If KubeLabs backend or frontend encounters unexpected behavior, follow this systematic runbook.

## 2. Common Platform Failure Modes & Remediation

### 2.1 Backend Port 8000 Already in Use
- **Symptom**: `ERROR: [Errno 48] Address already in use` or `[WinError 10048]`.
- **Diagnosis**: Another instance of uvicorn is running.
- **Remediation**:
  ```powershell
  Get-Process -Name python | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process
  ```

### 2.2 Podman Machine Not Responding
- **Symptom**: `RuntimeError: Failed to start Podman container: dial unix /var/run/podman.sock: connect: connection refused`.
- **Diagnosis**: WSL2 or Podman VM is stopped.
- **Remediation**:
  ```bash
  podman machine start
  podman run --rm alpine echo 'ok'
  ```
  If Podman is completely unavailable, the platform automatically fails over to the in-process `DeterministicSimulator`.

### 2.3 WebSocket Terminal Disconnects Immediately
- **Symptom**: xterm.js displays `[Terminal disconnected]` right after opening.
- **Diagnosis**: Session ID expired or proxy failed to upgrade HTTP to WebSocket.
- **Remediation**:
  - Verify session is active via `GET /api/v1/labs/session/{id}`.
  - Verify Vite reverse proxy has `ws: true` configured in `apps/web/vite.config.ts`.

### 2.4 Database Locked (SQLite)
- **Symptom**: `OperationalError: database is locked`.
- **Diagnosis**: Multiple concurrent threads attempting write operations without WAL mode.
- **Remediation**:
  - Ensure SQLite PRAGMA journal_mode is WAL (`PRAGMA journal_mode=WAL`).
  - Switch to PostgreSQL for multi-worker production deployments.
