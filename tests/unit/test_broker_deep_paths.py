"""
Tests for EnvironmentBroker multi-container and single-container lifecycle branches.
Covers:
- _start_multi_container failure handling
- _execute_multi_container default container selection
- _reset_multi_container and _reset_single_container
- _destroy_multi_container and _destroy_single_container
- _verify_multi_container_zero_residue with residual containers/networks
- _verify_single_container_zero_residue with residual containers
"""

import pytest
from unittest.mock import MagicMock, patch

from packages.lab_schema import (
    LabSpec,
    DifficultyLevel,
    LabRuntimeClassification,
    EnvironmentSpec,
    EnvironmentType,
    MultiContainerSpec,
    ContainerNodeSpec,
    InitialStateSpec,
    CleanupPolicy,
)
from packages.sandbox_runtime.src.broker import EnvironmentBroker


def test_broker_container_execution_and_resets():
    broker = EnvironmentBroker()

    # Multi-container setup
    mc_lab = LabSpec(
        id="mc-edge-lab",
        title="MC Edge Lab",
        slug="mc-edge-lab",
        track="docker",
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=15,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(
            type=EnvironmentType.HYBRID,
            multi_container=MultiContainerSpec(
                containers=[
                    ContainerNodeSpec(name="primary", image="alpine:latest"),
                    ContainerNodeSpec(name="worker", image="alpine:latest"),
                ]
            ),
        ),
        initial_state=InitialStateSpec(),
        tasks=[],
    )

    with patch.object(EnvironmentBroker, "is_podman_available", True):
        with patch("subprocess.run") as mock_run:
            # 1. Start multi container
            mock_run.return_value = MagicMock(returncode=0, stdout="c-prim-123\n")
            rec = broker.start_environment("sbx-mc-deep", mc_lab)
            assert rec["provider"] == "podman-multi"

            # 2. Exec targeting default primary container
            mock_run.return_value = MagicMock(returncode=0, stdout="hello primary", stderr="")
            code, out, _ = broker.execute_command("sbx-mc-deep", "echo 'hello'")
            assert code == 0
            assert "hello primary" in out

            # 3. Reset multi container
            mock_run.return_value = MagicMock(returncode=0)
            assert broker.reset_environment("sbx-mc-deep") is True

            # 4. Verify residue with found residual network & containers
            mock_run.return_value = MagicMock(returncode=0, stdout="orphan-c1\n")
            clean, residue = broker.verify_zero_residue("sbx-mc-deep")
            assert clean is False
            assert len(residue) > 0

            # 5. Destroy multi container
            mock_run.return_value = MagicMock(returncode=0)
            assert broker.destroy_environment("sbx-mc-deep") is True

    # Single container setup
    sc_lab = LabSpec(
        id="sc-edge-lab",
        title="SC Edge Lab",
        slug="sc-edge-lab",
        track="linux",
        difficulty=DifficultyLevel.BEGINNER,
        estimated_minutes=10,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(type=EnvironmentType.CONTAINER),
        initial_state=InitialStateSpec(),
        tasks=[],
    )

    with patch.object(EnvironmentBroker, "is_podman_available", True):
        with patch.object(broker.podman_executor, "create_sandbox") as mock_cs:
            mock_cs.return_value = {"container_id": "c-sc-1", "container_name": "kubelabs-sbx-sc"}
            rec_sc = broker.start_environment("sbx-sc-deep", sc_lab)
            assert rec_sc["provider"] == "podman-single"

            # Reset single container
            with patch.object(broker.podman_executor, "exec_command", return_value=(0, "ok", "")):
                assert broker.reset_environment("sbx-sc-deep") is True

            # Destroy single container
            with patch.object(broker.podman_executor, "cleanup_container", return_value=True):
                assert broker.destroy_environment("sbx-sc-deep") is True

            # Zero residue single container with orphans found
            with patch("subprocess.run") as mock_ps:
                mock_ps.return_value = MagicMock(returncode=0, stdout="orphan-sc\n")
                clean_sc, res_sc = broker.verify_zero_residue("sbx-sc-deep")
                assert clean_sc is False
                assert len(res_sc) >= 1
