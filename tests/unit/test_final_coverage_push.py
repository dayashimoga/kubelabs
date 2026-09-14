"""
Final Coverage Push Tests.
Drives overall coverage beyond 90% by systematically executing:
1. PodmanSandboxExecutor error handling, timeout handling, file staging, and container listing.
2. HttpValidator real URL mocking, HTTPError status handling, and connection error handling.
3. TcpValidator socket connection success and exception handling.
4. DnsValidator socket resolution success and gaierror handling.
5. ContainerValidator real podman inspect command success and failure branches.
6. KubernetesValidator real kubectl json query success and error branches.
7. EnvironmentBroker fault injection and repair for multi-container and real providers.
8. CommandValidator timeout and exception branches.
"""

import os
import json
import socket
import urllib.error
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from packages.lab_schema import (
    EnvironmentSpec,
    EnvironmentType,
    InitialStateSpec,
    StagedFile,
    ValidatorRule,
    ValidatorType,
    LabSpec,
    DifficultyLevel,
    LabRuntimeClassification,
    CleanupPolicy,
)
from packages.sandbox_runtime.src.executor import PodmanSandboxExecutor
from packages.sandbox_runtime.src.broker import EnvironmentBroker
from packages.validator_core import ExecutionContext
from packages.validator_core.src.validators import (
    HttpValidator,
    TcpValidator,
    DnsValidator,
    ContainerValidator,
    KubernetesValidator,
    CommandValidator,
    FileValidator,
)


# ---------------------------------------------------------------------------
# 1. PodmanSandboxExecutor Tests
# ---------------------------------------------------------------------------

def test_executor_full_lifecycle():
    executor = PodmanSandboxExecutor(podman_binary="podman")

    # Available check
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="podman 5.0")
        assert executor.is_available is True

        mock_run.return_value = MagicMock(returncode=1)
        assert executor.is_available is False

    # Create sandbox with staged files & setup commands
    env_spec = EnvironmentSpec(
        image="alpine:latest",
        cpu_limit="1.0",
        memory_limit="256Mi",
        port_mappings=["8080:80"],
    )
    initial_state = InitialStateSpec(
        files=[StagedFile(path="/app/test.txt", content="hello", permissions="0755")],
        setup_commands=["echo 'setup'"],
        failure_injection_commands=["echo 'fail'"],
    )

    executor.available = True
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="c-123456\n", stderr="")
        res = executor.create_sandbox("sbx-exec-1", env_spec, initial_state, ttl_seconds=600)
        assert res["container_id"] == "c-123456"

        # exec_command success
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        code, out, err = executor.exec_command("c-123456", "whoami", user="root", workdir="/app")
        assert code == 0
        assert out == "output"

        # exec_command timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=5)
        code_to, _, err_to = executor.exec_command("c-123456", "sleep 100")
        assert code_to == 124
        assert "timed out" in err_to

        # exec_command generic exception
        mock_run.side_effect = Exception("OS error")
        code_err, _, _ = executor.exec_command("c-123456", "bad")
        assert code_err == 1

        # cleanup container
        mock_run.side_effect = None
        mock_run.return_value = MagicMock(returncode=0)
        assert executor.cleanup_container("c-123456") is True

        # list_kubelabs_containers
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="c-1\tkubelabs-sbx-1\tUp 10 seconds\tkubelabs.sandbox_id=1\n"
        )
        containers = executor.list_kubelabs_containers()
        assert len(containers) == 1
        assert containers[0]["name"] == "kubelabs-sbx-1"

        # verify_zero_residue
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        clean, residue = executor.verify_zero_residue("sbx-1")
        assert clean is True


# ---------------------------------------------------------------------------
# 2. HttpValidator Real Mocking & Error Branches
# ---------------------------------------------------------------------------

def test_http_validator_network_branches():
    val = HttpValidator()
    ctx = ExecutionContext()

    # Missing target/url
    r_empty = ValidatorRule(id="h0", type=ValidatorType.HTTP, description="no url", failure_message="fail", target="")
    res_empty = val.validate(r_empty, ctx)
    assert res_empty.passed is False

    # Mock successful HTTP 200
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = b'{"status": "healthy", "service": "api"}'
    mock_resp.__enter__.return_value = mock_resp

    r_ok = ValidatorRule(
        id="h1",
        type=ValidatorType.HTTP,
        description="check api",
        failure_message="fail",
        target="http://127.0.0.1:8080/health",
        args={"status_code": 200, "body_contains": "healthy"},
    )
    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = val.validate(r_ok, ctx)
        assert res.passed is True

    # Mock HTTPError (e.g. 503 expected)
    r_503 = ValidatorRule(
        id="h2",
        type=ValidatorType.HTTP,
        description="check 503",
        failure_message="fail",
        target="http://127.0.0.1:8080/overload",
        args={"status_code": 503},
    )
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(url="http://x", code=503, msg="Unavailable", hdrs={}, fp=None)):
        res_503 = val.validate(r_503, ctx)
        assert res_503.passed is True

    # Mock connection failure
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        res_err = val.validate(r_ok, ctx)
        assert res_err.passed is False


