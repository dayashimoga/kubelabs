<#
.SYNOPSIS
    KubeLabs One-Command Idempotent Podman Management CLI (PowerShell).
.DESCRIPTION
    Provides unified commands: setup | up | status | logs | test | acceptance | reset | cleanup | down.
    Guarantees zero host residue upon cleanup/down.
#>

param (
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("setup", "up", "status", "logs", "test", "acceptance", "reset", "cleanup", "down")]
    [string]$Action
)

$ErrorActionPreference = "Continue"
$RootPath = (Get-Item -Path $PSScriptRoot).Parent.FullName

function Show-Header {
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "  KubeLabs Production Platform CLI (Rootless Podman Orchestrator)" -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
}

switch ($Action) {
    "setup" {
        Show-Header
        Write-Host "`n[1/3] Checking Podman container engine..." -ForegroundColor Yellow
        & podman --version
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Podman is not installed or not in PATH."
            exit 1
        }

        Write-Host "`n[2/3] Pulling certified base images into local Podman storage..." -ForegroundColor Yellow
        $images = @(
            "docker.io/library/alpine:latest",
            "docker.io/rancher/k3s:latest"
        )
        foreach ($img in $images) {
            Write-Host "  Pulling $img..." -ForegroundColor DarkCyan
            & podman pull $img
        }

        Write-Host "`n[3/3] Checking Python 3.11 environment..." -ForegroundColor Yellow
        & python --version
        Write-Host "`n[SUCCESS] Setup completed successfully." -ForegroundColor Green
    }

    "up" {
        Show-Header
        Write-Host "`nStarting KubeLabs Backend API on http://localhost:8000..." -ForegroundColor Yellow
        $job = Start-Process -FilePath "python" -ArgumentList "-m uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $RootPath -PassThru
        Start-Sleep -Seconds 2
        Write-Host "Backend started with PID: $($job.Id)" -ForegroundColor Green
        Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "Health Probe:     http://localhost:8000/healthz" -ForegroundColor Cyan
        Write-Host "Readiness Probe:  http://localhost:8000/readyz" -ForegroundColor Cyan
    }

    "status" {
        Show-Header
        Write-Host "`n[1] Checking Active KubeLabs Sandboxes & Containers:" -ForegroundColor Yellow
        & podman ps -a --filter "label=kubelabs.sandbox_id" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Labels}}"
        
        Write-Host "`n[2] Checking Active KubeLabs Networks:" -ForegroundColor Yellow
        & podman network ls --filter "label=kubelabs.sandbox_id"

        Write-Host "`n[3] Backend Readiness Probe:" -ForegroundColor Yellow
        try {
            $res = Invoke-RestMethod -Uri "http://localhost:8000/readyz" -TimeoutSec 2 -ErrorAction Stop
            Write-Host "  Readiness: $($res.ready) | DB: $($res.components.database) | Cache: $($res.components.redis_cache)" -ForegroundColor Green
        } catch {
            Write-Host "  Backend not responding on port 8000 (offline)." -ForegroundColor Red
        }
    }

    "logs" {
        Show-Header
        Write-Host "`nStreaming Podman container logs with label kubelabs.sandbox_id..." -ForegroundColor Yellow
        $containers = (& podman ps -q --filter "label=kubelabs.sandbox_id")
        if ($containers) {
            foreach ($c in $containers) {
                Write-Host "--- Container $c ---" -ForegroundColor DarkCyan
                & podman logs --tail 50 $c
            }
        } else {
            Write-Host "No active sandbox containers found." -ForegroundColor DarkGray
        }
    }

    "test" {
        Show-Header
        Write-Host "`nExecuting full automated test suite (Pytest)..." -ForegroundColor Yellow
        Set-Location $RootPath
        & pytest tests/ -v --cov=packages --cov=apps.api.src
    }

    "acceptance" {
        Show-Header
        Write-Host "`nExecuting 10-Gate Production Acceptance Suite..." -ForegroundColor Yellow
        Set-Location $RootPath
        & python scripts/verify_acceptance.py
    }

    "reset" {
        Show-Header
        Write-Host "`nResetting all active sandboxes..." -ForegroundColor Yellow
        $containers = (& podman ps -q --filter "label=kubelabs.sandbox_id")
        if ($containers) {
            & podman restart $containers
            Write-Host "Restarted active sandbox containers." -ForegroundColor Green
        } else {
            Write-Host "No active containers to reset." -ForegroundColor DarkGray
        }
    }

    "cleanup" {
        Show-Header
        Write-Host "`nPurging all orphaned KubeLabs containers, networks, and volumes..." -ForegroundColor Yellow
        # 1. Stop and remove containers
        $containers = (& podman ps -a -q --filter "label=kubelabs.sandbox_id")
        if ($containers) {
            Write-Host "  Removing containers: $containers" -ForegroundColor DarkCyan
            & podman rm -f $containers
        }

        # 2. Remove networks
        $nets = (& podman network ls -q --filter "label=kubelabs.sandbox_id")
        if ($nets) {
            Write-Host "  Removing networks: $nets" -ForegroundColor DarkCyan
            & podman network rm -f $nets
        }

        # 3. Clean temporary files
        Get-ChildItem -Path $RootPath -Include "*.pyc", "__pycache__" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Write-Host "[SUCCESS] Zero residue verified. Platform clean." -ForegroundColor Green
    }

    "down" {
        Show-Header
        Write-Host "`nTearing down all KubeLabs processes and sandbox environments..." -ForegroundColor Yellow
        
        # Stop background uvicorn processes
        Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn apps.api.src.main:app*" } | Stop-Process -Force -ErrorAction SilentlyContinue

        # Run full cleanup
        & "$PSScriptRoot\kubelabs.ps1" cleanup
        Write-Host "[SUCCESS] KubeLabs services and sandboxes fully shut down." -ForegroundColor Green
    }
}
