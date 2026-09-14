"""
Unit tests for KubeLabs State-Based Validators.
"""

import os
import tempfile
from pathlib import Path
import pytest

from packages.lab_schema import (
    ValidatorRule,
    ValidatorType,
    ValidationResultItem,
    ValidationOverallStatus,
)
from packages.validator_core import (
    ValidatorEngine,
    ExecutionContext,
    CommandValidator,
    FileValidator,
    YamlValidator,
    JsonValidator,
    HttpValidator,
    TcpValidator,
    DnsValidator,
    KubernetesValidator,
    GitValidator,
    PrometheusValidator,
    OpenTelemetryValidator,
)


def test_command_validator_success():
    validator = CommandValidator()
    rule = ValidatorRule(
        id="test-cmd",
        type=ValidatorType.COMMAND,
        description="Check echo command",
        target="echo hello",
        weight=10,
        failure_message="Echo failed",
        args={"expected_exit_code": 0, "output_contains": "hello"},
    )
    context = ExecutionContext()
    result = validator.validate(rule, context)
    assert result.passed is True
    assert result.score_awarded == 10


def test_command_validator_failure():
    validator = CommandValidator()
    rule = ValidatorRule(
        id="test-cmd-fail",
        type=ValidatorType.COMMAND,
        description="Check failing exit code",
        target="exit 1",
        weight=10,
        failure_message="Command failed as expected",
        args={"expected_exit_code": 0},
    )
    context = ExecutionContext()
    result = validator.validate(rule, context)
    assert result.passed is False
    assert result.score_awarded == 0


def test_file_validator_success():
    validator = FileValidator()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write("production configuration line")
        tmp_path = tmp.name

    try:
        rule = ValidatorRule(
            id="test-file",
            type=ValidatorType.FILE,
            description="Check file exists and has content",
            target=tmp_path,
            weight=15,
            failure_message="File check failed",
            args={"content_contains": "production"},
        )
        context = ExecutionContext()
        result = validator.validate(rule, context)
        assert result.passed is True
        assert result.score_awarded == 15
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_file_validator_missing():
    validator = FileValidator()
    rule = ValidatorRule(
        id="test-file-missing",
        type=ValidatorType.FILE,
        description="Check non-existent file",
        target="/tmp/nonexistent_file_998877.txt",
        weight=10,
        failure_message="File not found",
    )
    context = ExecutionContext()
    result = validator.validate(rule, context)
    assert result.passed is False


def test_yaml_validator_nested_assertion():
    validator = YamlValidator()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as tmp:
        tmp.write("""
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: web
        resources:
          limits:
            memory: 512Mi
""")
        tmp_path = tmp.name

    try:
        rule = ValidatorRule(
            id="test-yaml",
            type=ValidatorType.YAML,
            description="Check memory limit in YAML",
            target=tmp_path,
            weight=20,
            failure_message="YAML check failed",
            args={
                "assertions": {
                    "spec.replicas": 3,
                    "spec.template.spec.containers.0.resources.limits.memory": "512Mi",
                }
            },
        )
        context = ExecutionContext()
        result = validator.validate(rule, context)
        assert result.passed is True
        assert result.score_awarded == 20
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_json_validator():
    validator = JsonValidator()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
        tmp.write('{"status": "ok", "count": 42}')
        tmp_path = tmp.name

    try:
        rule = ValidatorRule(
            id="test-json",
            type=ValidatorType.JSON,
            description="Check json keys",
            target=tmp_path,
            weight=10,
            failure_message="JSON check failed",
            args={"assertions": {"status": "ok", "count": 42}},
        )
        context = ExecutionContext()
        result = validator.validate(rule, context)
        assert result.passed is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_validator_engine_scoring():
    engine = ValidatorEngine()
    rule1 = ValidatorRule(
        id="r1",
        type=ValidatorType.COMMAND,
        description="Check true",
        target='python -c "exit(0)"',
        weight=50,
        failure_message="Failed",
    )
    rule2 = ValidatorRule(
        id="r2",
        type=ValidatorType.COMMAND,
        description="Check false",
        target='python -c "exit(1)"',
        weight=50,
        failure_message="Failed",
    )
    context = ExecutionContext()
    report = engine.validate_rules([rule1, rule2], context)
    assert report.overall_status == ValidationOverallStatus.PARTIAL
    assert report.total_score == 50
    assert report.max_possible_score == 100
    assert report.percentage == 50.0
