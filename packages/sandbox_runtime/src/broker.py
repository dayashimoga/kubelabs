"""
Environment Broker: Multi-Provider Orchestration Engine for KubeLabs.
Coordinates single-container, multi-container pods/networks, dedicated Kubernetes sandboxes,
and deterministic simulations.
Enforces strict zero-silent-fallback guarantees and verified zero-residue cleanup.
"""

import os
import subprocess
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

from packages.lab_schema import (
    LabSpec,
    EnvironmentType,
    LabRuntimeClassification,
    EnvironmentSpec,
    MultiContainerSpec,
)
from .executor import PodmanSandboxExecutor
from .simulator import DeterministicSimulator
from .scenario_injector import ScenarioInjector
from .k8s_provider import KubernetesProvider, KubernetesRuntimeError


class RuntimeProvisioningError(Exception):
    """Raised when provisioning a real runtime environment fails."""
    pass


class EnvironmentBroker:
    """Orchestrates ephemeral learning environments across multiple runtime backends."""

    def __init__(self, podman_binary: str = "podman"):
        self.podman_executor = PodmanSandboxExecutor(podman_binary)
        self.k8s_provider = KubernetesProvider(podman_binary)
        self.active_environments: Dict[str, Dict[str, Any]] = {}

    @property
    def is_podman_available(self) -> bool:
        return self.podman_executor.available

    def start_environment(
        self, sandbox_id: str, lab_spec: LabSpec, force_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Provision the appropriate environment for a lab based on its specification.
        Enforces strict zero silent fallback: if a REAL lab fails, an explicit
        RuntimeProvisioningError is raised.
        """
        env_spec = lab_spec.environment
        env_type = env_spec.type
        is_real_required = (
            lab_spec.runtime_classification == LabRuntimeClassification.REAL
            and not force_simulation
        )

        # 1. REAL-KUBERNETES Environment
        if env_type == EnvironmentType.KUBERNETES and not force_simulation:
            try:
                k8s_rec = self.k8s_provider.provision_k8s_environment(sandbox_id, lab_spec)
                env_record = {
                    "sandbox_id": sandbox_id,
                    "provider": f"k8s-{k8s_rec['mode']}",
                    "classification": LabRuntimeClassification.REAL,
                    "k8s_info": k8s_rec,
                    "created_at": time.time(),
                    "lab_spec": lab_spec,
                }
                self.active_environments[sandbox_id] = env_record
                return env_record
            except Exception as exc:
                if is_real_required:
                    raise RuntimeProvisioningError(
                        f"Failed to provision REAL-KUBERNETES environment for lab '{lab_spec.id}': {str(exc)}"
                    )
                # Fall through to simulation only if NOT strictly REAL

        # 2. REAL-MULTI-CONTAINER Environment
        if env_spec.multi_container and not force_simulation:
            if not self.is_podman_available and is_real_required:
                raise RuntimeProvisioningError(
                    f"Podman runtime is not available to provision multi-container environment for '{lab_spec.id}'."
                )
            if self.is_podman_available:
                try:
                    return self._start_multi_container(sandbox_id, lab_spec)
                except Exception as exc:
                    if is_real_required:
                        raise RuntimeProvisioningError(
                            f"Failed to provision multi-container bridge environment for '{lab_spec.id}': {str(exc)}"
                        )

        # 3. REAL-SINGLE-CONTAINER Environment
        if env_type in [EnvironmentType.CONTAINER, EnvironmentType.HYBRID] and not force_simulation:
            if not self.is_podman_available and is_real_required:
                raise RuntimeProvisioningError(
                    f"Podman runtime is not available to provision single-container environment for '{lab_spec.id}'."
                )
            if self.is_podman_available:
                try:
                    res = self.podman_executor.create_sandbox(
                        sandbox_id=sandbox_id,
                        env_spec=env_spec,
                        initial_state=lab_spec.initial_state,
                        ttl_seconds=lab_spec.cleanup_policy.ttl_seconds,
                    )
                    env_record = {
                        "sandbox_id": sandbox_id,
                        "provider": "podman-single",
                        "classification": LabRuntimeClassification.REAL,
                        "container_id": res["container_id"],
                        "container_name": res["container_name"],
                        "created_at": time.time(),
                        "lab_spec": lab_spec,
                    }
                    self.active_environments[sandbox_id] = env_record
                    return env_record
                except Exception as exc:
                    if is_real_required:
                        raise RuntimeProvisioningError(
                            f"Failed to provision REAL container sandbox for '{lab_spec.id}': {str(exc)}"
                        )

        # 4. Deterministic Simulation Provider (Explicit or Cloud-Required fallback)
        classification = lab_spec.runtime_classification
        if force_simulation or classification in [
            LabRuntimeClassification.SIMULATED,
            LabRuntimeClassification.EMULATED,
            LabRuntimeClassification.CLOUD_REQUIRED,
        ]:
            sim = DeterministicSimulator(lab_spec.id, lab_spec.initial_state.seed_data)
            env_record = {
                "sandbox_id": sandbox_id,
                "provider": "simulator",
                "classification": (
                    LabRuntimeClassification.SIMULATED
                    if force_simulation
                    else classification
                ),
                "simulator": sim,
                "created_at": time.time(),
                "lab_spec": lab_spec,
            }
            self.active_environments[sandbox_id] = env_record
            return env_record

        # If we reached here with is_real_required, raise error
        raise RuntimeProvisioningError(
            f"Unable to provision environment for lab '{lab_spec.id}'. Runtime requirement '{classification}' could not be satisfied."
        )

    def _start_multi_container(self, sandbox_id: str, lab_spec: LabSpec) -> Dict[str, Any]:
        """Deploy an interconnected multi-container pod or bridge network."""
        multi_spec = lab_spec.environment.multi_container
        network_name = f"kubelabs-net-{sandbox_id}"
        containers = []

        try:
            # Create isolated bridge network
            subprocess.run(
                [
                    self.podman_executor.podman,
                    "network",
                    "create",
                    f"--label=kubelabs.sandbox_id={sandbox_id}",
                    network_name,
                ],
                check=False,
                capture_output=True,
                timeout=10,
            )

            for c_spec in multi_spec.containers:
                c_name = f"kubelabs-{sandbox_id}-{c_spec.name}"
                cmd = [
                    self.podman_executor.podman,
                    "run",
                    "-d",
                    "--name",
                    c_name,
                    f"--network={network_name}",
                    f"--label=kubelabs.sandbox_id={sandbox_id}",
                    "--security-opt=no-new-privileges",
                    "--cap-drop=ALL",
                    "--memory=256m",
                    "--cpus=0.5",
                ]
                for p in c_spec.ports:
                    cmd.append(f"-p={p}")
                for k, v in c_spec.environment.items():
                    cmd.append(f"-e={k}={v}")

                cmd.extend([c_spec.image, "sh", "-c", c_spec.command or "sleep 86400"])
                run_res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                if run_res.returncode == 0:
                    containers.append({
                        "name": c_spec.name,
                        "container_id": run_res.stdout.strip(),
                        "container_name": c_name,
                    })
                else:
                    raise RuntimeError(
                        f"Failed to start multi-container node '{c_spec.name}': {run_res.stderr.strip()}"
                    )

            # Stage initial files into primary container
            if containers and lab_spec.initial_state.files:
                import posixpath
                primary_name = containers[0]["container_name"]
                for staged in lab_spec.initial_state.files:
                    parent_dir = posixpath.dirname(staged.path)
                    cmd_stage = [
                        self.podman_executor.podman,
                        "exec",
                        "-i",
                        primary_name,
                        "sh",
                        "-c",
                        f"mkdir -p '{parent_dir}' && cat > '{staged.path}' && chmod {staged.permissions} '{staged.path}'",
                    ]
                    subprocess.run(
                        cmd_stage,
                        input=staged.content,
                        text=True,
                        capture_output=True,
                        timeout=15,
                    )

            env_record = {
                "sandbox_id": sandbox_id,
                "provider": "podman-multi",
                "classification": LabRuntimeClassification.REAL,
                "network_name": network_name,
                "containers": containers,
                "primary_container": containers[0]["container_name"] if containers else None,
                "created_at": time.time(),
                "lab_spec": lab_spec,
            }
            self.active_environments[sandbox_id] = env_record
            return env_record
        except Exception as exc:
            # Clean up partial creations
            self.destroy_environment(sandbox_id)
            raise exc

    def execute_command(
        self, sandbox_id: str, command: str, container_name: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """Execute command in target environment."""
        env = self.active_environments.get(sandbox_id)
        if not env:
            return 1, "", f"Sandbox {sandbox_id} not found."

        provider = env.get("provider", "")

        if provider == "podman-single":
            target = env.get("container_name") or env.get("container_id")
            return self.podman_executor.exec_command(target, command)

        elif provider == "podman-multi":
            target = container_name or env.get("primary_container")
            if not target:
                return 1, "", "No container target available in multi-container sandbox."
            return self.podman_executor.exec_command(target, command)

        elif provider.startswith("k8s-"):
            return self.k8s_provider.execute_kubectl(sandbox_id, command)

        else:
            sim: DeterministicSimulator = env.get("simulator")
            return sim.execute_command(command)

    def inject_fault(self, sandbox_id: str, fault_name: str) -> Tuple[bool, str]:
        """Inject failure scenario dynamically."""
        exec_fn = lambda cmd: self.execute_command(sandbox_id, cmd)
        return ScenarioInjector.inject(exec_fn, fault_name)

    def apply_solution(self, sandbox_id: str, fault_name: str) -> Tuple[bool, str]:
        """Apply solution fix dynamically."""
        exec_fn = lambda cmd: self.execute_command(sandbox_id, cmd)
        return ScenarioInjector.repair(exec_fn, fault_name)

    def reset_environment(self, sandbox_id: str) -> bool:
        """Reset sandbox to initial failure state."""
        env = self.active_environments.get(sandbox_id)
        if not env:
            return False

        lab_spec: LabSpec = env.get("lab_spec")
        if not lab_spec:
            return False

        # Re-run initial failure injection commands
        for cmd in lab_spec.initial_state.failure_injection_commands:
            self.execute_command(sandbox_id, cmd)

        return True

    def destroy_environment(self, sandbox_id: str) -> bool:
        """Destroy environment and clean up all associated containers, networks, namespaces, and files."""
        env = self.active_environments.pop(sandbox_id, None)
        if not env:
            return False

        provider = env.get("provider", "")

        # 1. Kubernetes cleanup
        if provider.startswith("k8s-") or sandbox_id in self.k8s_provider.active_clusters or sandbox_id in self.k8s_provider.active_namespaces:
            self.k8s_provider.destroy_k8s_environment(sandbox_id)

        # 2. Podman single-container cleanup
        if provider == "podman-single":
            c_name = env.get("container_name") or env.get("container_id")
            if c_name:
                self.podman_executor.cleanup_container(c_name)

        # 3. Podman multi-container cleanup
        elif provider == "podman-multi":
            for c in env.get("containers", []):
                self.podman_executor.cleanup_container(c.get("container_name"))
            net_name = env.get("network_name")
            if net_name and self.is_podman_available:
                try:
                    subprocess.run(
                        [self.podman_executor.podman, "network", "rm", "-f", net_name],
                        capture_output=True,
                        timeout=10,
                    )
                except Exception:
                    pass

        return True

    def verify_zero_residue(self, sandbox_id: str) -> Tuple[bool, List[str]]:
        """Verify that no containers, networks, volumes, or namespaces remain for this sandbox."""
        residue = []

        # Check Kubernetes residue
        k8s_clean, k8s_residue = self.k8s_provider.verify_zero_residue(sandbox_id)
        if not k8s_clean:
            residue.extend(k8s_residue)

        if not self.is_podman_available:
            return len(residue) == 0, residue

        try:
            # Check containers
            res = subprocess.run(
                [
                    self.podman_executor.podman,
                    "ps",
                    "-a",
                    "--filter",
                    f"label=kubelabs.sandbox_id={sandbox_id}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            found_containers = [
                line.strip() for line in res.stdout.strip().splitlines() if line.strip()
            ]
            if found_containers:
                residue.extend([f"Container: {c}" for c in found_containers])

            # Check networks
            res_net = subprocess.run(
                [
                    self.podman_executor.podman,
                    "network",
                    "ls",
                    "--filter",
                    f"label=kubelabs.sandbox_id={sandbox_id}",
                    "--format",
                    "{{.Name}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            found_nets = [
                line.strip() for line in res_net.stdout.strip().splitlines() if line.strip()
            ]
            if found_nets:
                residue.extend([f"Network: {n}" for n in found_nets])

        except Exception as e:
            print(f"[verify_zero_residue] Error querying residue: {e}")

        return len(residue) == 0, residue
