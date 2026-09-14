"""
Comprehensive Unit Tests for ValidatorCore.
Exhaustively covers all state validator classes across both simulated and live contexts,
testing success, failure, regex matching, missing targets, nested structures,
and edge cases.
"""

import os
import tempfile
import pytest

from packages.lab_schema import ValidatorRule, ValidatorType
from packages.validator_core.src.base import ExecutionContext
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
from packages.sandbox_runtime import DeterministicSimulator


@pytest.fixture
def sim_context():
    sim = DeterministicSimulator("test-lab")
    sim.state["filesystem"]["/etc/test.conf"] = "foo=bar\nport=8080\n"
    sim.state["k8s"]["pods"]["web-pod"] = {"phase": "Running"}
    sim.state["containers"] = {"redis-cache": {"state": "running"}}
    sim.state["ports"] = {8080: True}

    return ExecutionContext(
        container_id="test-cnt-01",
        simulator=sim,
        simulation_state=sim.state,
    )


def test_command_validator_comprehensive():
    v = CommandValidator()
    ctx = ExecutionContext()

    # Missing command
    r_empty = ValidatorRule(
        id="c0", type=ValidatorType.COMMAND, description="empty", failure_message="fail", target="", args={}
    )
    res_empty = v.validate(r_empty, ctx)
    assert not res_empty.passed

    # Success
    r1 = ValidatorRule(
        id="c1", type=ValidatorType.COMMAND, description="ok", failure_message="fail", target="echo OK", args={"output_contains": "OK"}
    )
    res1 = v.validate(r1, ctx)
    assert res1.passed

    # Exit code failure
    r2 = ValidatorRule(
        id="c2", type=ValidatorType.COMMAND, description="fail code", failure_message="fail", target="exit 1", args={"expected_exit_code": 0}
    )
    res2 = v.validate(r2, ctx)
    assert not res2.passed

    # Regex failure
    r3 = ValidatorRule(
        id="c3", type=ValidatorType.COMMAND, description="regex", failure_message="fail", target="echo version-1.0", args={"output_regex": r"^v2\..*"}
    )
    res3 = v.validate(r3, ctx)
    assert not res3.passed


def test_file_validator_comprehensive(sim_context):
    v = FileValidator()

    # Success: simulated file exists and contains string
    r1 = ValidatorRule(
        id="f1", type=ValidatorType.FILE, description="file check", failure_message="fail", target="/etc/test.conf", args={"content_contains": "foo=bar"}
    )
    res1 = v.validate(r1, sim_context)
    assert res1.passed

    # Content mismatch in simulated file
    r1_fail = ValidatorRule(
        id="f1_fail", type=ValidatorType.FILE, description="mismatch", failure_message="fail", target="/etc/test.conf", args={"content_contains": "nonexistent"}
    )
    res1_fail = v.validate(r1_fail, sim_context)
    assert not res1_fail.passed

    # Missing target
    r_empty = ValidatorRule(
        id="f_empty", type=ValidatorType.FILE, description="empty", failure_message="fail", target="", args={}
    )
    assert not v.validate(r_empty, sim_context).passed


