"""
Unit tests for Mini Production Applications Library (ApplicationLibrary).
"""

import pytest
from packages.incident_core import ApplicationLibrary, ProductionApp, ServiceNode
from packages.lab_schema import MultiContainerSpec


def test_application_library_count_and_diversity():
    apps = ApplicationLibrary.list_applications()
    assert len(apps) == 12, f"Expected 12 canonical applications, got {len(apps)}"

    categories = {a.category for a in apps}
    assert len(categories) >= 8, "Expected diverse application categories"


def test_ecommerce_microservices_spec():
    app = ApplicationLibrary.get_by_id("ecommerce-microservices")
    assert app is not None
    assert app.name == "E-Commerce OmniStore Microservices"
    assert len(app.services) >= 7
    assert len(app.traffic_flow) >= 6
    assert "checkout_latency_spike" in app.supported_faults

    # Verify translation to multi-container runtime spec
    multi_spec = app.to_multi_container_spec()
    assert isinstance(multi_spec, MultiContainerSpec)
    assert len(multi_spec.containers) == len(app.services)
    container_names = [c.name for c in multi_spec.containers]
    assert "api-gateway" in container_names
    assert "payment-service" in container_names
    assert "cache-redis" in container_names


def test_fintech_and_telemetry_apps():
    fintech = ApplicationLibrary.get_by_id("fintech-payment-pipeline")
    assert fintech is not None
    assert any(s.name == "ledger-core" for s in fintech.services)

    telemetry = ApplicationLibrary.get_by_id("streaming-telemetry-stack")
    assert telemetry is not None
    assert any(s.name == "otel-collector" for s in telemetry.services)


def test_nonexistent_application():
    missing = ApplicationLibrary.get_by_id("non-existent-app-999")
    assert missing is None
