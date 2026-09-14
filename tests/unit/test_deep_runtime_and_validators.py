"""
Deep Runtime and Validator Coverage Tests.
Tests KubernetesProvider, EnvironmentBroker multi-container and k8s flows,
advanced Validator rules, and Troubleshooting service progressive hint mechanics.
"""

import pytest
import subprocess
from unittest.mock import MagicMock, patch

from packages.lab_schema import (
    LabSpec,
    DifficultyLevel,
    LabRuntimeClassification,
    EnvironmentSpec,
    EnvironmentType,
    MultiContainerSpec,
    ContainerNodeSpec,
    InitialStateSpec,
    CleanupPolicy,
    ValidatorRule,
    ValidatorType,
    ValidationOverallStatus,
    TaskSpec,
    Hint,
    HintTier,
)
from packages.validator_core import ValidatorEngine, ExecutionContext
from packages.validator_core.src.validators import (
    CommandValidator,
    FileValidator,
    YamlValidator,
    JsonValidator,
    HttpValidator,
    TcpValidator,
    DnsValidator,
    ContainerValidator,
    KubernetesValidator,
    GitValidator,
    PrometheusValidator,
    OpenTelemetryValidator,
)
from packages.sandbox_runtime import (
    KubernetesProvider,
    EnvironmentBroker,
    RuntimeProvisioningError,
    DeterministicSimulator,
)
from packages.incident_core.src.microservices_topology import (
    get_production_microservices_topology,
    get_correlated_trace,
)
from apps.api.src.services.troubleshooting_service import TroubleshootingAdvisor


# ---------------------------------------------------------------------------
# 1. KubernetesProvider Tests
# ---------------------------------------------------------------------------

def test_k8s_provider_availability():
    prov = KubernetesProvider(podman_binary="podman")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="podman 5.0.0")
        assert prov.is_podman_available is True

        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        assert prov.is_kubectl_available is False


def test_k8s_provider_provision_and_destroy_namespace():
    prov = KubernetesProvider()
    lab = LabSpec(
        id="k8s-net-test",
        title="K8s Net Test",
        slug="k8s-net-test",
        track="kubernetes",
        difficulty=DifficultyLevel.BEGINNER,
        estimated_minutes=15,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(type=EnvironmentType.KUBERNETES),
        initial_state=InitialStateSpec(),
        tasks=[],
        cleanup_policy=CleanupPolicy(),
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="created", stderr="")
        rec = prov._provision_isolated_namespace("sbx-123", "kubelabs-sbx-123", lab)
        assert rec["mode"] == "namespace"
        assert "kubelabs-sbx-123" in prov.active_namespaces["sbx-123"]["namespace"]

        # Execute kubectl in namespace
        mock_run.return_value = MagicMock(returncode=0, stdout="pod-1 Running", stderr="")
        code, out, _ = prov.execute_kubectl("sbx-123", "get pods")
        assert code == 0
        assert "pod-1" in out

        # Destroy namespace
        mock_run.return_value = MagicMock(returncode=0, stdout="deleted", stderr="")
        destroyed = prov.destroy_k8s_environment("sbx-123")
        assert destroyed is True
        assert "sbx-123" not in prov.active_namespaces

        # Zero residue
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        clean, residue = prov.verify_k8s_zero_residue("sbx-123")
        assert clean is True
        assert len(residue) == 0


def test_k8s_provider_provision_and_destroy_k3s_container():
    prov = KubernetesProvider()
    lab = LabSpec(
        id="k8s-k3s-test",
        title="K3s Test",
        slug="k8s-k3s-test",
        track="kubernetes",
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=20,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(type=EnvironmentType.KUBERNETES),
        initial_state=InitialStateSpec(),
        tasks=[],
        cleanup_policy=CleanupPolicy(),
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="container-hash-id-999\n", stderr="")
        rec = prov._provision_k3s_container("sbx-456", lab)
        assert rec["mode"] == "k3s-container"
        assert "sbx-456" in prov.active_clusters

        # Destroy k3s container
        mock_run.return_value = MagicMock(returncode=0, stdout="removed", stderr="")
        destroyed = prov.destroy_k8s_environment("sbx-456")
        assert destroyed is True
        assert "sbx-456" not in prov.active_clusters


# ---------------------------------------------------------------------------
# 2. EnvironmentBroker Multi-Container Tests
# ---------------------------------------------------------------------------

