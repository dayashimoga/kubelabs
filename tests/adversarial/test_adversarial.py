"""
Adversarial and Edge Case Tests for KubeLabs.
Tests malformed input, infinite loops, resource bombs, and path traversal defenses.
"""

import pytest
from pydantic import ValidationError
from packages.lab_schema import LabSpec, ValidatorRule, ValidatorType
from packages.validator_core import CommandValidator, ExecutionContext, FileValidator


def test_malformed_lab_spec_rejected():
    # Missing required id and title
    with pytest.raises(ValidationError):
        LabSpec.model_validate({"track": "linux"})


def test_command_timeout_defense():
    validator = CommandValidator()
    # Run a sleep 10 command with a 1 second timeout
    rule = ValidatorRule(
        id="timeout-test",
        type=ValidatorType.COMMAND,
        description="Test timeout defense",
        target="python -c \"import time; time.sleep(5)\"",
        weight=10,
        failure_message="Command failed",
        args={"timeout": 1},
    )
    context = ExecutionContext()
    result = validator.validate(rule, context)
    assert result.passed is False
    assert "timed out" in result.feedback.lower()


def test_path_traversal_non_existent_file():
    validator = FileValidator()
    rule = ValidatorRule(
        id="traversal-test",
        type=ValidatorType.FILE,
        description="Test directory traversal",
        target="../../../../etc/shadow_does_not_exist",
        weight=10,
        failure_message="File not found",
    )
    context = ExecutionContext()
    result = validator.validate(rule, context)
    assert result.passed is False


def test_invalid_yaml_syntax_handled_gracefully():
    from packages.validator_core import YamlValidator
    import tempfile
    import os

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml") as tmp:
        tmp.write("invalid: yaml: : : syntax")
        tmp_path = tmp.name

    try:
        validator = YamlValidator()
        rule = ValidatorRule(
            id="bad-yaml",
            type=ValidatorType.YAML,
            description="Test bad yaml",
            target=tmp_path,
            weight=10,
            failure_message="YAML check failed",
        )
        context = ExecutionContext()
        result = validator.validate(rule, context)
        assert result.passed is False
        assert "invalid yaml" in result.feedback.lower()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
