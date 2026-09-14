"""
Integration tests for ScenarioInjector compound failure chains.
"""

import pytest
from packages.sandbox_runtime import ScenarioInjector


def test_compound_failure_catalog_keys():
    faults = ScenarioInjector.list_available_faults()
    assert "bad_deployment_cascade" in faults
    assert "memory_leak_oom_cascade" in faults
    assert "dns_timeout_cascade" in faults
    assert "db_pool_exhaustion" in faults


def test_compound_fault_injection_and_repair():
    # Mock execution function that records state
    state = {}

    def mock_exec(cmd: str):
        if "touch" in cmd or "echo" in cmd:
            for part in cmd.split():
                if part.startswith("/tmp/"):
                    state[part] = True
            return 0, "mocked touch", ""
        elif "rm" in cmd:
            for part in cmd.split():
                if part.startswith("/tmp/"):
                    state.pop(part, None)
            return 0, "mocked rm", ""
        elif "test -f" in cmd:
            target = cmd.split("test -f")[-1].strip()
            return (0 if state.get(target) else 1), "", ""
        return 0, "", ""

    # Test bad_deployment_cascade
    injected, msg = ScenarioInjector.inject(mock_exec, "bad_deployment_cascade")
    assert injected is True

    repaired, r_msg = ScenarioInjector.repair(mock_exec, "bad_deployment_cascade")
    assert repaired is True


def test_unknown_fault_handling():
    def mock_exec(cmd): return 0, "", ""
    injected, msg = ScenarioInjector.inject(mock_exec, "completely_unknown_fault_xyz")
    assert injected is False
    assert "Unknown fault scenario" in msg
