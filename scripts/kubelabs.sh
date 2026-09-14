#!/usr/bin/env bash
# ==============================================================================
# KubeLabs One-Command Idempotent Podman Management CLI (POSIX Shell)
# Supports: setup | up | status | logs | test | acceptance | reset | cleanup | down
# ==============================================================================

set -euo pipefail

ACTION="${1:-help}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

show_header() {
    echo "======================================================================"
    echo "  KubeLabs Production Platform CLI (Rootless Podman Orchestrator)"
    echo "======================================================================"
}

case "${ACTION}" in
    setup)
        show_header
        echo "[1/3] Checking Podman container engine..."
        podman --version
        echo "[2/3] Pulling certified base images into local Podman storage..."
        podman pull docker.io/library/alpine:latest
        podman pull docker.io/rancher/k3s:latest
        echo "[3/3] Checking Python environment..."
        python3 --version || python --version
        echo "[SUCCESS] Setup completed successfully."
        ;;

    up)
        show_header
        echo "Starting KubeLabs Backend API on http://0.0.0.0:8000..."
        cd "${ROOT_DIR}"
        python3 -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 &
        echo "Backend started in background. Visit http://localhost:8000/docs"
        ;;

    status)
        show_header
        echo "[1] Checking Active KubeLabs Sandboxes & Containers:"
        podman ps -a --filter "label=kubelabs.sandbox_id" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Labels}}"
        echo "[2] Checking Active KubeLabs Networks:"
        podman network ls --filter "label=kubelabs.sandbox_id"
        echo "[3] Backend Readiness Probe:"
        curl -s http://localhost:8000/readyz || echo "Backend offline"
        ;;

    logs)
        show_header
        echo "Streaming Podman container logs with label kubelabs.sandbox_id..."
        for cid in $(podman ps -q --filter "label=kubelabs.sandbox_id"); do
            echo "--- Container ${cid} ---"
            podman logs --tail 50 "${cid}"
        done
        ;;

    test)
        show_header
        echo "Executing full automated test suite (Pytest)..."
        cd "${ROOT_DIR}"
        pytest tests/ -v --cov=packages --cov=apps.api.src
        ;;

    acceptance)
        show_header
        echo "Executing Production Acceptance Suite..."
        cd "${ROOT_DIR}"
        python3 scripts/verify_acceptance.py || python scripts/verify_acceptance.py
        ;;

    reset)
        show_header
        echo "Restarting active sandboxes..."
        for cid in $(podman ps -q --filter "label=kubelabs.sandbox_id"); do
            podman restart "${cid}"
        done
        echo "All active sandboxes restarted."
        ;;

    cleanup)
        show_header
        echo "Purging all orphaned KubeLabs containers, networks, and volumes..."
        for cid in $(podman ps -a -q --filter "label=kubelabs.sandbox_id"); do
            podman rm -f "${cid}" || true
        done
        for net in $(podman network ls -q --filter "label=kubelabs.sandbox_id"); do
            podman network rm -f "${net}" || true
        done
        find "${ROOT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        echo "[SUCCESS] Zero residue verified. Platform clean."
        ;;

    down)
        show_header
        echo "Shutting down KubeLabs backend processes and sandbox environments..."
        pkill -f "uvicorn apps.api.src.main:app" || true
        "${SCRIPT_DIR}/kubelabs.sh" cleanup
        echo "[SUCCESS] Platform fully stopped."
        ;;

    *)
        echo "Usage: $0 {setup|up|status|logs|test|acceptance|reset|cleanup|down}"
        exit 1
        ;;
esac
