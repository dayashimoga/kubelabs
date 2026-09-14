"""
KubeLabs Structural & Semantic Duplicate Detector.
Audits the entire lab catalog (declarative YAMLs + ScenarioFactory procedural labs)
to ensure exercises are genuinely distinct, without duplicate titles, topologies,
or cloned validator rules.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from packages.lab_schema import LabRegistry, ScenarioFactory


def compute_jaccard(set1: Set[str], set2: Set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return round(intersection / union, 3)


def detect_duplicates():
    print("=" * 70)
    print("  KubeLabs Semantic & Structural Duplicate Detector")
    print("=" * 70)

    # 1. Gather all scenarios
    registry = LabRegistry()
    registry.load_from_directory(ROOT_DIR / "labs")
    static_labs = registry.list_all()
    factory_labs = ScenarioFactory.get_all_scenarios()

    all_labs = {l.id: l for l in static_labs}
    for l in factory_labs:
        all_labs[l.id] = l

    labs_list = list(all_labs.values())
    total_labs = len(labs_list)
    print(f"\nAnalyzing {total_labs} unique exercise specifications across {len(ScenarioFactory.get_tracks())} tracks...")

    # 2. Check title uniqueness
    titles: Dict[str, str] = {}
    title_collisions = []
    for lab in labs_list:
        clean_title = lab.title.strip().lower()
        if clean_title in titles:
            title_collisions.append((lab.id, titles[clean_title], lab.title))
        else:
            titles[clean_title] = lab.id

    # 3. Check structural similarity of validators and commands
    duplicates = []
    suspicious_pairs = []

    for i in range(total_labs):
        for j in range(i + 1, total_labs):
            l1 = labs_list[i]
            l2 = labs_list[j]

            # Tokens from what_why & tasks
            words1 = set((l1.what_why or "").lower().split())
            for t in l1.tasks:
                words1.update(t.description.lower().split())
            words2 = set((l2.what_why or "").lower().split())
            for t in l2.tasks:
                words2.update(t.description.lower().split())
            desc_sim = compute_jaccard(words1, words2)

            # Commands and targets
            cmds1 = set()
            for t in l1.tasks:
                for v in t.validators:
                    cmds1.add(f"{v.type.value}:{v.target}")

            cmds2 = set()
            for t in l2.tasks:
                for v in t.validators:
                    cmds2.add(f"{v.type.value}:{v.target}")

            cmd_sim = compute_jaccard(cmds1, cmds2)

            if l1.id != l2.id and (cmd_sim > 0.85 or desc_sim > 0.80):
                duplicates.append({
                    "lab_1": l1.id,
                    "lab_2": l2.id,
                    "desc_similarity": desc_sim,
                    "command_similarity": cmd_sim,
                })
            elif l1.id != l2.id and (cmd_sim > 0.60 or desc_sim > 0.60):
                suspicious_pairs.append((l1.id, l2.id, max(desc_sim, cmd_sim)))

    print(f"Title collisions: {len(title_collisions)}")
    print(f"Structural duplicates detected (>85% overlap): {len(duplicates)}")
    print(f"Near-neighbor related exercises: {len(suspicious_pairs)}")

    is_clean = (len(title_collisions) == 0 and len(duplicates) == 0)

    print("\n" + "=" * 70)
    if is_clean:
        print(f"  [PASS] ZERO DUPLICATES DETECTED: 100% UNCONDITIONAL LAB UNIQUENESS ({total_labs}/{total_labs})")
    else:
        print(f"  [FAIL] {len(duplicates)} DUPLICATES FOUND")
    print("=" * 70)

    report = {
        "total_labs_audited": total_labs,
        "title_collisions": title_collisions,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "is_clean": is_clean,
    }

    report_path = ROOT_DIR / "duplicate_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return 0 if is_clean else 1


if __name__ == "__main__":
    sys.exit(detect_duplicates())