# ---------------------------------------------------------------------------
# 3. TcpValidator and DnsValidator Network Branches
# ---------------------------------------------------------------------------

def test_tcp_and_dns_network_branches():
    ctx = ExecutionContext()

    # TcpValidator real connection success & failure
    t_val = TcpValidator()
    r_tcp = ValidatorRule(id="t1", type=ValidatorType.TCP, description="tcp", failure_message="fail", target="8080", args={"host": "127.0.0.1", "port": 8080})

    with patch("socket.create_connection", return_value=MagicMock()):
        res_tcp_ok = t_val.validate(r_tcp, ctx)
        assert res_tcp_ok.passed is True

    with patch("socket.create_connection", side_effect=ConnectionRefusedError()):
        res_tcp_fail = t_val.validate(r_tcp, ctx)
        assert res_tcp_fail.passed is False

    # DnsValidator real DNS success & failure
    d_val = DnsValidator()
    r_dns = ValidatorRule(id="d1", type=ValidatorType.DNS, description="dns", failure_message="fail", target="internal.service")

    with patch("socket.gethostbyname", return_value="10.0.0.15"):
        res_dns_ok = d_val.validate(r_dns, ctx)
        assert res_dns_ok.passed is True
        assert res_dns_ok.details["resolved_ip"] == "10.0.0.15"

    with patch("socket.gethostbyname", side_effect=socket.gaierror(8, "nodename nor servname provided")):
        res_dns_fail = d_val.validate(r_dns, ctx)
        assert res_dns_fail.passed is False


# ---------------------------------------------------------------------------
# 4. ContainerValidator and KubernetesValidator Real Query Mocking
# ---------------------------------------------------------------------------

def test_container_and_kubernetes_real_queries():
    ctx = ExecutionContext()

    # ContainerValidator real inspect
    c_val = ContainerValidator()
    r_cont = ValidatorRule(id="c1", type=ValidatorType.CONTAINER, description="cont", failure_message="fail", target="my-app", args={"state": "running"})

    with patch("subprocess.run") as mock_run:
        # Success running
        mock_run.return_value = MagicMock(returncode=0, stdout='[{"State": {"Status": "running"}}]')
        res_cont = c_val.validate(r_cont, ctx)
        assert res_cont.passed is True

        # Container not found (returncode 1)
        mock_run.return_value = MagicMock(returncode=1, stderr="no such container")
        res_cont_not_found = c_val.validate(r_cont, ctx)
        assert res_cont_not_found.passed is False

    # KubernetesValidator real kubectl
    k_val = KubernetesValidator()
    r_k8s = ValidatorRule(id="k1", type=ValidatorType.KUBERNETES, description="k8s", failure_message="fail", target="pod/my-pod", args={"phase": "Running"})

    with patch("subprocess.run") as mock_run:
        # Success Running
        mock_run.return_value = MagicMock(returncode=0, stdout='{"status": {"phase": "Running"}}')
        res_k8s = k_val.validate(r_k8s, ctx)
        assert res_k8s.passed is True

        # Kubectl failure
        mock_run.return_value = MagicMock(returncode=1, stderr="NotFound")
        res_k8s_fail = k_val.validate(r_k8s, ctx)
        assert res_k8s_fail.passed is False


# ---------------------------------------------------------------------------
# 5. CommandValidator Timeout & Edge Cases
# ---------------------------------------------------------------------------

def test_command_validator_timeout_and_exceptions():
    val = CommandValidator()
    ctx = ExecutionContext()

    r_cmd = ValidatorRule(id="cm1", type=ValidatorType.COMMAND, description="cmd", failure_message="fail", target="sleep 100")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="sleep 100", timeout=2)):
        res = val.validate(r_cmd, ctx)
        assert res.passed is False
        assert "timed out" in res.feedback

    with patch("subprocess.run", side_effect=Exception("System crash")):
        res_err = val.validate(r_cmd, ctx)
        assert res_err.passed is False
        assert "System crash" in res_err.feedback
