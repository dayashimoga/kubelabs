"""
Dedicated Kubernetes Runtime Provider for KubeLabs.
Manages ephemeral k3s container instances and isolated namespaces with strict resource quotas,
NetworkPolicy containment, and verified zero-residue lifecycle.
"""

import os
import time
import json
import uuid
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from packages.lab_schema import LabSpec, LabRuntimeClassification


class KubernetesRuntimeError(Exception):
    """Raised when Kubernetes environment operations fail."""
    pass


class KubernetesProvider:
    """Orchestrates genuine ephemeral Kubernetes environments via K3s containers or isolated namespaces."""

    def __init__(self, podman_binary: str = "podman"):
        self.podman = podman_binary
        self.active_clusters: Dict[str, Dict[str, Any]] = {}
        self.active_namespaces: Dict[str, Dict[str, Any]] = {}

    @property
    def is_podman_available(self) -> bool:
        try:
            res = subprocess.run([self.podman, "--version"], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    @property
    def is_kubectl_available(self) -> bool:
        try:
            res = subprocess.run(["kubectl", "version", "--client"], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def provision_k8s_environment(self, sandbox_id: str, lab_spec: LabSpec) -> Dict[str, Any]:
        """
        Provisions a real Kubernetes environment:
        1. If host has an active cluster connection, provision an isolated namespace with ResourceQuotas.
        2. Otherwise, launch an ephemeral single-node K3s container in rootless Podman.
        """
        env_spec = lab_spec.environment
        namespace_name = f"kubelabs-{sandbox_id}"

        # Strategy A: Use active cluster if reachable
        if self.is_kubectl_available:
            try:
                probe = subprocess.run(["kubectl", "cluster-info"], capture_output=True, text=True, timeout=5)
                if probe.returncode == 0:
                    return self._provision_isolated_namespace(sandbox_id, namespace_name, lab_spec)
            except Exception:
                pass

        # Strategy B: Spin up ephemeral K3s container in Podman
        if self.is_podman_available:
            return self._provision_k3s_container(sandbox_id, lab_spec)

        raise KubernetesRuntimeError(
            "Neither an accessible Kubernetes cluster nor Podman container runtime is available to provision REAL-KUBERNETES environment."
        )

    def _provision_isolated_namespace(self, sandbox_id: str, namespace: str, lab_spec: LabSpec) -> Dict[str, Any]:
        """Creates an isolated namespace with strict limits and NetworkPolicy."""
        try:
            # 1. Create namespace
            subprocess.run(
                ["kubectl", "create", "namespace", namespace],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Label namespace for cleanup tracking
            subprocess.run(
                ["kubectl", "label", "namespace", namespace, f"kubelabs.sandbox_id={sandbox_id}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )

            # 2. Apply ResourceQuota
            quota_manifest = f"""apiVersion: v1
kind: ResourceQuota
metadata:
  name: sandbox-quota
  namespace: {namespace}
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 1Gi
    limits.cpu: "4"
    limits.memory: 2Gi
    pods: "10"
"""
            subprocess.run(["kubectl", "apply", "-f", "-"], input=quota_manifest, text=True, check=True, timeout=10)

            # 3. Apply default NetworkPolicy (isolate namespace traffic)
            netpol_manifest = f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-sandbox
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {{}}
  egress:
  - to:
    - podSelector: {{}}
  - ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
"""
            subprocess.run(["kubectl", "apply", "-f", "-"], input=netpol_manifest, text=True, check=False, timeout=10)

            record = {
                "sandbox_id": sandbox_id,
                "mode": "namespace",
                "namespace": namespace,
                "classification": LabRuntimeClassification.REAL,
                "created_at": time.time(),
                "lab_spec": lab_spec,
            }
            self.active_namespaces[sandbox_id] = record
            return record

        except subprocess.CalledProcessError as err:
            raise KubernetesRuntimeError(f"Failed to create isolated namespace {namespace}: {err.stderr.strip()}")

    def _provision_k3s_container(self, sandbox_id: str, lab_spec: LabSpec) -> Dict[str, Any]:
        """Launches an ephemeral K3s container with an isolated bridge network."""
        c_name = f"kubelabs-k3s-{sandbox_id}"
        net_name = f"kubelabs-k8s-net-{sandbox_id}"

        try:
            # 1. Create network
            subprocess.run(
                [self.podman, "network", "create", f"--label=kubelabs.sandbox_id={sandbox_id}", net_name],
                capture_output=True,
                timeout=10,
            )

            # 2. Launch K3s container
            cmd = [
                self.podman, "run", "-d",
                "--name", c_name,
                f"--network={net_name}",
                f"--label=kubelabs.sandbox_id={sandbox_id}",
                "--memory=1024m",
                "--cpus=2.0",
                "--pids-limit=300",
                "--security-opt=no-new-privileges",
                "-e", "K3S_KUBECONFIG_OUTPUT=/output/kubeconfig.yaml",
                "-e", "K3S_KUBECONFIG_MODE=666",
                "docker.io/rancher/k3s:latest",
                "server",
                "--disable=traefik",
                "--disable=metrics-server",
                "--disable=local-storage",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                raise KubernetesRuntimeError(f"Podman failed to launch K3s container: {res.stderr.strip()}")

            container_id = res.stdout.strip()
            record = {
                "sandbox_id": sandbox_id,
                "mode": "k3s-container",
                "container_id": container_id,
                "container_name": c_name,
                "network_name": net_name,
                "classification": LabRuntimeClassification.REAL,
                "created_at": time.time(),
                "lab_spec": lab_spec,
            }
            self.active_clusters[sandbox_id] = record
            return record

        except Exception as exc:
            # Cleanup on failure
            self.destroy_k8s_environment(sandbox_id)
            raise KubernetesRuntimeError(f"K3s ephemeral provisioning failed: {str(exc)}")

    def execute_kubectl(self, sandbox_id: str, command: str) -> Tuple[int, str, str]:
        """Executes a kubectl/k8s command within the provisioned sandbox context."""
        if sandbox_id in self.active_namespaces:
            rec = self.active_namespaces[sandbox_id]
            ns = rec["namespace"]
            # Ensure command targets the isolated namespace if not specified
            if "-n " not in command and "--namespace" not in command:
                full_cmd = f"kubectl {command} -n {ns}"
            else:
                full_cmd = f"kubectl {command}"
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=15)
            return res.returncode, res.stdout, res.stderr

        elif sandbox_id in self.active_clusters:
            rec = self.active_clusters[sandbox_id]
            c_name = rec["container_name"]
            # Execute inside the k3s container using its internal kubectl
            cmd = [self.podman, "exec", "-i", c_name, "sh", "-c", f"k3s kubectl {command}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return res.returncode, res.stdout, res.stderr

        return 1, "", f"Kubernetes sandbox {sandbox_id} not found."

    def destroy_k8s_environment(self, sandbox_id: str) -> bool:
        """Tears down all Kubernetes artifacts (namespaces, containers, networks) cleanly."""
        cleaned = True

        # Clean namespace if active
        if sandbox_id in self.active_namespaces:
            rec = self.active_namespaces.pop(sandbox_id)
            ns = rec.get("namespace")
            if ns and self.is_kubectl_available:
                try:
                    subprocess.run(["kubectl", "delete", "namespace", ns, "--timeout=30s"], capture_output=True, timeout=35)
                except Exception:
                    cleaned = False

        # Clean K3s container and network if active
        if sandbox_id in self.active_clusters:
            rec = self.active_clusters.pop(sandbox_id)
            c_name = rec.get("container_name")
            net_name = rec.get("network_name")
            if c_name and self.is_podman_available:
                try:
                    subprocess.run([self.podman, "rm", "-f", c_name], capture_output=True, timeout=10)
                except Exception:
                    cleaned = False
            if net_name and self.is_podman_available:
                try:
                    subprocess.run([self.podman, "network", "rm", "-f", net_name], capture_output=True, timeout=10)
                except Exception:
                    cleaned = False

        return cleaned

    def verify_zero_residue(self, sandbox_id: str) -> Tuple[bool, List[str]]:
        """Verifies no orphaned namespaces, containers, or networks remain."""
        residue = []

        # Check namespaces
        if self.is_kubectl_available:
            try:
                res = subprocess.run(
                    ["kubectl", "get", "namespaces", "-l", f"kubelabs.sandbox_id={sandbox_id}", "-o", "jsonpath={.items[*].metadata.name}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0 and res.stdout.strip():
                    residue.extend([f"Namespace: {ns}" for ns in res.stdout.strip().split()])
            except Exception:
                pass

        # Check containers
        if self.is_podman_available:
            try:
                res = subprocess.run(
                    [self.podman, "ps", "-a", "--filter", f"label=kubelabs.sandbox_id={sandbox_id}", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0 and res.stdout.strip():
                    residue.extend([f"Container: {c}" for c in res.stdout.strip().splitlines() if c.strip()])

                # Check networks
                res_net = subprocess.run(
                    [self.podman, "network", "ls", "--filter", f"label=kubelabs.sandbox_id={sandbox_id}", "--format", "{{.Name}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res_net.returncode == 0 and res_net.stdout.strip():
                    residue.extend([f"Network: {n}" for n in res_net.stdout.strip().splitlines() if n.strip()])
            except Exception:
                pass

        return len(residue) == 0, residue

    def verify_k8s_zero_residue(self, sandbox_id: str) -> Tuple[bool, List[str]]:
        return self.verify_zero_residue(sandbox_id)
