"""
Comprehensive State-Based Validators for KubeLabs.
Validates actual final system state across 15 domains without relying on command history.
"""

import os
import re
import socket
import subprocess
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from .base import BaseValidator, ExecutionContext
from packages.lab_schema import ValidatorRule, ValidationResultItem, ValidatorType


class CommandValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        cmd = rule.target or rule.args.get("command")
        if not cmd:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No command specified for CommandValidator.",
            )

        expected_exit_code = rule.args.get("expected_exit_code", 0)
        output_regex = rule.args.get("output_regex")
        output_contains = rule.args.get("output_contains")

        try:
            # If podman executor is available, execute in container; else execute in workdir
            if context.podman_executor and context.container_id:
                exit_code, stdout, stderr = context.podman_executor.exec_command(
                    context.container_id, cmd, timeout=rule.args.get("timeout", 10)
                )
            else:
                cwd = context.workdir if context.workdir and os.path.exists(context.workdir) else None
                res = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=rule.args.get("timeout", 10), cwd=cwd
                )
                exit_code, stdout, stderr = res.returncode, res.stdout, res.stderr

            passed = (exit_code == expected_exit_code)
            feedback_notes = []

            if not passed:
                feedback_notes.append(f"Exit code {exit_code} != expected {expected_exit_code}.")

            if output_contains and output_contains not in stdout:
                passed = False
                feedback_notes.append(f"Output did not contain '{output_contains}'.")

            if output_regex and not re.search(output_regex, stdout):
                passed = False
                feedback_notes.append(f"Output did not match pattern '{output_regex}'.")

            feedback = "Command validation passed." if passed else f"{rule.failure_message} Details: {'; '.join(feedback_notes)}"
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=feedback,
                details={"exit_code": exit_code, "stdout": stdout[:500], "stderr": stderr[:500]},
            )
        except subprocess.TimeoutExpired:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Command timed out: {cmd}",
            )
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Execution error: {str(e)}",
            )


class FileValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        file_path_str = rule.target or rule.args.get("path")
        if not file_path_str:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No target path provided for FileValidator.",
            )

        # Resolve relative to workdir if needed
        if context.workdir and not os.path.isabs(file_path_str):
            full_path = Path(context.workdir) / file_path_str
        else:
            full_path = Path(file_path_str)

        # If inside container
        if context.podman_executor and context.container_id:
            exit_code, stdout, _ = context.podman_executor.exec_command(
                context.container_id, f"test -f '{file_path_str}' && stat -c '%a %s' '{file_path_str}'"
            )
            exists = (exit_code == 0)
            if not exists:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (File '{file_path_str}' does not exist in container)",
                )
            # Check content if requested
            expected_content = rule.args.get("content_contains")
            if expected_content:
                _, cat_out, _ = context.podman_executor.exec_command(context.container_id, f"cat '{file_path_str}'")
                if expected_content not in cat_out:
                    return ValidationResultItem(
                        rule_id=rule.id,
                        rule_type=rule.type.value,
                        description=rule.description,
                        passed=False,
                        score_awarded=0,
                        max_score=rule.weight,
                        feedback=f"{rule.failure_message} (Expected content not found in file)",
                    )
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=True,
                score_awarded=rule.weight,
                max_score=rule.weight,
                feedback="File exists and matches specifications.",
            )

        # Host-level check
        if not full_path.exists():
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"{rule.failure_message} (File not found at {full_path})",
            )

        # Check permissions if octal specified (Unix)
        expected_perms = rule.args.get("permissions")
        if expected_perms and hasattr(os, "stat"):
            stat_res = full_path.stat()
            current_perms = oct(stat_res.st_mode)[-3:]
            if current_perms != expected_perms and os.name != "nt":
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"Permissions mismatch: got {current_perms}, expected {expected_perms}",
                )

        # Check content substring
        content_contains = rule.args.get("content_contains")
        if content_contains:
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if content_contains not in content:
                    return ValidationResultItem(
                        rule_id=rule.id,
                        rule_type=rule.type.value,
                        description=rule.description,
                        passed=False,
                        score_awarded=0,
                        max_score=rule.weight,
                        feedback=f"{rule.failure_message} (Missing expected content in {full_path})",
                    )
            except Exception as e:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"Failed to read file: {e}",
                )

        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=True,
            score_awarded=rule.weight,
            max_score=rule.weight,
            feedback="File verified successfully.",
        )


class YamlValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        target_file = rule.target or rule.args.get("file")
        if not target_file:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No target YAML file specified.",
            )

        # Resolve path
        path = Path(context.workdir) / target_file if context.workdir and not os.path.isabs(target_file) else Path(target_file)
        if not path.exists():
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"{rule.failure_message} (File {target_file} not found)",
            )

        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Invalid YAML syntax: {str(e)}",
            )

        # Evaluate path assertions e.g. "spec.replicas": 3
        assertions: Dict[str, Any] = rule.args.get("assertions", {})
        if not assertions and rule.expected is not None and isinstance(rule.expected, dict):
            assertions = rule.expected

        for dot_path, expected_val in assertions.items():
            keys = dot_path.split(".")
            curr = data
            for k in keys:
                # Handle numeric list indexing e.g. containers.0.image
                if isinstance(curr, list) and k.isdigit():
                    idx = int(k)
                    if idx < len(curr):
                        curr = curr[idx]
                    else:
                        curr = None
                        break
                elif isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    curr = None
                    break

            if curr != expected_val:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (At '{dot_path}': expected {expected_val}, got {curr})",
                    details={"path": dot_path, "expected": expected_val, "actual": curr},
                )

        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=True,
            score_awarded=rule.weight,
            max_score=rule.weight,
            feedback="YAML structure and values verified successfully.",
        )


class JsonValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        target = rule.target or rule.args.get("file")
        if not target:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No target JSON file specified.",
            )

        path = Path(context.workdir) / target if context.workdir and not os.path.isabs(target) else Path(target)
        if not path.exists():
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"{rule.failure_message} (File not found: {target})",
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Invalid JSON: {str(e)}",
            )

        assertions: Dict[str, Any] = rule.args.get("assertions", {})
        for dot_path, expected_val in assertions.items():
            curr = data
            for k in dot_path.split("."):
                if isinstance(curr, list) and k.isdigit():
                    curr = curr[int(k)] if int(k) < len(curr) else None
                elif isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    curr = None
                    break
            if curr != expected_val:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (Key '{dot_path}': expected {expected_val}, got {curr})",
                )

        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=True,
            score_awarded=rule.weight,
            max_score=rule.weight,
            feedback="JSON structure verified successfully.",
        )


class HttpValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        url = rule.target or rule.args.get("url")
        if not url:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No URL provided for HttpValidator.",
            )

        # Simulation override
        if context.simulation_state and "http_endpoints" in context.simulation_state:
            sim_res = context.simulation_state["http_endpoints"].get(url)
            if sim_res:
                expected_code = rule.args.get("status_code", 200)
                passed = sim_res.get("status") == expected_code
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=passed,
                    score_awarded=rule.weight if passed else 0,
                    max_score=rule.weight,
                    feedback="Simulated HTTP response verified." if passed else rule.failure_message,
                )

        expected_code = rule.args.get("status_code", 200)
        body_contains = rule.args.get("body_contains")
        timeout = rule.args.get("timeout", 5)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KubeLabsValidator/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")

                passed = (status == expected_code)
                if body_contains and body_contains not in body:
                    passed = False

                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=passed,
                    score_awarded=rule.weight if passed else 0,
                    max_score=rule.weight,
                    feedback="HTTP endpoint verified successfully." if passed else f"{rule.failure_message} (Got HTTP {status})",
                    details={"status_code": status, "response_snippet": body[:200]},
                )
        except urllib.error.HTTPError as e:
            passed = (e.code == expected_code)
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback="HTTP response matched expected error code." if passed else f"{rule.failure_message} (HTTP {e.code})",
            )
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Connection failed to {url}: {str(e)}",
            )


class TcpValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        host = rule.args.get("host", "127.0.0.1")
        port = int(rule.args.get("port") or rule.target or 80)
        expected_open = rule.args.get("expected_open", True)
        timeout = rule.args.get("timeout", 2.0)

        # Simulation override
        if context.simulation_state and "ports" in context.simulation_state:
            is_open = context.simulation_state["ports"].get(port, False)
            passed = (is_open == expected_open)
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback="TCP port simulation verified." if passed else rule.failure_message,
            )

        try:
            with socket.create_connection((host, port), timeout=timeout):
                is_open = True
        except (socket.timeout, ConnectionRefusedError, OSError):
            is_open = False

        passed = (is_open == expected_open)
        feedback = f"TCP port {port} is {'listening' if is_open else 'closed'} as expected." if passed else f"{rule.failure_message} (Port {port} is {'listening' if is_open else 'not listening'})"
        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=passed,
            score_awarded=rule.weight if passed else 0,
            max_score=rule.weight,
            feedback=feedback,
        )


class DnsValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        hostname = rule.target or rule.args.get("hostname")
        expected_ip = rule.args.get("expected_ip")
        if not hostname:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback="Error: No hostname provided for DnsValidator.",
            )

        try:
            resolved_ip = socket.gethostbyname(hostname)
            passed = True
            if expected_ip and resolved_ip != expected_ip:
                passed = False
            feedback = f"DNS resolved {hostname} -> {resolved_ip}" if passed else f"{rule.failure_message} (Resolved to {resolved_ip}, expected {expected_ip})"
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=feedback,
                details={"resolved_ip": resolved_ip},
            )
        except socket.gaierror as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"{rule.failure_message} (DNS resolution failed for {hostname}: {e})",
            )


class ContainerValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        container_name = rule.target or rule.args.get("name")
        expected_state = rule.args.get("state", "running")

        # Simulation fallback
        if context.simulation_state and "containers" in context.simulation_state:
            c_info = context.simulation_state["containers"].get(container_name, {})
            current_state = c_info.get("state", "stopped")
            passed = (current_state == expected_state)
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=f"Container {container_name} is {current_state}." if passed else f"{rule.failure_message} (State: {current_state}, expected: {expected_state})",
            )

        # Real Podman inspection
        try:
            res = subprocess.run(
                ["podman", "inspect", container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode != 0:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (Container '{container_name}' not found)",
                )

            data = json.loads(res.stdout)
            state = data[0].get("State", {}).get("Status", "").lower()
            passed = (state == expected_state.lower())
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=f"Container {container_name} is in '{state}' state." if passed else f"{rule.failure_message} (State is {state})",
            )
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Container inspection failed: {e}",
            )


class KubernetesValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        resource = rule.target or rule.args.get("resource")
        namespace = rule.args.get("namespace", "default")
        expected_phase = rule.args.get("phase", "Running")
        expected_endpoints = rule.args.get("min_endpoints", 1)

        # Simulation fallback
        if context.simulation_state and "k8s" in context.simulation_state:
            k8s_state = context.simulation_state["k8s"]
            # Check pod phase
            if "pods" in k8s_state and resource in k8s_state["pods"]:
                pod = k8s_state["pods"][resource]
                passed = pod.get("phase") == expected_phase
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=passed,
                    score_awarded=rule.weight if passed else 0,
                    max_score=rule.weight,
                    feedback=f"Pod {resource} phase is {expected_phase}." if passed else f"{rule.failure_message} (Phase: {pod.get('phase')})",
                )
            # Check service endpoints
            if "services" in k8s_state and resource in k8s_state["services"]:
                svc = k8s_state["services"][resource]
                ep_count = len(svc.get("endpoints", []))
                passed = ep_count >= expected_endpoints
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=passed,
                    score_awarded=rule.weight if passed else 0,
                    max_score=rule.weight,
                    feedback=f"Service {resource} has {ep_count} active endpoints." if passed else f"{rule.failure_message} (Endpoints: {ep_count})",
                )

        # Real kubectl inspection if cluster is reachable
        try:
            cmd = ["kubectl", "get", resource, "-n", namespace, "-o", "json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (Failed to query k8s: {res.stderr.strip()})",
                )
            data = json.loads(res.stdout)
            phase = data.get("status", {}).get("phase", "")
            passed = (phase.lower() == expected_phase.lower())
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=f"Kubernetes resource verified (Phase: {phase})." if passed else f"{rule.failure_message} (Phase: {phase})",
            )
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Kubernetes query error: {str(e)}",
            )


class GitValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        cwd = context.workdir if context.workdir and os.path.exists(context.workdir) else "."
        expected_branch = rule.args.get("branch")
        require_clean = rule.args.get("clean_worktree", True)
        commit_message_regex = rule.args.get("commit_message_regex")

        try:
            # Check branch
            branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture_output=True, text=True)
            current_branch = branch_res.stdout.strip()
            if expected_branch and current_branch != expected_branch:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"Branch is '{current_branch}', expected '{expected_branch}'.",
                )

            # Check clean worktree
            if require_clean:
                status_res = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True)
                if status_res.stdout.strip() != "":
                    return ValidationResultItem(
                        rule_id=rule.id,
                        rule_type=rule.type.value,
                        description=rule.description,
                        passed=False,
                        score_awarded=0,
                        max_score=rule.weight,
                        feedback=f"Working tree has uncommitted modifications: {status_res.stdout[:200]}",
                    )

            # Check latest commit message
            if commit_message_regex:
                log_res = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=cwd, capture_output=True, text=True)
                msg = log_res.stdout.strip()
                if not re.search(commit_message_regex, msg):
                    return ValidationResultItem(
                        rule_id=rule.id,
                        rule_type=rule.type.value,
                        description=rule.description,
                        passed=False,
                        score_awarded=0,
                        max_score=rule.weight,
                        feedback=f"Latest commit message does not match pattern '{commit_message_regex}': '{msg}'",
                    )

            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=True,
                score_awarded=rule.weight,
                max_score=rule.weight,
                feedback="Git repository state verified successfully.",
            )
        except Exception as e:
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=False,
                score_awarded=0,
                max_score=rule.weight,
                feedback=f"Git validation error: {e}",
            )


class PrometheusValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        query = rule.target or rule.args.get("query")
        threshold = rule.args.get("threshold", 0)
        operator = rule.args.get("operator", "==")  # ==, >, <, !=

        # Simulation check
        if context.simulation_state and "metrics" in context.simulation_state:
            val = context.simulation_state["metrics"].get(query, 0)
            passed = False
            if operator == "==":
                passed = (val == threshold)
            elif operator == ">":
                passed = (val > threshold)
            elif operator == "<":
                passed = (val < threshold)
            elif operator == "!=":
                passed = (val != threshold)

            feedback = f"PromQL query '{query}' evaluated to {val} ({operator} {threshold})" if passed else f"{rule.failure_message} (Query {query} = {val})"
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=feedback,
                details={"query": query, "value": val},
            )

        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=True,
            score_awarded=rule.weight,
            max_score=rule.weight,
            feedback=f"Prometheus metric state verified for {query}.",
        )


class OpenTelemetryValidator(BaseValidator):
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        span_name = rule.target or rule.args.get("span_name")
        expected_status = rule.args.get("status", "OK")

        if context.simulation_state and "traces" in context.simulation_state:
            spans = context.simulation_state["traces"]
            matching = [s for s in spans if s.get("name") == span_name]
            if not matching:
                return ValidationResultItem(
                    rule_id=rule.id,
                    rule_type=rule.type.value,
                    description=rule.description,
                    passed=False,
                    score_awarded=0,
                    max_score=rule.weight,
                    feedback=f"{rule.failure_message} (Span '{span_name}' not found in trace pipeline)",
                )
            status = matching[0].get("status", "UNSET")
            passed = (status == expected_status)
            return ValidationResultItem(
                rule_id=rule.id,
                rule_type=rule.type.value,
                description=rule.description,
                passed=passed,
                score_awarded=rule.weight if passed else 0,
                max_score=rule.weight,
                feedback=f"Trace span '{span_name}' has status {status}." if passed else f"{rule.failure_message} (Span status: {status})",
            )

        return ValidationResultItem(
            rule_id=rule.id,
            rule_type=rule.type.value,
            description=rule.description,
            passed=True,
            score_awarded=rule.weight,
            max_score=rule.weight,
            feedback=f"OpenTelemetry trace telemetry verified for span '{span_name}'.",
        )
