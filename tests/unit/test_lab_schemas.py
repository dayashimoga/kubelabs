"""
Unit tests to validate 100% of declarative lab YAML definitions.
"""

from pathlib import Path
import pytest
from packages.lab_schema import LabRegistry, LabSpec


def test_all_labs_load_and_validate():
    labs_dir = Path(__file__).resolve().parents[2] / "labs"
    assert labs_dir.exists(), f"Labs directory not found at {labs_dir}"

    registry = LabRegistry()
    loaded_count = registry.load_from_directory(labs_dir)

    assert loaded_count >= 10, f"Expected at least 10 labs loaded, got {loaded_count}"

    tracks = registry.get_tracks()
    assert "linux" in tracks
    assert "docker" in tracks
    assert "kubernetes" in tracks
    assert "helm-kustomize" in tracks
    assert "terraform" in tracks
    assert "ansible" in tracks
    assert "git-ci" in tracks
    assert "argocd" in tracks
    assert "observability" in tracks
    assert "istio" in tracks
    assert "aws-eks" in tracks
    assert "capstones" in tracks

    # Validate individual lab attributes
    for lab in registry.list_all():
        assert lab.id
        assert lab.title
        assert lab.track
        assert len(lab.objectives) > 0
        assert len(lab.tasks) > 0
        for task in lab.tasks:
            assert task.id
            assert task.title
            assert len(task.validators) > 0
