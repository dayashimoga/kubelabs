from pathlib import Path
import pytest
from packages.lab_schema import LabRegistry
from packages.sandbox_runtime import SandboxManager
from packages.validator_core import ValidatorEngine, ExecutionContext


def test_k8s_zero_endpoints_diagnostic_workflow():
    registry = LabRegistry()
    registry.load_from_directory(Path("labs"))
    lab = registry.get_by_id("k8s-zero-endpoints")
    assert lab is not None

    manager = SandboxManager()
    session = manager.create_sandbox(lab, force_simulation=True)
    sim = session.simulator
    assert sim is not None

    # Step 1: kubectl get endpoints checkout-svc
    rc, out, _ = sim.execute_command("kubectl get endpoints checkout-svc")
    assert rc == 0
    assert "checkout-svc" in out
    assert "<none>" in out

    # Step 2: kubectl get pods --show-labels
    rc, out, _ = sim.execute_command("kubectl get pods --show-labels")
    assert rc == 0
    assert "LABELS" in out
    assert "app=checkout-service" in out

    # Step 3: kubectl describe svc checkout-svc
    rc, out, _ = sim.execute_command("kubectl describe svc checkout-svc")
    assert rc == 0
    assert "checkout-svc" in out
    assert "Selector:          app=checkout-api-v2" in out
    assert "Endpoints:         <none>" in out

    # Also test cat /workspace/service.yaml
    rc, out, _ = sim.execute_command("cat /workspace/service.yaml")
    assert rc == 0
    assert "checkout-api-v2" in out

    # Step 4: Fix selector via sed -i
    rc, out, err = sim.execute_command("sed -i 's/checkout-api-v2/checkout-service/' /workspace/service.yaml")
    assert rc == 0

    # Step 5: Validate endpoints are populated
    rc, out, _ = sim.execute_command("kubectl get endpoints checkout-svc")
    assert rc == 0
    assert "10.244.1.44:8080" in out

    # Step 6: Validate describe svc shows updated endpoints and selector
    rc, out, _ = sim.execute_command("kubectl describe svc checkout-svc")
    assert rc == 0
    assert "Selector:          app=checkout-service" in out
    assert "Endpoints:         10.244.1.44:8080" in out

    # Step 7: Validate describe ep checkout-svc
    rc, out, _ = sim.execute_command("kubectl describe ep checkout-svc")
    assert rc == 0
    assert "Addresses:          10.244.1.44:8080" in out

    # Step 8: Validate with ValidatorEngine
    validator = ValidatorEngine()
    context = ExecutionContext(
        sandbox_id=session.session_id,
        simulation_state=sim.state,
    )
    report = validator.validate_rules(lab.tasks[0].validators, context)
    assert report.overall_status.value == "PASS"
    assert report.total_score == 100