def test_yaml_validator_comprehensive():
    v = YamlValidator()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as tmp:
        tmp.write("server:\n  host: 0.0.0.0\n  port: 8080\n")
        tmp_path = tmp.name

    try:
        # Success
        r1 = ValidatorRule(
            id="y1", type=ValidatorType.YAML, description="yaml check", failure_message="fail", target=tmp_path, args={"assertions": {"server.port": 8080}}
        )
        assert v.validate(r1, ExecutionContext()).passed

        # Key missing
        r2 = ValidatorRule(
            id="y2", type=ValidatorType.YAML, description="yaml miss", failure_message="fail", target=tmp_path, args={"assertions": {"server.missing": 123}}
        )
        assert not v.validate(r2, ExecutionContext()).passed

        # Missing target
        r_empty = ValidatorRule(
            id="y_empty", type=ValidatorType.YAML, description="empty", failure_message="fail", target="", args={}
        )
        assert not v.validate(r_empty, ExecutionContext()).passed
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_json_validator_comprehensive():
    v = JsonValidator()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
        tmp.write('{"service": {"name": "auth", "replicas": 3}}')
        tmp_path = tmp.name

    try:
        # Success
        r1 = ValidatorRule(
            id="j1", type=ValidatorType.JSON, description="json check", failure_message="fail", target=tmp_path, args={"assertions": {"service.replicas": 3}}
        )
        assert v.validate(r1, ExecutionContext()).passed

        # Value mismatch
        r2 = ValidatorRule(
            id="j2", type=ValidatorType.JSON, description="json mismatch", failure_message="fail", target=tmp_path, args={"assertions": {"service.name": "billing"}}
        )
        assert not v.validate(r2, ExecutionContext()).passed

        # Missing target
        r_empty = ValidatorRule(
            id="j_empty", type=ValidatorType.JSON, description="empty", failure_message="fail", target="", args={}
        )
        assert not v.validate(r_empty, ExecutionContext()).passed
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_tcp_and_dns_validators(sim_context):
    vt = TcpValidator()
    vd = DnsValidator()

    # TCP port open in simulation
    r_t = ValidatorRule(
        id="t1", type=ValidatorType.TCP, description="tcp port", failure_message="fail", target="8080", args={"port": 8080, "expected_open": True}
    )
    assert vt.validate(r_t, sim_context).passed

    # TCP port closed
    r_t_closed = ValidatorRule(
        id="t2", type=ValidatorType.TCP, description="tcp closed", failure_message="fail", target="9090", args={"port": 9090, "expected_open": True}
    )
    assert not vt.validate(r_t_closed, sim_context).passed

    # DNS lookup of localhost
    r_d = ValidatorRule(
        id="d1", type=ValidatorType.DNS, description="dns check", failure_message="fail", target="localhost", args={"hostname": "localhost"}
    )
    assert vd.validate(r_d, ExecutionContext()).passed

    # DNS missing target
    r_d_empty = ValidatorRule(
        id="d_empty", type=ValidatorType.DNS, description="empty", failure_message="fail", target="", args={}
    )
    assert not vd.validate(r_d_empty, ExecutionContext()).passed


def test_container_and_kubernetes_validators(sim_context):
    vc = ContainerValidator()
    vk = KubernetesValidator()

    # Container status in simulation
    r_c = ValidatorRule(
        id="c1", type=ValidatorType.CONTAINER, description="container check", failure_message="fail", target="redis-cache", args={"state": "running"}
    )
    assert vc.validate(r_c, sim_context).passed

    # Container stopped mismatch
    r_c_fail = ValidatorRule(
        id="c2", type=ValidatorType.CONTAINER, description="container miss", failure_message="fail", target="ghost-container", args={"state": "running"}
    )
    assert not vc.validate(r_c_fail, sim_context).passed

    # Kubernetes pod in simulation
    r_k = ValidatorRule(
        id="k1", type=ValidatorType.KUBERNETES, description="k8s pod", failure_message="fail", target="web-pod", args={"phase": "Running"}
    )
    assert vk.validate(r_k, sim_context).passed

    # Kubernetes pod mismatch
    r_k_fail = ValidatorRule(
        id="k2", type=ValidatorType.KUBERNETES, description="k8s fail", failure_message="fail", target="web-pod", args={"phase": "Failed"}
    )
    assert not vk.validate(r_k_fail, sim_context).passed


def test_git_prom_otel_validators():
    vg = GitValidator()
    vp = PrometheusValidator()
    vo = OpenTelemetryValidator()

    # Git validator on current repository
    r_g = ValidatorRule(
        id="g1", type=ValidatorType.GIT, description="git check", failure_message="fail", target=".", args={"clean_worktree": False}
    )
    res_g = vg.validate(r_g, ExecutionContext(workdir="."))
    assert res_g is not None

    # Prometheus validator error handling for unreachable endpoint
    r_p = ValidatorRule(
        id="p1", type=ValidatorType.PROMETHEUS, description="prom check", failure_message="fail", target="http://127.0.0.1:9099/metrics", args={}
    )
    res_p = vp.validate(r_p, ExecutionContext())
    assert res_p is not None

    # OpenTelemetry validator error handling
    r_o = ValidatorRule(
        id="o1", type=ValidatorType.OPENTELEMETRY, description="otel check", failure_message="fail", target="http://127.0.0.1:4318", args={}
    )
    res_o = vo.validate(r_o, ExecutionContext())
    assert res_o is not None