def test_broker_multi_container_lifecycle():
    broker = EnvironmentBroker(podman_binary="podman")
    lab = LabSpec(
        id="multi-c-test",
        title="Multi Container Test",
        slug="multi-c-test",
        track="docker",
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=20,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(
            type=EnvironmentType.HYBRID,
            multi_container=MultiContainerSpec(
                containers=[
                    ContainerNodeSpec(name="web", image="nginx:alpine", ports=["80:80"]),
                    ContainerNodeSpec(name="api", image="python:3.11-alpine", environment={"PORT": "5000"}),
                ]
            ),
        ),
        initial_state=InitialStateSpec(),
        tasks=[],
        cleanup_policy=CleanupPolicy(),
    )

    with patch.object(EnvironmentBroker, "is_podman_available", True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="c-id-123\n", stderr="")
            rec = broker.start_environment("mc-sbx-1", lab)
            assert rec["provider"] == "podman-multi"
            assert "mc-sbx-1" in broker.active_environments

            # Execute command on multi-container
            mock_run.return_value = MagicMock(returncode=0, stdout="Linux web 6.1", stderr="")
            code, out, _ = broker.execute_command("mc-sbx-1", "uname -a", target_container="web")
            assert code == 0
            assert "Linux" in out

            # Reset multi-container
            mock_run.return_value = MagicMock(returncode=0, stdout="restarted", stderr="")
            reset_ok = broker.reset_environment("mc-sbx-1")
            assert reset_ok is True

            # Destroy multi-container
            mock_run.return_value = MagicMock(returncode=0, stdout="cleaned", stderr="")
            dest_ok = broker.destroy_environment("mc-sbx-1")
            assert dest_ok is True
            assert "mc-sbx-1" not in broker.active_environments

            # Zero residue check
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            clean, residue = broker.verify_zero_residue("mc-sbx-1")
            assert clean is True


def test_broker_strict_real_failure_raises():
    broker = EnvironmentBroker(podman_binary="nonexistent-podman")
    lab = LabSpec(
        id="strict-real-lab",
        title="Strict Real Lab",
        slug="strict-real-lab",
        track="docker",
        difficulty=DifficultyLevel.ADVANCED,
        estimated_minutes=30,
        runtime_classification=LabRuntimeClassification.REAL,
        environment=EnvironmentSpec(type=EnvironmentType.CONTAINER),
        initial_state=InitialStateSpec(),
        tasks=[],
        cleanup_policy=CleanupPolicy(),
    )

    with patch.object(EnvironmentBroker, "is_podman_available", False):
        with pytest.raises(RuntimeProvisioningError):
            broker.start_environment("strict-sbx", lab, force_simulation=False)


# ---------------------------------------------------------------------------
# 3. Advanced Validator Rules Tests
# ---------------------------------------------------------------------------

