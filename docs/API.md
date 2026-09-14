# KubeLabs REST & WebSocket API Reference

All REST endpoints are prefixed with `/api/v1`. Interactive documentation is available at `http://localhost:8000/docs`.

## 1. Labs API (`/api/v1/labs`)

### `GET /api/v1/labs/tracks`
Returns list of unique curriculum track slugs.

### `GET /api/v1/labs?track={track_name}`
Returns list of available lab summaries.

### `GET /api/v1/labs/{lab_id}`
Returns full declarative lab specification including objectives, theory, workflow, topology, and tasks.

### `POST /api/v1/labs/{lab_id}/session`
Provisions an isolated container or simulation sandbox session.
- **Request Body**: `{"force_simulation": false}`
- **Response**: `{"session_id": "8f3b2a", "is_container": true, "expires_at": 1789214400, ...}`

### `POST /api/v1/labs/session/{session_id}/exec`
Executes an ad-hoc command in the sandbox.
- **Request Body**: `{"command": "df -i"}`
- **Response**: `{"exit_code": 0, "stdout": "...", "stderr": ""}`

### `POST /api/v1/labs/session/{session_id}/advisor`
Contextual diagnostic assistant.
- **Request Body**: `{"task_id": "t1", "question": "What should I inspect next?"}`
- **Response**: `{"tier": 2, "category": "Inspection Target", "guidance": "..."}`

### `POST /api/v1/labs/session/{session_id}/validate`
Evaluates task state against declarative validators.
- **Request Body**: `{"task_id": "t1"}`
- **Response**: `ValidationReport` (`overall_status`, `total_score`, `items`)

### `DELETE /api/v1/labs/session/{session_id}`
Terminates and purges sandbox session.

## 2. Incidents API (`/api/v1/incidents`)

### `GET /api/v1/incidents`
Lists all 12 SEV-1/SEV-2 incident scenarios.

### `POST /api/v1/incidents/{incident_id}/start`
Starts a live incident war room session.

### `POST /api/v1/incidents/session/{session_id}/hypothesis`
Submits an SRE hypothesis for evaluation against live telemetry.

### `POST /api/v1/incidents/session/{session_id}/mitigate`
Applies a mitigation command.

### `POST /api/v1/incidents/session/{session_id}/resolve`
Verifies incident resolution and calculates SRE scorecard across 6 dimensions.

## 3. Assessments API (`/api/v1/assessments`)

### `GET /api/v1/assessments/{track}`
Returns questions for specified track (or `all`). Correct answers are redacted.

### `POST /api/v1/assessments/{track}/submit`
Grades submission and returns score, percentages, and detailed pedagogical explanations.

## 4. Telemetry API (`/api/v1/telemetry`)
- `GET /api/v1/telemetry/metrics?perturbed={bool}`: Real-time time series vector.
- `GET /api/v1/telemetry/logs?service={name}`: Streaming structured logs.
- `GET /api/v1/telemetry/traces`: Distributed trace spans.

## 5. WebSocket Terminal (`/ws/terminal/{session_id}`)
Bi-directional PTY streaming connection. Client sends raw keystrokes/data; server responds with formatted ANSI terminal output.
