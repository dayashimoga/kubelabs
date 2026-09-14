"""
KubeLabs Declarative Lab Schema Definitions.
Strict Pydantic models for parsing, validating, and executing labs,
incident simulations, validators, and step-by-step troubleshooting tasks.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PRODUCTION = "production"


class ValidationStatus(str, Enum):
    PROVEN = "PROVEN"
    SIMULATION_PROVEN = "SIMULATION-PROVEN"
    IMPLEMENTED_UNPROVEN = "IMPLEMENTED-UNPROVEN"
    HARDWARE_CLOUD_REQUIRED = "HARDWARE/CLOUD-REQUIRED"


class LabRuntimeClassification(str, Enum):
    REAL = "REAL"
    EMULATED = "EMULATED"
    SIMULATED = "SIMULATED"
    CLOUD_REQUIRED = "CLOUD-REQUIRED"


class EnvironmentType(str, Enum):
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    SIMULATION = "simulation"
    HYBRID = "hybrid"


class HintTier(int, Enum):
    CONCEPTUAL = 1
    AREA = 2
    COMMAND = 3
    STRONG_CLUE = 4
    FULL_SOLUTION = 5


class Hint(BaseModel):
    tier: HintTier = Field(..., description="Hint depth tier from 1 (conceptual) to 5 (full solution)")
    title: str = Field(..., description="Short summary title of the hint")
    content: str = Field(..., description="Markdown or text content of the hint")
    penalty_points: int = Field(default=5, description="Score penalty deducted if revealed")


class ValidatorType(str, Enum):
    COMMAND = "command"
    FILE = "file"
    REGEX = "regex"
    YAML = "yaml"
    JSON = "json"
    HTTP = "http"
    TCP = "tcp"
    DNS = "dns"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    GIT = "git"
    PROMETHEUS = "prometheus"
    OPENTELEMETRY = "opentelemetry"


class ValidatorRule(BaseModel):
    id: str = Field(..., description="Unique validator rule identifier")
    type: ValidatorType = Field(..., description="Validator engine type")
    description: str = Field(..., description="What this validator checks")
    target: Optional[str] = Field(None, description="File path, URL, command, metric, or k8s resource")
    expected: Optional[Any] = Field(None, description="Expected value, regex, status code, or JSON structure")
    args: Dict[str, Any] = Field(default_factory=dict, description="Validator-specific parameters")
    weight: int = Field(default=10, description="Points awarded for passing this validation rule")
    failure_message: str = Field(..., description="Feedback shown if the rule fails")


class TopologyNode(BaseModel):
    id: str
    label: str
    type: str  # service, database, gateway, queue, pod, node, alb, etc.
    status: str = "healthy"  # healthy, degraded, failed, unknown
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TopologyEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None
    protocol: Optional[str] = "http"
    status: str = "normal"  # normal, slow, broken, dropped


class TopologySpec(BaseModel):
    nodes: List[TopologyNode] = Field(default_factory=list)
    edges: List[TopologyEdge] = Field(default_factory=list)


class ContainerNodeSpec(BaseModel):
    name: str
    image: str = "docker.io/library/alpine:latest"
    ports: List[str] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    command: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)


class MultiContainerSpec(BaseModel):
    network_name: str = "kubelabs-net"
    pod_name: Optional[str] = None
    containers: List[ContainerNodeSpec] = Field(default_factory=list)


class EnvironmentSpec(BaseModel):
    type: EnvironmentType = Field(default=EnvironmentType.CONTAINER)
    image: str = Field(default="docker.io/library/alpine:latest")
    cpu_limit: str = Field(default="1.0")
    memory_limit: str = Field(default="512Mi")
    pids_limit: int = Field(default=100)
    capabilities_drop: List[str] = Field(default_factory=lambda: ["ALL"])
    capabilities_add: List[str] = Field(default_factory=lambda: ["NET_BIND_SERVICE"])
    read_only_root: bool = Field(default=False)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    port_mappings: List[str] = Field(default_factory=list)
    mount_paths: List[str] = Field(default_factory=list)
    isolated_network: bool = Field(default=True)
    multi_container: Optional[MultiContainerSpec] = None


class StagedFile(BaseModel):
    path: str
    content: str
    permissions: str = "0644"


class InitialStateSpec(BaseModel):
    files: List[StagedFile] = Field(default_factory=list)
    setup_commands: List[str] = Field(default_factory=list)
    failure_injection_commands: List[str] = Field(default_factory=list)
    seed_data: Dict[str, Any] = Field(default_factory=dict)


class TaskSpec(BaseModel):
    id: str
    order: int
    title: str
    description: str
    diagnostic_questions: List[str] = Field(
        default_factory=lambda: [
            "What should I inspect next?",
            "Why did this fail?",
            "Which command should I run?",
            "Explain this output",
            "Show another possible root cause",
            "Show the correct solution",
        ]
    )
    hints: List[Hint] = Field(default_factory=list)
    validators: List[ValidatorRule] = Field(default_factory=list)


class CleanupPolicy(BaseModel):
    ttl_seconds: int = Field(default=1800, description="Auto cleanup timeout in seconds (30m)")
    delete_containers: bool = True
    delete_volumes: bool = True
    delete_networks: bool = True


class ScoringSpec(BaseModel):
    max_score: int = 100
    detection_weight: int = 15
    investigation_weight: int = 25
    root_cause_weight: int = 20
    fix_weight: int = 25
    verification_weight: int = 15


class LabSpec(BaseModel):
    id: str = Field(..., description="Unique slug ID (e.g. linux-inode-exhaustion)")
    version: str = Field(default="1.0.0")
    title: str = Field(..., description="Human readable lab title")
    track: str = Field(..., description="Core track (e.g. linux, kubernetes, docker, sre-incidents)")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    estimated_minutes: int = Field(default=30)
    validation_status: ValidationStatus = Field(default=ValidationStatus.PROVEN)
    runtime_classification: LabRuntimeClassification = Field(default=LabRuntimeClassification.REAL)
    pedagogical_steps: List[str] = Field(
        default_factory=lambda: [
            "Learn", "Practice", "Break", "Troubleshoot", "Fix", "Validate", "Explain", "Assess", "Master"
        ]
    )

    objectives: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    expected_learning_outcomes: List[str] = Field(default_factory=list)

    what_why: str = Field(default="", description="What it is and Why it matters")
    architecture_overview: str = Field(default="", description="Architecture and system components")
    internals_deep_dive: str = Field(default="", description="Kernel/system internals explanation")
    common_errors: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    troubleshooting_workflow: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    production_design_notes: str = Field(default="")
    security_considerations: str = Field(default="")
    performance_tips: str = Field(default="")
    interview_scenarios: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)

    topology: Optional[TopologySpec] = None
    environment: EnvironmentSpec = Field(default_factory=EnvironmentSpec)
    initial_state: InitialStateSpec = Field(default_factory=InitialStateSpec)
    tasks: List[TaskSpec] = Field(default_factory=list)
    cleanup_policy: CleanupPolicy = Field(default_factory=CleanupPolicy)
    scoring: ScoringSpec = Field(default_factory=ScoringSpec)


class ValidationResultItem(BaseModel):
    rule_id: str
    rule_type: str
    description: str
    passed: bool
    score_awarded: int
    max_score: int
    feedback: str
    details: Optional[Dict[str, Any]] = None


class ValidationOverallStatus(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"


class ValidationReport(BaseModel):
    overall_status: ValidationOverallStatus
    total_score: int
    max_possible_score: int
    percentage: float
    items: List[ValidationResultItem] = Field(default_factory=list)
    summary: str