def test_advanced_validators_coverage():
    ctx = ExecutionContext(
        simulation_state={
            "files": {
                "/etc/app/config.yaml": "server:\n  port: 8080\n  tls: true\n  workers: 4\n",
                "/etc/app/config.json": '{"database": {"host": "db.internal", "port": 5432, "ssl": true}}',
                "/var/log/audit.log": "line1\nline2\nline3\nline4\n",
            },
            "k8s": {
                "deployments": {
                    "api-deploy": {"replicas": 3, "available": 3, "ready": True}
                },
                "pods": {
                    "api-pod-1": {"status": "Running", "ready": True, "restarts": 0}
                },
            },
            "containers": {
                "redis-cache": {"status": "running", "labels": {"app": "cache"}}
            },
            "git": {
                "branch": "main",
                "last_commit": "feat: harden ingress tls",
                "clean": True,
            },
            "metrics": {
                "http_requests_total": 450.0,
                "error_rate": 0.01,
            },
            "traces": {
                "checkout_flow": {"spans": 12, "errors": 0}
            },
        }
    )

    # 1. YamlValidator
    y_val = YamlValidator()
    r_yaml = ValidatorRule(
        id="y1",
        type=ValidatorType.YAML,
        description="Check YAML port",
        failure_message="Port incorrect",
        target="/etc/app/config.yaml",
        args={"path": "server.port", "expected_value": 8080},
    )
    res_yaml = y_val.validate(r_yaml, ctx)
    assert res_yaml.passed is True

    # 2. JsonValidator
    j_val = JsonValidator()
    r_json = ValidatorRule(
        id="j1",
        type=ValidatorType.JSON,
        description="Check JSON DB host",
        failure_message="Host incorrect",
        target="/etc/app/config.json",
        args={"path": "database.host", "expected_value": "db.internal"},
    )
    res_json = j_val.validate(r_json, ctx)
    assert res_json.passed is True

    # 3. FileValidator line count
    f_val = FileValidator()
    r_file = ValidatorRule(
        id="f1",
        type=ValidatorType.FILE,
        description="Check audit log size",
        failure_message="Audit log invalid",
        target="/var/log/audit.log",
        args={"min_lines": 3, "contains": "line2"},
    )
    res_file = f_val.validate(r_file, ctx)
    assert res_file.passed is True

    # 4. KubernetesValidator
    k_val = KubernetesValidator()
    r_k8s = ValidatorRule(
        id="k1",
        type=ValidatorType.KUBERNETES,
        description="Check API deploy replicas",
        failure_message="Replicas mismatch",
        target="deployment/api-deploy",
        args={"field": "replicas", "expected_value": 3},
    )
    res_k8s = k_val.validate(r_k8s, ctx)
    assert res_k8s.passed is True

    # 5. ContainerValidator
    c_val = ContainerValidator()
    r_cont = ValidatorRule(
        id="c1",
        type=ValidatorType.CONTAINER,
        description="Check Redis running",
        failure_message="Redis not running",
        target="redis-cache",
        args={"status": "running"},
    )
    res_cont = c_val.validate(r_cont, ctx)
    assert res_cont.passed is True

    # 6. GitValidator
    g_val = GitValidator()
    r_git = ValidatorRule(
        id="g1",
        type=ValidatorType.GIT,
        description="Check branch is main",
        failure_message="Not on main branch",
        target="branch",
        args={"expected_branch": "main"},
    )
    res_git = g_val.validate(r_git, ctx)
    assert res_git.passed is True

    # 7. PrometheusValidator
    p_val = PrometheusValidator()
    r_prom = ValidatorRule(
        id="p1",
        type=ValidatorType.PROMETHEUS,
        description="Check http requests",
        failure_message="Metric threshold not reached",
        target="http_requests_total",
        args={"threshold": 400.0, "operator": ">="},
    )
    res_prom = p_val.validate(r_prom, ctx)
    assert res_prom.passed is True

    # 8. OpenTelemetryValidator
    o_val = OpenTelemetryValidator()
    r_otel = ValidatorRule(
        id="o1",
        type=ValidatorType.OPENTELEMETRY,
        description="Check checkout trace spans",
        failure_message="Trace spans incomplete",
        target="checkout_flow",
        args={"min_spans": 10},
    )
    res_otel = o_val.validate(r_otel, ctx)
    assert res_otel.passed is True


# ---------------------------------------------------------------------------
# 4. Troubleshooting Progressive Hints & Full Solution
# ---------------------------------------------------------------------------

def test_troubleshooting_progressive_hints():
    advisor = TroubleshootingAdvisor()
    task = TaskSpec(
        id="task-debug",
        order=1,
        title="Debug CrashLoop",
        description="Resolve pod failure",
        hints=[
            Hint(tier=HintTier.CONCEPTUAL, title="Concept", content="Examine exit code 137"),
            Hint(tier=HintTier.AREA, title="Area", content="Inspect container memory limits"),
            Hint(tier=HintTier.COMMAND, title="Command", content="kubectl describe pod -l app=worker"),
            Hint(tier=HintTier.STRONG_CLUE, title="Clue", content="Check OOMKilled events"),
            Hint(tier=HintTier.FULL_SOLUTION, title="Solution", content="Increase memory limit to 512Mi"),
        ],
    )

    # Tier 1
    h1 = advisor.get_hint_for_tier(task, 1)
    assert h1 is not None
    assert "exit code 137" in h1.content

    # Tier 2
    h2 = advisor.get_hint_for_tier(task, 2)
    assert h2 is not None
    assert "memory limits" in h2.content

    # Tier 3
    h3 = advisor.get_hint_for_tier(task, 3)
    assert h3 is not None
    assert "kubectl describe" in h3.content

    # Tier 4 (Strong clue)
    h4 = advisor.get_hint_for_tier(task, 4)
    assert h4 is not None
    assert "OOMKilled" in h4.content

    # Tier 5 (Full Solution)
    h5 = advisor.get_hint_for_tier(task, 5)
    assert h5 is not None
    assert "512Mi" in h5.content


# ---------------------------------------------------------------------------
# 5. Microservices Topology
# ---------------------------------------------------------------------------

def test_microservices_topology_graph():
    topo = get_production_microservices_topology()
    assert topo is not None
    assert "nodes" in topo
    assert "edges" in topo
    node_ids = [n["id"] for n in topo["nodes"]]
    assert "frontend" in node_ids
    assert "api-gateway" in node_ids
    assert "checkout-service" in node_ids

    trace = get_correlated_trace("test-tr-999", duration_ms=450.0, error=True)
    assert trace["trace_id"] == "test-tr-999"
    assert len(trace["spans"]) == 4
    assert trace["spans"][0]["status"] == "ERROR"
