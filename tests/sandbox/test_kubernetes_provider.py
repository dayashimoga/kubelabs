"""
Integration tests for KubernetesProvider in sandbox_runtime.
"""

import pytest
from packages.sandbox_runtime.src.k8s_provider import KubernetesProvider, KubernetesRuntimeError
from packages.lab_schema import LabSpec, EnvironmentSpec, EnvironmentType, LabRuntimeClassification


def test_k8s_provider_availability_flags():
    provider = KubernetesProvider()
    assert isinstance(provider.is_podman_available, bool)
    assert isinstance(provider.is_kubectl_available, bool)


def test_k8s_provider_zero_residue_initially_clean():
    provider = KubernetesProvider()
    clean, residue = provider.verify_zero_residue("test-init-clean")
    assert clean is True
    assert len(residue) == 0


def test_k8s_provider_nonexistent_command():
    provider = KubernetesProvider()
    code, stdout, stderr = provider.execute_kubectl("non-existent-sandbox", "get pods")
    assert code != 0
    assert "not found" in stderr


def test_k8s_destroy_clean_lifecycle():
    provider = KubernetesProvider()
    res = provider.destroy_k8s_environment("non-existent-sandbox")
    assert res is True
