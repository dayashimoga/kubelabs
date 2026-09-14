"""
Validator Engine: Orchestrates rules evaluation, score computation,
and structured feedback generation.
"""

from typing import Dict, List, Optional
from packages.lab_schema import (
    ValidatorRule,
    ValidatorType,
    ValidationResultItem,
    ValidationReport,
    ValidationOverallStatus,
)
from .base import BaseValidator, ExecutionContext
from .validators import (
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


class ValidatorEngine:
    """Registry and execution runner for all state-based validators."""

    def __init__(self):
        self._validators: Dict[ValidatorType, BaseValidator] = {
            ValidatorType.COMMAND: CommandValidator(),
            ValidatorType.FILE: FileValidator(),
            ValidatorType.REGEX: CommandValidator(),  # Regex checks handled by command/file output matching
            ValidatorType.YAML: YamlValidator(),
            ValidatorType.JSON: JsonValidator(),
            ValidatorType.HTTP: HttpValidator(),
            ValidatorType.TCP: TcpValidator(),
            ValidatorType.DNS: DnsValidator(),
            ValidatorType.CONTAINER: ContainerValidator(),
            ValidatorType.KUBERNETES: KubernetesValidator(),
            ValidatorType.GIT: GitValidator(),
            ValidatorType.PROMETHEUS: PrometheusValidator(),
            ValidatorType.OPENTELEMETRY: OpenTelemetryValidator(),
            ValidatorType.TERRAFORM: CommandValidator(),
            ValidatorType.ANSIBLE: CommandValidator(),
        }

    def register(self, validator_type: ValidatorType, validator: BaseValidator):
        self._validators[validator_type] = validator

    def validate_rules(self, rules: List[ValidatorRule], context: ExecutionContext) -> ValidationReport:
        """Run all validator rules against context and produce an overall report."""
        if not rules:
            return ValidationReport(
                overall_status=ValidationOverallStatus.PASS,
                total_score=100,
                max_possible_score=100,
                percentage=100.0,
                items=[],
                summary="No validation rules specified; automatically passing.",
            )

        items: List[ValidationResultItem] = []
        total_score = 0
        max_possible_score = sum(r.weight for r in rules) or 100

        for rule in rules:
            validator = self._validators.get(rule.type)
            if not validator:
                item = ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"Unsupported validator type: {rule.type}",
                )
            else:
                try:
                    item = validator.validate(rule, context)
                except Exception as exc:
                    item = ValidationResultItem(
                        rule_id=rule.id,
                        rule_type=rule.type.value,
                        description=rule.description,
                        passed=False,
                        score_awarded=0,
                        max_score=rule.weight,
                        feedback=f"Validator internal error: {str(exc)}",
                    )

            items.append(item)
            total_score += item.score_awarded

        passed_count = sum(1 for item in items if item.passed)
        percentage = round((total_score / max_possible_score) * 100.0, 1)

        if passed_count == len(items):
            overall_status = ValidationOverallStatus.PASS
            summary = f"All {len(items)} validation rules passed successfully! (Score: {total_score}/{max_possible_score})"
        elif passed_count > 0:
            overall_status = ValidationOverallStatus.PARTIAL
            summary = f"{passed_count} of {len(items)} rules passed. ({total_score}/{max_possible_score} pts)"
        else:
            overall_status = ValidationOverallStatus.FAIL
            summary = f"0 of {len(items)} validation rules passed. Please inspect feedback and retry."

        return ValidationReport(
            overall_status=overall_status,
            total_score=total_score,
            max_possible_score=max_possible_score,
            percentage=percentage,
            items=items,
            summary=summary,
        )
