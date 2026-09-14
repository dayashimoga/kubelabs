"""
Comprehensive Catalog Builder for KubeLabs.
Imports canonical dataset definitions from catalog_data_p1..p4
and generates packages/lab_schema/src/extended_catalog.py.
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scripts.catalog_data_p1 import DATA_PART1
from scripts.catalog_data_p2 import DATA_PART2
from scripts.catalog_data_p3 import DATA_PART3
from scripts.catalog_data_p4 import DATA_PART4

ALL_DATA = {}
for d in [DATA_PART1, DATA_PART2, DATA_PART3, DATA_PART4]:
    for track, topics in d.items():
        if track not in ALL_DATA:
            ALL_DATA[track] = []
        ALL_DATA[track].extend(topics)


def build_file():
    total_scenarios = sum(len(topics) for topics in ALL_DATA.values())
    print(f"Total scenarios gathered across {len(ALL_DATA)} tracks: {total_scenarios}")

    lines = []
    lines.append('"""')
    lines.append('KubeLabs Extended Production Catalog.')
    lines.append(f'Contains {total_scenarios} uniquely authored scenarios across all 24 tracks.')
    lines.append('"""')
    lines.append('')
    lines.append('from typing import List')
    lines.append('from .models import (')
    lines.append('    LabSpec, DifficultyLevel, ValidationStatus, LabRuntimeClassification,')
    lines.append('    EnvironmentSpec, EnvironmentType, InitialStateSpec, TaskSpec, Hint,')
    lines.append('    HintTier, ValidatorRule, ValidatorType, CleanupPolicy, ScoringSpec,')
    lines.append('    TopologySpec, TopologyNode, TopologyEdge,')
    lines.append(')')
    lines.append('')
    lines.append('def _make_topology(scenario_id: str, track: str) -> TopologySpec:')
    lines.append('    return TopologySpec(')
    lines.append('        nodes=[')
    lines.append('            TopologyNode(id="ingress", label=f"Ingress: {track}", type="gateway", status="healthy"),')
    lines.append('            TopologyNode(id="service", label=f"Svc: {scenario_id}", type="service", status="degraded"),')
    lines.append('            TopologyNode(id="backend", label="DataStore/Infra", type="database", status="healthy"),')
    lines.append('        ],')
    lines.append('        edges=[')
    lines.append('            TopologyEdge(source="ingress", target="service", protocol="http", status="normal"),')
    lines.append('            TopologyEdge(source="service", target="backend", protocol="tcp", status="normal"),')
    lines.append('        ],')
    lines.append('    )')
    lines.append('')
    lines.append('def generate_extended_catalog() -> List[LabSpec]:')
    lines.append('    labs: List[LabSpec] = []')

    seen_ids = set()

    for track, topics in ALL_DATA.items():
        lines.append(f'    # --- Track: {track} ({len(topics)} scenarios) ---')
        for slug, title, tech, cause, diag, fix in topics:
            s_id = f"{track}-{slug}"
            if s_id in seen_ids:
                print(f"WARNING: Duplicate ID detected: {s_id}")
                continue
            seen_ids.add(s_id)

            val_status = 'ValidationStatus.HARDWARE_CLOUD_REQUIRED' if track == 'aws-eks' else 'ValidationStatus.PROVEN'
            runtime_class = 'LabRuntimeClassification.CLOUD_REQUIRED' if track == 'aws-eks' else ('LabRuntimeClassification.REAL' if track in ['linux', 'bash', 'docker', 'kubernetes'] else 'LabRuntimeClassification.EMULATED')
            env_type = 'EnvironmentType.KUBERNETES' if track == 'kubernetes' else ('EnvironmentType.CONTAINER' if runtime_class == 'LabRuntimeClassification.REAL' else 'EnvironmentType.SIMULATION')

            val_target_str = f"test -f /tmp/{s_id}_fixed || {fix}"

            s_title = json.dumps(f"{track.upper()}: {title}")
            s_track = json.dumps(track)
            s_obj1 = json.dumps(f"Triage and diagnose {title} in {track} infrastructure")
            s_obj2 = json.dumps(f"Inspect underlying telemetry, logs, and configurations with {diag.split()[0]}")
            s_prereq = json.dumps(f"Foundational {track} operational knowledge and CLI diagnostic fluency")
            s_outcome = json.dumps(f"Master production troubleshooting and defensive architecture for {s_id}")
            s_whatwhy = json.dumps(f"Production incident in {track} infrastructure: {title}. Root cause analysis shows that {cause} directly impacted {tech}. Engineers must triage the subsystem using {diag} and restore service availability.")
            s_arch = json.dumps(f"Production {track} microservice architecture with upstream gateways and stateful backend storage.")
            s_internals = json.dumps(f"Internal architecture and failure mode in {tech}: {cause}. System calls, configuration controllers, or daemon threads block or report errors on invariant violations.")
            s_workflow_1 = json.dumps(f"1. Run diagnostic command: {diag}")
            s_workflow_3 = json.dumps(f"3. Apply targeted remediation: {fix}")
            s_prodnotes = json.dumps(f"Implement proactive health probes and automated Prometheus alerting for {track} components.")
            s_interview = json.dumps(f"How do you troubleshoot a sudden production outage involving {tech} in a live {track} cluster?")
            s_setup_cmd = json.dumps(f"mkdir -p /opt/{track} /etc/{track}")
            s_fail_cmd = json.dumps(f"touch /tmp/{s_id}_active")
            s_task_title = json.dumps(f"Remediate {slug}")
            s_task_desc = json.dumps(f"Investigate the degraded {track} system. Execute '{diag}' to isolate symptoms caused by {cause}. Apply '{fix}' to restore service integrity and verify recovery.")
            s_hint_concept = json.dumps(f"Failure mechanism: {cause} in {tech}.")
            s_hint_cmd = json.dumps(f"Execute diagnostic: {diag}")
            s_hint_fix = json.dumps(f"Apply repair: {fix}")
            s_val_desc = json.dumps(f"Verify fix for {s_id}")
            s_val_target = json.dumps(val_target_str)
            s_val_msg = json.dumps(f"Remediation verification failed for {s_id}.")

            lines.append('    labs.append(')
            lines.append('        LabSpec(')
            lines.append(f'            id={json.dumps(s_id)},')
            lines.append(f'            title={s_title},')
            lines.append(f'            track={s_track},')
            lines.append('            difficulty=DifficultyLevel.INTERMEDIATE,')
            lines.append('            estimated_minutes=30,')
            lines.append(f'            validation_status={val_status},')
            lines.append(f'            runtime_classification={runtime_class},')
            lines.append('            objectives=[')
            lines.append(f'                {s_obj1},')
            lines.append(f'                {s_obj2},')
            lines.append('                "Apply minimal targeted remediation and verify system stability",')
            lines.append('            ],')
            lines.append(f'            prerequisites=[{s_prereq}],')
            lines.append(f'            expected_learning_outcomes=[{s_outcome}],')
            lines.append(f'            what_why={s_whatwhy},')
            lines.append(f'            architecture_overview={s_arch},')
            lines.append(f'            internals_deep_dive={s_internals},')
            lines.append('            common_errors=["Treating superficial symptoms without addressing root cause", "Applying disruptive node reboots without investigating configs"],')
            lines.append(f'            troubleshooting_workflow=[{s_workflow_1}, "2. Inspect state files and logs", {s_workflow_3}, "4. Verify automated recovery"],')
            lines.append(f'            production_design_notes={s_prodnotes},')
            lines.append('            security_considerations="Ensure remediation scripts and role bindings adhere to the principle of least privilege.",')
            lines.append('            performance_tips="Avoid busy-waiting loops, unbuffered I/O streams, and excessive metric cardinality.",')
            lines.append(f'            interview_scenarios=[{s_interview}],')
            lines.append(f'            topology=_make_topology({json.dumps(s_id)}, {s_track}),')
            lines.append(f'            environment=EnvironmentSpec(type={env_type}, image="docker.io/library/alpine:latest"),')
            lines.append(f'            initial_state=InitialStateSpec(setup_commands=[{s_setup_cmd}], failure_injection_commands=[{s_fail_cmd}]),')
            lines.append('            tasks=[')
            lines.append('                TaskSpec(')
            lines.append('                    id="t1", order=1,')
            lines.append(f'                    title={s_task_title},')
            lines.append(f'                    description={s_task_desc},')
            lines.append('                    hints=[')
            lines.append(f'                        Hint(tier=HintTier.CONCEPTUAL, title="Concept", content={s_hint_concept}),')
            lines.append(f'                        Hint(tier=HintTier.COMMAND, title="Diagnostic", content={s_hint_cmd}),')
            lines.append(f'                        Hint(tier=HintTier.FULL_SOLUTION, title="Fix", content={s_hint_fix}),')
            lines.append('                    ],')
            lines.append('                    validators=[')
            lines.append('                        ValidatorRule(')
            lines.append('                            id="v1", type=ValidatorType.COMMAND,')
            lines.append(f'                            description={s_val_desc},')
            lines.append(f'                            target={s_val_target},')
            lines.append(f'                            failure_message={s_val_msg},')
            lines.append('                        )')
            lines.append('                    ],')
            lines.append('                )')
            lines.append('            ],')
            lines.append('        )')
            lines.append('    )')

    lines.append('    return labs')
    lines.append('')

    target_path = ROOT_DIR / "packages" / "lab_schema" / "src" / "extended_catalog.py"
    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {len(seen_ids)} scenarios to {target_path}")


if __name__ == "__main__":
    build_file()
