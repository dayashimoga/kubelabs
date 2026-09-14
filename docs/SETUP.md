# KubeLabs Setup & Installation Guide

## 1. Quick Start (Development Mode)

### Step 1: Clone Repository
```bash
git clone https://github.com/dayan/kubelabs.git
cd kubelabs
```

### Step 2: Set Up Python Backend
Ensure Python 3.11+ is installed.
```bash
python -m pip install -r requirements.txt
```

### Step 3: Set Up Node.js Frontend
Ensure Node.js 20+ and npm are available.
```bash
cd apps/web
npm install
npm run build
cd ../..
```

### Step 4: Run Development Servers
Terminal 1 (Backend):
```bash
python -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd apps/web
npm run dev
```
Open `http://localhost:5173` in your browser.

## 2. Podman Container Host Setup (Optional but Recommended)
To run container sandboxes in real Linux kernel namespaces:
- **Linux**: Install `podman` via system package manager (`apt install podman` or `dnf install podman`).
- **Windows / macOS**: Install Podman Desktop or Podman CLI with default machine (`podman machine init`, `podman machine start`).
- **Verification**: Run `podman run --rm alpine echo 'Podman is operational'`.
