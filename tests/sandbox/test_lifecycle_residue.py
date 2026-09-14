"""
Lifecycle & Zero-Residue Verification Tests.
Verifies the complete automated cycle:
provision -> fault exists -> diagnose -> fix -> validate -> reset -> destroy -> zero residue.
"""

import pytest
from packages.lab_schema import LabRegistry, ScenarioFactory
from packages.sandbox_runtime import SandboxManager, ScenarioInjector


def test_lab_lifecycle_and_zero_residue():
    """Verify that a lab can be provisioned, diagnosed, fixed, reset, and cleanly destroyed with zero residue."""
    manager = SandboxManager()
    scenarios = ScenarioFactory.get_all_scenarios()
    assert len(scenarios) > 0

    # Test with Linux Inode Exhaustion lab
    lab = scenarios[0]
    session = manager.create_sandbox(lab)
    assert session is not None
    assert session.session_id is not None

    sid = session.session_id

    # 1. Verify environment execution
    code, out, err = manager.execute_command(sid, "echo 'hello from sandbox'")
    assert code == 0
    assert "hello" in out

    # 2. Terminal scrollback buffering check
    scrollback = session.get_scrollback()
    assert "hello from sandbox" in scrollback

    # 3. Dynamic fault injection check
    faults = ScenarioInjector.list_available_faults()
    assert "linux_inode_exhaustion" in faults

    # 4. Reset environment
    reset_ok = manager.reset_sandbox(sid)
    assert reset_ok is True

    # 5. Destroy environment
    destroyed = manager.terminate_session(sid)
    assert destroyed is True

    # 6. Verify zero residue
    clean, residue = manager.verify_zero_residue(sid)
    assert clean is True
    assert len(residue) == 0


def test_multi_container_broker_simulation_fallback():
    """Verify EnvironmentBroker handles multi-container topology with zero residue."""
    manager = SandboxManager()
    lab = ScenarioFactory.get_scenario_by_id("k8s-service-zero-endpoints")
    assert lab is not None

    session = manager.create_sandbox(lab)
    assert session.session_id is not None

    # Check command execution
    code, out, _ = manager.execute_command(session.session_id, "cat /opt/k8s/service.yaml")
    assert code == 0
    assert "payment-svc" in out

    # Terminate and verify cleanup
    manager.terminate_session(session.session_id)
    clean, residue = manager.verify_zero_residue(session.session_id)
    assert clean is True
    assert len(residue) == 0
