"""
Lab loader and parser utilities.
Loads declarative YAML lab definitions, validates against schema,
and provides indexing and track grouping.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import ValidationError
from .models import LabSpec


class LabRegistry:
    """In-memory catalog of all loaded and validated lab specifications."""

    def __init__(self):
        self._labs: Dict[str, LabSpec] = {}
        self._by_track: Dict[str, List[LabSpec]] = {}

    def load_from_directory(self, root_dir: Path) -> int:
        """Scan directory recursively for lab.yaml or *.lab.yaml files."""
        count = 0
        if not root_dir.exists():
            return 0

        yaml_files = list(root_dir.rglob("*.yaml")) + list(root_dir.rglob("*.yml"))
        for file_path in yaml_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                raw_data = yaml.safe_load(content)
                if isinstance(raw_data, dict) and "id" in raw_data and "track" in raw_data:
                    lab = LabSpec.model_validate(raw_data)
                    self.register(lab)
                    count += 1
            except (yaml.YAMLError, ValidationError, Exception) as exc:
                # Log or handle invalid files gracefully
                print(f"[LabRegistry] Warning loading {file_path}: {exc}")
        return count

    def register(self, lab: LabSpec) -> None:
        self._labs[lab.id] = lab
        if lab.track not in self._by_track:
            self._by_track[lab.track] = []
        # Update or append
        existing = [i for i, item in enumerate(self._by_track[lab.track]) if item.id == lab.id]
        if existing:
            self._by_track[lab.track][existing[0]] = lab
        else:
            self._by_track[lab.track].append(lab)

    def get_by_id(self, lab_id: str) -> Optional[LabSpec]:
        return self._labs.get(lab_id)

    def list_all(self) -> List[LabSpec]:
        return list(self._labs.values())

    def list_by_track(self, track: str) -> List[LabSpec]:
        return self._by_track.get(track, [])

    def get_tracks(self) -> List[str]:
        return sorted(list(self._by_track.keys()))
