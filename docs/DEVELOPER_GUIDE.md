# KubeLabs Developer & Contributor Guide

## 1. Local Environment Setup

### 1.1 Prerequisites
- Python 3.11+
- Node.js 20+ & npm
- Podman 5.x or Docker (optional for container sandboxes; in-process simulator acts as deterministic fallback)

### 1.2 Running Backend Locally
```bash
# From repository root
python -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 1.3 Running Frontend Locally
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## 2. Monorepo Structure
```
h:/kubelabs/
├── apps/
│   ├── api/             # FastAPI modular monolith
│   └── web/             # React 18 + Vite + TypeScript
├── packages/
│   ├── lab_schema/      # Pydantic models & YAML loader
│   ├── validator_core/  # 14 state-based validators
│   ├── sandbox_runtime/ # Podman executor & SRE simulator
│   └── incident_core/   # Incident state machine & scenarios
├── labs/                # Declarative lab definitions
├── content/             # Curriculum tracks & assessments
├── tests/               # Unit, integration, security tests
├── scripts/             # Automation & verification scripts
└── docs/                # Architecture & operational documentation
```

## 3. Running Automated Tests
```bash
# Run all unit and integration tests
pytest tests/ -v

# Run with test coverage
pytest tests/ --cov=packages --cov=apps.api.src --cov-report=term-missing
```
