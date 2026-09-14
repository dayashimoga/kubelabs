"""
Deep coverage expansion tests targeting SandboxRuntime, KubernetesProvider,
DeterministicSimulator, ValidatorEngine, and API Service layers.
"""

import pytest
from packages.lab_schema import (
    LabSpec,
    DifficultyLevel,
    ValidationStatus,
    ValidationOverallStatus,
    LabRuntimeClassification,
    EnvironmentSpec,
    EnvironmentType,
    ScenarioFactory,
    ValidatorRule,
    ValidatorType,
    TaskSpec,
    Hint,
    HintTier,
)
from packages.validator_core import ValidatorEngine, ExecutionContext
from packages.sandbox_runtime import (
    DeterministicSimulator,
    EnvironmentBroker,
    KubernetesProvider,
)
from apps.api.src.services.lab_service import LabService
from apps.api.src.services.troubleshooting_service import TroubleshootingAdvisor
from apps.api.src.services.assessment_service import AssessmentService, QUESTIONS
from apps.api.src.core.config import settings


def test_simulator_comprehensive_commands():
    sim = DeterministicSimulator("k8s-pod-crashloop-backoff")

    # AWS EKS cluster inspection
    code, out, _ = sim.execute_command("aws eks describe-cluster --name prod-useast1-core")
    assert code == 0
    assert "prod-useast1-core" in out

    # Kubernetes get services
    sim.state["k8s"]["services"]["frontend-svc"] = {
        "type": "ClusterIP",
        "cluster_ip": "10.96.0.15",
        "ports": "80/TCP",
        "endpoints": ["10.244.1.22:80"],
    }
    code_s, out_s, _ = sim.execute_command("kubectl get services")
    assert code_s == 0
    assert "frontend-svc" in out_s

    # Kubernetes get endpoints
    code_e, out_e, _ = sim.execute_command("kubectl get endpoints")
    assert code_e == 0
    assert "frontend-svc" in out_e

    # Kubernetes describe pod
    sim.state["k8s"]["pods"]["auth-service-pod"] = {
        "status": "CrashLoopBackOff",
        "events": ["Back-off restarting failed container"],
    }
    code_d, out_d, _ = sim.execute_command("kubectl describe pod auth-service-pod")
    assert code_d == 0
    assert "auth-service-pod" in out_d


def test_validator_engine_comprehensive():
    engine = ValidatorEngine()
    ctx = ExecutionContext()

    # Empty rules
    rep_empty = engine.validate_rules([], ctx)
    assert len(rep_empty.items) == 0
    assert rep_empty.overall_status == ValidationOverallStatus.PASS
    assert rep_empty.total_score == 100

    # Passing & failing rules
    r_pass = ValidatorRule(
        id="v1", type=ValidatorType.COMMAND, description="pass", failure_message="fail", target="echo 1", args={"expected_exit_code": 0}
    )
    r_fail = ValidatorRule(
        id="v2", type=ValidatorType.COMMAND, description="fail", failure_message="fail", target="exit 1", args={"expected_exit_code": 0}
    )

    rep = engine.validate_rules([r_pass, r_fail], ctx)
    passed_items = [i for i in rep.items if i.passed]
    failed_items = [i for i in rep.items if not i.passed]
    assert len(passed_items) == 1
    assert len(failed_items) == 1
    assert rep.total_score == r_pass.weight

    # Validate task
    task = TaskSpec(id="t1", order=1, title="Task 1", description="desc", validators=[r_pass])
    task_rep = engine.validate_rules(task.validators, ctx)
    assert len([i for i in task_rep.items if i.passed]) == 1


def test_troubleshooting_advisor_full_api():
    advisor = TroubleshootingAdvisor()
    task = TaskSpec(
        id="t1",
        order=1,
        title="Resolve Failure",
        description="Fix app",
        hints=[
            Hint(tier=HintTier.CONCEPTUAL, title="Concept", content="Memory saturation"),
            Hint(tier=HintTier.AREA, title="Area", content="Check /var/log/syslog"),
            Hint(tier=HintTier.COMMAND, title="Command", content="dmesg -T"),
        ],
    )
    lab = ScenarioFactory.get_all_scenarios()[0]

    # Get specific hint tier
    h1 = advisor.get_hint_for_tier(task, 1)
    assert h1 is not None
    assert h1.content == "Memory saturation"

    # Answer diagnostic question
    ans1 = advisor.answer_diagnostic_question(lab, task, "What should I inspect next?")
    assert "Inspection Target" in ans1["category"]
    assert "Check /var/log/syslog" in ans1["guidance"]

    ans2 = advisor.answer_diagnostic_question(lab, task, "Why did this fail?")
    assert "Failure Mechanics" in ans2["category"]
    assert "Memory saturation" in ans2["guidance"]


def test_assessment_service_full_api():
    svc = AssessmentService()

    # Get questions for track
    k8s_qs = svc.get_questions_for_track("kubernetes")
    assert len(k8s_qs) > 0
    # Answers should be hidden from client
    assert "correct_answer" not in k8s_qs[0]

    # Grade submission
    q_target = [q for q in QUESTIONS if q.track == "kubernetes"][0]
    answers = {q_target.id: q_target.correct_answer}
    result = svc.grade_submission("kubernetes", answers)
    assert result["score"] >= 1
    assert result["percentage"] > 0


def test_lab_service_session_lifecycle():
    svc = LabService(settings.LABS_DIR)

    # List tracks and labs
    tracks = svc.get_tracks()
    assert len(tracks) > 0
    labs = svc.list_labs()
    assert len(labs) > 0

    # Start session
    lab_id = labs[0].id
    session_data = svc.start_lab_session(lab_id, force_simulation=True)
    assert session_data is not None
    session_id = session_data["session_id"]
    assert session_id in svc.sandbox_manager.sessions

    # Execute command
    res = svc.execute_command(session_id, "uptime")
    assert res is not None

    # Validate task
    first_task_id = labs[0].tasks[0].id if labs[0].tasks else "t1"
    val_res = svc.validate_task(session_id, first_task_id)
    assert val_res is not None

    # Cleanup session
    del_res = svc.stop_lab_session(session_id)
    assert del_res is True
