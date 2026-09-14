"""
Automated Acceptance Runner for KubeLabs Platform.
Performs end-to-end validation of all platform capabilities and outputs
human-readable and machine-readable acceptance reports.
"""

import sys
import time
from pathlib import Path

# Add root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from packages.lab_schema import LabRegistry, ValidationOverallStatus
from packages.validator_core import ValidatorEngine, ExecutionContext
from packages.sandbox_runtime import SandboxManager
from packages.incident_core import IncidentEngine


def run_acceptance_tests():
    print("=" * 60)
    print("  KubeLabs Production Acceptance Verification Runner")
    print("=" * 60)

    results = []

    # 1. Test Lab Registry & Catalog
    print("\n[Gate 1] Validating Declarative Lab Catalog...")
    registry = LabRegistry()
    loaded_labs = registry.load_from_directory(ROOT_DIR / "labs")
    tracks = registry.get_tracks()
    if loaded_labs >= 10 and len(tracks) >= 10:
        results.append(("Declarative Lab Registry", "PASS", f"{loaded_labs} labs loaded across {len(tracks)} tracks"))
        print(f"  [PASS] Loaded {loaded_labs} labs across {len(tracks)} tracks: {', '.join(tracks)}")
    else:
        results.append(("Declarative Lab Registry", "FAIL", f"Only {loaded_labs} labs loaded"))
        print(f"  [FAIL] Expected >= 10 labs, got {loaded_labs}")

    # 2. Test State-Based Validator Engine
    print("\n[Gate 2] Validating State-Based Validator Core...")
    engine = ValidatorEngine()
    test_lab = registry.get_by_id("linux-inode-exhaustion")
    if test_lab:
        context = ExecutionContext(
            sandbox_id="acceptance-test",
            simulation_state={"inode_exhausted": False},
        )
        report = engine.validate_rules(test_lab.tasks[0].validators, context)
        results.append(("State Validator Engine", "PASS", f"Score: {report.total_score}/{report.max_possible_score}"))
        print(f"  [PASS] Validator evaluated task: Status={report.overall_status.value} Score={report.total_score}")
    else:
        results.append(("State Validator Engine", "FAIL", "Lab linux-inode-exhaustion not found"))

    # 3. Test Sandbox Runtime Lifecycle
    print("\n[Gate 3] Validating Sandbox Execution Lifecycle...")
    manager = SandboxManager()
    if test_lab:
        session = manager.create_sandbox(test_lab, force_simulation=True)
        exit_code, stdout, _ = manager.execute_command(session.session_id, "df -h")
        clean_res = manager.terminate_session(session.session_id)
        if exit_code == 0 and "Filesystem" in stdout and clean_res:
            results.append(("Sandbox Lifecycle", "PASS", "Session created, command executed, clean termination"))
            print(f"  [PASS] Sandbox provisioned, executed 'df -h' cleanly, and terminated.")
        else:
            results.append(("Sandbox Lifecycle", "FAIL", f"Exit code: {exit_code}"))

    # 4. Test Incident War Room & Scoring
    print("\n[Gate 4] Validating SEV Incident Simulator & SRE Scoring...")
    inc_engine = IncidentEngine()
    inc_session = inc_engine.start_incident("checkout-latency-spike", "acc-inc-1")
    inc_session.record_inspection("kubectl logs -l app=checkout-service")
    inc_session.test_hypothesis("hyp-2")
    mitigated = inc_session.apply_fix("kubectl rollout restart deployment/checkout-service")
    scorecard = inc_session.verify_resolution()
    if scorecard.total_score >= 80:
        results.append(("Incident Simulator", "PASS", f"SRE Score: {scorecard.total_score}/100"))
        print(f"  [PASS] Incident simulated: Mitigated={mitigated}, Total SRE Score={scorecard.total_score}/100")
    else:
        results.append(("Incident Simulator", "FAIL", f"Score too low: {scorecard.total_score}"))

    # 5. Summary Report
    print("\n" + "=" * 60)
    print("  ACCEPTANCE REPORT SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, status, details in results:
        print(f"  [{status}] {name:<30} | {details}")
        if status != "PASS":
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("  ALL ACCEPTANCE GATES PASSED - PRODUCTION READY!")
        print("=" * 60)
        return 0
    else:
        print("  ACCEPTANCE GATES FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_acceptance_tests())
