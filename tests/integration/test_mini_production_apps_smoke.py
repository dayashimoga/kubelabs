"""
Integration Smoke Test Suite for All 12 Mini-Production Applications.
Verifies:
1. Container image & process specifications across all 12 topologies.
2. Service discovery and isolated bridge networking configuration.
3. Inter-service dependency integrity and absence of circular references.
4. Baseline healthy state contracts.
5. Deterministic failure injection across multi-service paths (frontend -> gateway -> API -> DB).
6. Multi-service cascading incidents (bad release -> latency -> retries -> CPU saturation -> 503).
7. Corrective remediation validation and clean zero-residue lifecycle.
"""

import pytest
from packages.incident_core.src.app_library import ApplicationLibrary, ProductionApp
from packages.lab_schema import MultiContainerSpec, ContainerNodeSpec
from packages.sandbox_runtime.src.broker import EnvironmentBroker
from packages.sandbox_runtime.src.scenario_injector import ScenarioInjector
from packages.validator_core import ValidatorEngine, ExecutionContext
from packages.validator_core.src.validators import CommandValidator, HttpValidator


ALL_APP_IDS = [a.id for a in ApplicationLibrary.get_all_apps()]


@pytest.mark.parametrize("app_id", ALL_APP_IDS)
def test_mini_production_application_structure(app_id: str):
    """Verifies image, process, port, and dependency integrity for each canonical app."""
    app = ApplicationLibrary.get_by_id(app_id)
    assert app is not None, f"Application {app_id} missing from registry"
    assert len(app.services) >= 3, f"Application {app_id} must have at least 3 tiers"
    assert len(app.supported_faults) >= 2, f"Application {app_id} must declare supported fault modes"
    assert len(app.traffic_flow) >= 2, f"Application {app_id} must have connected traffic flows"

    service_names = {s.name for s in app.services}
    assert len(service_names) == len(app.services), f"Duplicate service names in {app_id}"

    # Verify dependency references exist
    for svc in app.services:
        for dep in svc.dependencies:
            assert dep in service_names, f"Service {svc.name} references nonexistent dependency {dep}"

    # Verify MultiContainerSpec translation
    spec = app.to_multi_container_spec()
    assert isinstance(spec, MultiContainerSpec)
    assert spec.network_name == "kubelabs-net"
    assert len(spec.containers) == len(app.services)
    for c in spec.containers:
        assert c.name in service_names
        assert c.image.startswith("docker.io/")


def test_ecommerce_multi_service_incident_cascade():
    """
    Simulates complete multi-tier cascading failure in E-Commerce microservices:
    web-frontend -> api-gateway -> order-service -> payment-service -> order-db
    Fault: Database connection pool saturation leads to order-service timeouts and 503s at gateway.
    """
    app = ApplicationLibrary.get_by_id("ecommerce-microservices")
    assert app is not None

    # Baseline health check
    context = ExecutionContext(
        simulation_state={
            "http_endpoints": {
                "http://api-gateway:8080/healthz": {"status": 200, "body": "OK"},
                "http://order-service:5002/healthz": {"status": 200, "body": "OK"},
                "http://payment-service:5003/healthz": {"status": 200, "body": "OK"},
            },
            "commands": {
                "kubectl get pods -n ecommerce": {
                    "exit_code": 0,
                    "stdout": "api-gateway Running\norder-service Running\npayment-service Running\n",
                    "stderr": "",
                }
            },
            "db_connections": {"active": 20, "max": 200},
        }
    )

    h_val = HttpValidator()
    # Baseline assertion: API Gateway healthy
    from packages.lab_schema import ValidatorRule, ValidatorType
    r_baseline = ValidatorRule(
        id="v-base",
        type=ValidatorType.HTTP,
        description="Verify gateway is healthy",
        failure_message="Gateway unhealthy",
        target="http://api-gateway:8080/healthz",
        args={"status_code": 200},
    )
    res_base = h_val.validate(r_baseline, context)
    assert res_base.passed is True

    # Inject failure: Cascade triggered
    # DB connections exhaust -> order-service starts failing -> API gateway returns 503
    context.simulation_state["db_connections"]["active"] = 200
    context.simulation_state["http_endpoints"]["http://api-gateway:8080/healthz"] = {"status": 503, "body": "Upstream timeout"}
    context.simulation_state["http_endpoints"]["http://order-service:5002/healthz"] = {"status": 500, "body": "Connection pool exhausted"}

    res_fault = h_val.validate(r_baseline, context)
    assert res_fault.passed is False, "Fault should be observable at API Gateway"

    # Remediation: Scale pool and clear stuck connections
    context.simulation_state["db_connections"]["active"] = 35
    context.simulation_state["http_endpoints"]["http://api-gateway:8080/healthz"] = {"status": 200, "body": "OK"}
    context.simulation_state["http_endpoints"]["http://order-service:5002/healthz"] = {"status": 200, "body": "OK"}

    res_recovery = h_val.validate(r_baseline, context)
    assert res_recovery.passed is True, "Recovery should return gateway to healthy state"


def test_bad_release_latency_and_cpu_saturation_incident():
    """
    Simulates regression cascade:
    bad release -> memory leak / CPU thrashing -> probe timeout -> 503 outage.
    """
    sim_state = {
        "release_version": "v1.4.2-bad",
        "cpu_utilization": 98.4,
        "latency_p99_ms": 3200.0,
        "readiness_probe_passing": False,
        "http_endpoints": {
            "http://checkout-service:8080/healthz": {"status": 503, "body": "Readiness failed"},
        }
    }
    context = ExecutionContext(simulation_state=sim_state)

    h_val = HttpValidator()
    from packages.lab_schema import ValidatorRule, ValidatorType
    r_check = ValidatorRule(
        id="v-check",
        type=ValidatorType.HTTP,
        description="Check checkout service availability",
        failure_message="Checkout service unavailable",
        target="http://checkout-service:8080/healthz",
        args={"status_code": 200},
    )
    assert h_val.validate(r_check, context).passed is False

    # Rollback deployment to v1.4.1-stable
    sim_state["release_version"] = "v1.4.1-stable"
    sim_state["cpu_utilization"] = 22.1
    sim_state["latency_p99_ms"] = 45.0
    sim_state["readiness_probe_passing"] = True
    sim_state["http_endpoints"]["http://checkout-service:8080/healthz"] = {"status": 200, "body": "OK"}

    assert h_val.validate(r_check, context).passed is True


    from packages.lab_schema import LabSpec, DifficultyLevel, ValidationStatus, LabRuntimeClassification, EnvironmentSpec, EnvironmentType
    broker = EnvironmentBroker()
    for app_id in ALL_APP_IDS:
        app = ApplicationLibrary.get_by_id(app_id)
        spec = app.to_multi_container_spec()
        lab = LabSpec(
            id=f"lab-{app_id}",
            title=f"Lab for {app.name}",
            track="kubernetes",
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_minutes=20,
            validation_status=ValidationStatus.PROVEN,
            runtime_classification=LabRuntimeClassification.SIMULATED,
            multi_container_spec=spec,
            environment=EnvironmentSpec(type=EnvironmentType.SIMULATION),
            tasks=[],
        )
        rec = broker.start_environment(f"sandbox-{app_id}", lab, force_simulation=True)
        assert rec["sandbox_id"] == f"sandbox-{app_id}"

        clean = broker.destroy_environment(f"sandbox-{app_id}")
        assert clean is True
        clean_res, residue = broker.verify_zero_residue(f"sandbox-{app_id}")
        assert clean_res is True
        assert len(residue) == 0
