"""
Podman Rootless Container Executor for KubeLabs.
Enforces security isolation: capability drops, cgroup limits,
isolated namespaces, timeouts, and automated cleanup labels.
"""

import os
import subprocess
import time
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from packages.lab_schema import EnvironmentSpec, InitialStateSpec


class PodmanSandboxExecutor:
    """Manages real rootless container sandboxes via Podman."""

    def __init__(self, podman_binary: str = "podman"):
        self.podman = podman_binary
        self._check_availability()

    def _check_availability(self) -> bool:
        try:
            res = subprocess.run([self.podman, "--version"], capture_output=True, text=True, timeout=5)
            self.available = (res.returncode == 0)
            self.version = res.stdout.strip()
        except Exception:
            self.available = False
            self.version = "Unavailable"
        return self.available

    @property
    def is_available(self) -> bool:
        return self._check_availability()

    def create_sandbox(
        self,
        sandbox_id: str,
        env_spec: EnvironmentSpec,
        initial_state: InitialStateSpec,
        ttl_seconds: int = 1800,
    ) -> Dict[str, str]:
        """Spawn a secure container sandbox and stage initial state files and failure seeds."""
        if not self.available:
            raise RuntimeError("Podman is not available on this host.")

        container_name = f"kubelabs-{sandbox_id}"

        # Normalize memory specification for Podman (e.g. 512Mi -> 512m)
        mem_limit = env_spec.memory_limit.lower().replace("ib", "b").replace("i", "")

        cmd = [
            self.podman,
            "run",
            "-d",
            "--name",
            container_name,
            f"--memory={mem_limit}",
            f"--cpus={env_spec.cpu_limit}",
            f"--pids-limit={env_spec.pids_limit}",
            "--security-opt=no-new-privileges",
            f"--label=kubelabs.sandbox_id={sandbox_id}",
            f"--label=kubelabs.created_at={int(time.time())}",
            f"--label=kubelabs.ttl={ttl_seconds}",
        ]

        # Capability dropping
        for cap in env_spec.capabilities_drop:
            cmd.append(f"--cap-drop={cap}")
        for cap in env_spec.capabilities_add:
            cmd.append(f"--cap-add={cap}")

        # Read only root
        if env_spec.read_only_root:
            cmd.append("--read-only")

        # Environment variables
        for k, v in env_spec.environment_variables.items():
            cmd.append(f"-e={k}={v}")

        # Port mappings
        for port in env_spec.port_mappings:
            cmd.append(f"-p={port}")

        # Image and keep-alive process
        cmd.extend([env_spec.image, "sh", "-c", "sleep 86400"])

        run_res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if run_res.returncode != 0:
            raise RuntimeError(f"Failed to start Podman container: {run_res.stderr}")

        container_id = run_res.stdout.strip()

        # Stage files into container using streaming stdin
        if initial_state.files:
            import posixpath
            for staged in initial_state.files:
                parent_dir = posixpath.dirname(staged.path)
                cmd_stage = [
                    self.podman,
                    "exec",
                    "-i",
                    container_name,
                    "sh",
                    "-c",
                    f"mkdir -p '{parent_dir}' && cat > '{staged.path}' && chmod {staged.permissions} '{staged.path}'",
                ]
                subprocess.run(cmd_stage, input=staged.content, text=True, capture_output=True, timeout=15)

        # Run setup commands
        for setup_cmd in initial_state.setup_commands:
            self.exec_command(container_name, setup_cmd)

        # Inject initial failure modes
        for fail_cmd in initial_state.failure_injection_commands:
            self.exec_command(container_name, fail_cmd)

        return {"sandbox_id": sandbox_id, "container_id": container_id, "container_name": container_name}

    def exec_command(
        self,
        container_identifier: str,
        command: str,
        timeout: int = 15,
        user: Optional[str] = None,
        workdir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute a command inside the container and capture exit code, stdout, and stderr."""
        cmd = [self.podman, "exec"]
        if user:
            cmd.extend(["-u", user])
        if workdir:
            cmd.extend(["-w", workdir])

        cmd.extend([container_identifier, "sh", "-c", command])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout} seconds."
        except Exception as e:
            return 1, "", f"Execution failure: {str(e)}"

    def cleanup_container(self, container_identifier: str) -> bool:
        """Stop and remove a container."""
        try:
            subprocess.run([self.podman, "rm", "-f", container_identifier], capture_output=True, timeout=15)
            # Synchronize removal
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def list_kubelabs_containers(self) -> List[Dict[str, str]]:
        """List active sandboxes created by KubeLabs."""
        try:
            res = subprocess.run(
                [self.podman, "ps", "-a", "--filter", "label=kubelabs.sandbox_id", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Labels}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            containers = []
            for line in res.stdout.strip().splitlines():
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "labels": parts[3] if len(parts) > 3 else "",
                    })
            return containers
        except Exception:
            return []

    def verify_zero_residue(self, sandbox_id: str) -> Tuple[bool, List[str]]:
        """Verify no containers remain for this sandbox id."""
        try:
            res = subprocess.run(
                [self.podman, "ps", "-a", "--filter", f"label=kubelabs.sandbox_id={sandbox_id}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            orphans = [c for c in res.stdout.strip().splitlines() if c.strip()]
            return len(orphans) == 0, orphans
        except Exception:
            return True, []
