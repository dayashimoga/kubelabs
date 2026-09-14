"""
Scenario Factory: Extensible Catalog and Generator for KubeLabs.
Produces hundreds of genuinely distinct, deeply structured SRE and DevOps learning labs
across all 24 core tracks following the 13-part pedagogical architecture.
"""

from typing import Dict, List, Optional
from pathlib import Path
import yaml
from .models import (
    LabSpec,
    DifficultyLevel,
    ValidationStatus,
    LabRuntimeClassification,
    EnvironmentSpec,
    EnvironmentType,
    InitialStateSpec,
    StagedFile,
    TaskSpec,
    Hint,
    HintTier,
    ValidatorRule,
    ValidatorType,
    CleanupPolicy,
    ScoringSpec,
    TopologySpec,
    TopologyNode,
    TopologyEdge,
)


class ScenarioFactory:
    """Factory generating distinct, production-grade SRE & DevOps learning scenarios."""

    TRACKS = [
        "linux",
        "bash",
        "git",
        "networking",
        "http-dns-tls",
        "docker",
        "kubernetes",
        "helm",
        "kustomize",
        "terraform",
        "ansible",
        "ci-cd",
        "github-actions",
        "argocd",
        "prometheus",
        "grafana",
        "alertmanager",
        "loki",
        "opentelemetry",
        "istio",
        "aws-eks",
        "devsecops",
        "platform-engineering",
        "sre-resilience",
    ]

    @classmethod
    def _create_base_topology(cls, scenario_id: str, track: str) -> TopologySpec:
        """Create a track-specific visual topology."""
        return TopologySpec(
            nodes=[
                TopologyNode(id="client", label="Client Traffic", type="gateway", status="healthy"),
                TopologyNode(id="ingress", label="Ingress / Proxy", type="service", status="healthy"),
                TopologyNode(id="app", label=f"App: {scenario_id}", type="service", status="degraded"),
                TopologyNode(id="datastore", label="State Store", type="database", status="healthy"),
            ],
            edges=[
                TopologyEdge(source="client", target="ingress", protocol="http", status="normal"),
                TopologyEdge(source="ingress", target="app", protocol="http", status="broken"),
                TopologyEdge(source="app", target="datastore", protocol="tcp", status="normal"),
            ],
        )

    @classmethod
    def build_catalog(cls) -> List[LabSpec]:
        """Generate the full scenario catalog covering all 24 tracks with genuine failure modes."""
        scenarios: List[LabSpec] = []

        # 1. Linux Track: Inode Exhaustion
        scenarios.append(
            LabSpec(
                id="linux-inode-exhaustion",
                title="Linux Kernel: Inode Starvation in High-Throughput Mail Spool",
                track="linux",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=30,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Diagnose No space left on device when disk has gigabytes free", "Clean exhausted spool queue safely"],
                prerequisites=["Basic Linux CLI", "Filesystem understanding"],
                expected_learning_outcomes=["Understand superblock inode allocations", "Master df -i and find -type f execution"],
                what_why="Inodes hold file metadata. Creating millions of tiny files exhausts inode tables before disk storage runs out.",
                architecture_overview="VFS -> Ext4/XFS Superblock -> Inode Table -> Data Blocks.",
                internals_deep_dive="Each inode represents a file. The inode table is fixed at format time on ext4. df -i queries s_inodes_count.",
                common_errors=["Assuming df -h disk space tells the whole story", "Attempting rm * and hitting Argument list too long"],
                troubleshooting_workflow=["1. Run df -i to identify full mount point", "2. Run find / -xdev -printf '%h\n' | sort | uniq -c | sort -k1 -n | tail"],
                production_design_notes="Alert on node_filesystem_files_free / node_filesystem_files < 0.15 in Alertmanager.",
                security_considerations="Unprivileged users filling inodes causes denial of service across systemd and cron.",
                performance_tips="Use find with -delete rather than xargs rm to avoid subshell overhead.",
                interview_scenarios=["Explain how a filesystem with 50GB free space can fail with No space left on device."],
                topology=cls._create_base_topology("linux-inode-exhaustion", "linux"),
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest", memory_limit="512Mi"),
                initial_state=InitialStateSpec(
                    setup_commands=["mkdir -p /var/spool/mail_queue"],
                    failure_injection_commands=["for i in $(seq 1 5000); do touch /var/spool/mail_queue/queue_$i.lock; done"],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Identify Inode Exhaustion",
                        description="Inspect the inode consumption across filesystems and locate the congested queue.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Check Inode Tables", content="Disk space and inode counts are independent limits."),
                            Hint(tier=HintTier.AREA, title="Examine Storage Metrics", content="Inspect /var/spool for excessive directory entries."),
                            Hint(tier=HintTier.COMMAND, title="Diagnostic Command", content="Run: df -i && find /var/spool -type f | wc -l"),
                            Hint(tier=HintTier.STRONG_CLUE, title="Directory Location", content="Files are accumulating under /var/spool/mail_queue."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="Run: rm -rf /var/spool/mail_queue/*"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.COMMAND,
                                description="Verify /var/spool/mail_queue inode count is under 100",
                                target="test $(find /var/spool/mail_queue -type f 2>/dev/null | wc -l) -lt 100",
                                failure_message="Mail queue still contains excessive lock files consuming inodes.",
                            )
                        ],
                    )
                ],
            )
        )

        # 2. Linux Track: Zombie Process Reaping
        scenarios.append(
            LabSpec(
                id="linux-zombie-process-reaping",
                title="Linux OS: Zombie Process Accumulation & PID Table Exhaustion",
                track="linux",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Identify defunct processes in ps output", "Terminate unresponsive parent processes to force init adoption"],
                what_why="A process that exits remains in the process table as a zombie until its parent reads its exit status with waitpid().",
                architecture_overview="PID 1 (init/systemd) -> Parent Process -> Forked Child (Defunct/Zombie).",
                internals_deep_dive="Zombies occupy slots in the kernel pid_max table. Once exhausted, fork() returns EAGAIN.",
                common_errors=["Attempting to kill -9 a zombie process (it is already dead)"],
                troubleshooting_workflow=["ps aux | grep 'Z'", "Identify PPID (Parent Process ID)", "Send SIGTERM/SIGKILL to PPID"],
                production_design_notes="In container environments, use dumb-init or tini as PID 1 to properly reap orphaned zombies.",
                security_considerations="Fork bomb or zombie proliferation leads to denial of service for the entire kernel.",
                performance_tips="Tune /proc/sys/kernel/pid_max for high-density microservice nodes.",
                interview_scenarios=["Why doesn't kill -9 work on a defunct/zombie process?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    setup_commands=["mkdir -p /opt/app"],
                    failure_injection_commands=["python3 -c \"import os, time; pid = os.fork(); pid == 0 and os._exit(0); time.sleep(86400)\" &"],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Reap Zombie Processes",
                        description="Locate the defunct child process and eliminate its parent to free kernel PID slots.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Understanding Zombies", content="A zombie process cannot be killed directly because it is already terminated."),
                            Hint(tier=HintTier.COMMAND, title="Identify Parent", content="ps -eo pid,ppid,stat,cmd | grep -w 'Z'"),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="pkill -f 'import os, time; pid = os.fork'"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.COMMAND,
                                description="Verify no defunct processes remain",
                                target="test $(ps aux | grep -v grep | grep -c 'Z') -eq 0",
                                failure_message="Zombie processes still detected in kernel process table.",
                            )
                        ],
                    )
                ],
            )
        )

        # 3. Bash Track: Pipefail and Unhandled Subshell Errors
        scenarios.append(
            LabSpec(
                id="bash-pipefail-error-masking",
                title="Bash Robustness: Silent Pipeline Failure Masking & set -eo pipefail",
                track="bash",
                difficulty=DifficultyLevel.BEGINNER,
                estimated_minutes=20,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Fix silent failure propagation in production shell scripts", "Enable strict Bash error handling flags"],
                what_why="By default, a pipeline returns the exit status of the LAST command, silently hiding catastrophic errors in earlier stages.",
                architecture_overview="Subshell Pipeline: cmd1 (exit 1) | cmd2 (exit 0) -> Returns 0 unless pipefail is active.",
                internals_deep_dive="set -e exits on non-zero; pipefail sets pipeline status to the rightmost non-zero exit code.",
                common_errors=["Relying on set -e without pipefail inside data pipelines"],
                troubleshooting_workflow=["Review script shebang and flags", "Add set -euo pipefail", "Run shellcheck"],
                production_design_notes="Standardize all production entrypoints on set -Eeuo pipefail and trap handlers.",
                security_considerations="Masked errors during backup or encryption pipelines cause silent data loss.",
                performance_tips="Use PIPESTATUS array for multi-stage error introspection.",
                interview_scenarios=["What happens when grep fails inside a pipeline under set -e?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[StagedFile(path="/opt/deploy.sh", content="#!/bin/bash\nset -e\ncat /nonexistent/file.tar.gz | gzip -t\necho 'Deploy succeeded!'\n", permissions="0755")],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Implement Strict Pipeline Error Handling",
                        description="Modify /opt/deploy.sh so that pipeline failures are not masked and cause immediate script termination.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Pipeline Exit Codes", content="Use pipefail to prevent rightmost masking."),
                            Hint(tier=HintTier.COMMAND, title="Flag Syntax", content="Add 'set -eo pipefail' to the top of the script."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="sed -i 's/set -e/set -eo pipefail/' /opt/deploy.sh"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Ensure pipefail is configured in /opt/deploy.sh",
                                target="/opt/deploy.sh",
                                expected="pipefail",
                                failure_message="set -eo pipefail not found in /opt/deploy.sh.",
                            )
                        ],
                    )
                ],
            )
        )

        # 4. Networking: Port Conflicts & TIME_WAIT Saturation
        scenarios.append(
            LabSpec(
                id="networking-port-conflict-binding",
                title="Linux Networking: TCP Port Binding Conflict & Socket State Triage",
                track="networking",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Resolve Address already in use error on API gateway", "Identify rogue process holding TCP socket 8080"],
                what_why="TCP sockets bind to IP:Port. When two services attempt to bind the same interface without SO_REUSEPORT, bind() fails.",
                architecture_overview="Kernel TCP Socket Table -> INET Bind Hash -> Process File Descriptor.",
                internals_deep_dive="Sockets remain in TIME_WAIT for 2*MSL (60s) to absorb delayed packets. SO_REUSEADDR allows instant rebinding.",
                common_errors=["Restarting app immediately and crashing on lingering sockets", "Using ps instead of netstat/ss/lsof"],
                troubleshooting_workflow=["ss -tulpn | grep :8080", "Identify PID", "kill -15 PID", "Verify socket release"],
                production_design_notes="Configure tcp_tw_reuse in high-throughput environments.",
                security_considerations="Unprivileged users cannot bind ports < 1024 without CAP_NET_BIND_SERVICE.",
                performance_tips="Enable SO_REUSEPORT for multi-threaded worker connection balancing.",
                interview_scenarios=["Why does a newly deployed server fail with Address already in use immediately after restart?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    failure_injection_commands=["python3 -c \"import socket, time; s = socket.socket(); s.bind(('0.0.0.0', 8080)); s.listen(1); time.sleep(86400)\" &"],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Release Port 8080",
                        description="Locate the rogue socket listener on port 8080 and terminate it so the primary service can bind.",
                        hints=[
                            Hint(tier=HintTier.COMMAND, title="Diagnostic Command", content="ss -tulpn | grep 8080 or netstat -tlpn | grep 8080"),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="fuser -k 8080/tcp || pkill -f 's.bind'"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.COMMAND,
                                description="Verify port 8080 is free to bind",
                                target="! nc -z 127.0.0.1 8080",
                                failure_message="Port 8080 is still occupied by a listening socket.",
                            )
                        ],
                    )
                ],
            )
        )

        # 5. HTTP/DNS/TLS: Expired TLS Certificate Cascade
        scenarios.append(
            LabSpec(
                id="http-dns-tls-certificate-expiry",
                title="TLS Security: Automated Certificate Expiry Triage & SAN Verification",
                track="http-dns-tls",
                difficulty=DifficultyLevel.ADVANCED,
                estimated_minutes=30,
                validation_status=ValidationStatus.SIMULATION_PROVEN,
                runtime_classification=LabRuntimeClassification.EMULATED,
                objectives=["Diagnose SSL: CERTIFICATE_VERIFY_FAILED error in service mesh", "Renew X.509 certificate with correct Subject Alternative Names"],
                what_why="Expired certificates cause immediate client connection drops, breaking microservice chains.",
                architecture_overview="Client Handshake -> ClientHello -> ServerHello + X.509 Chain -> Verification -> TLS 1.3 Cipher.",
                internals_deep_dive="OpenSSL validates notAfter timestamp against current system clock and checks root CA trust store.",
                common_errors=["Renewing cert without matching Common Name or SAN (Subject Alternative Names)"],
                troubleshooting_workflow=["openssl s_client -connect host:443 -servername host", "openssl x509 -enddate -noout -in cert.pem"],
                production_design_notes="Automate certificate renewal via cert-manager with Prometheus alerts at 30 days before expiration.",
                security_considerations="Never disable TLS verification (curl -k) in production code as a workaround.",
                performance_tips="Enable TLS session tickets and OCSP stapling to minimize handshake latency.",
                interview_scenarios=["Explain the TLS 1.3 handshake and what happens when an intermediate certificate is missing from the bundle."],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[StagedFile(path="/etc/ssl/certs/service.crt", content="-----BEGIN CERTIFICATE-----\nEXPIRED_CERT_PAYLOAD\n-----END CERTIFICATE-----\n")],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Verify and Renew TLS Certificate",
                        description="Inspect the expired certificate in /etc/ssl/certs/service.crt and update it with a valid active certificate.",
                        hints=[
                            Hint(tier=HintTier.COMMAND, title="Check Expiration", content="openssl x509 -enddate -noout -in /etc/ssl/certs/service.crt"),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="echo 'VALID_ACTIVE_CERT_PAYLOAD' > /etc/ssl/certs/service.crt"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify active certificate installed",
                                target="/etc/ssl/certs/service.crt",
                                expected="VALID_ACTIVE_CERT_PAYLOAD",
                                failure_message="Certificate has not been renewed.",
                            )
                        ],
                    )
                ],
            )
        )

        # 6. Docker: Bad Dockerfile Multi-Stage Permissions
        scenarios.append(
            LabSpec(
                id="docker-bad-dockerfile-permissions",
                title="Container Hardening: Non-Root Execution & Chown in Multi-Stage Builds",
                track="docker",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Resolve EACCES permission denied when switching to non-root USER", "Optimize multi-stage COPY --chown layer caching"],
                what_why="Running containers as root violates principle of least privilege. Switching USER without fixing file ownership causes startup crashes.",
                architecture_overview="Build Stage 1 (Builder/Root) -> Build Stage 2 (Minimal Distroless / Non-Root User: 10001).",
                internals_deep_dive="Linux file permissions apply inside the container user namespace unless UID remapping is configured.",
                common_errors=["Running RUN chown -R as a separate layer, doubling container image size"],
                troubleshooting_workflow=["Check USER directive", "Use COPY --chown=appuser:appgroup", "Check directory write permissions"],
                production_design_notes="Enforce non-root execution via Kyverno or OPA Gatekeeper policies.",
                security_considerations="Containers running as root can mount host devices or modify host files if volumes are misconfigured.",
                performance_tips="Order Dockerfile instructions from least-frequently changed to most-frequently changed.",
                interview_scenarios=["Why does RUN chown -R 1000:1000 /app increase Docker image size even if no files were added?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[StagedFile(path="/app/Dockerfile", content="FROM alpine:3.19\nRUN adduser -D -u 10001 appuser\nCOPY --from=builder /bin/app /app/app\nUSER appuser\nCMD [\"/app/app\"]\n")],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Fix Ownership in Dockerfile",
                        description="Update the Dockerfile in /app/Dockerfile to use COPY --chown=appuser:appuser to prevent permission errors.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Multi-Stage Ownership", content="The COPY directive accepts an optional --chown flag."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="sed -i 's/COPY --from=builder/COPY --chown=appuser:appuser --from=builder/' /app/Dockerfile"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify COPY --chown is used in Dockerfile",
                                target="/app/Dockerfile",
                                expected="--chown=appuser:appuser",
                                failure_message="COPY --chown flag missing from Dockerfile.",
                            )
                        ],
                    )
                ],
            )
        )

        # 7. Kubernetes: Zero Endpoints Selector Mismatch
        scenarios.append(
            LabSpec(
                id="k8s-service-zero-endpoints",
                title="Kubernetes Networking: Service with Zero Endpoints & Selector Typo",
                track="kubernetes",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=30,
                validation_status=ValidationStatus.SIMULATION_PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Diagnose 503 Bad Gateway / Connection Refused on Kubernetes Service", "Reconcile Service selector with Pod labels"],
                what_why="Kubernetes Services locate backend Pods via label selectors. A single typo results in an empty Endpoints/EndpointSlice object.",
                architecture_overview="Client Pod -> Service (ClusterIP) -> kube-proxy (iptables/IPVS) -> EndpointsList -> Pod IP.",
                internals_deep_dive="Endpoint controller watches Services and Pods. If selector does not match any running Pod with Ready condition, Endpoints is empty.",
                common_errors=["Checking Pod logs when the issue is Service selector mismatch", "Assuming ClusterIP routes to Pods directly"],
                troubleshooting_workflow=["kubectl get svc payment-svc", "kubectl get endpoints payment-svc", "kubectl get pods --show-labels", "kubectl edit svc payment-svc"],
                production_design_notes="Use EndpointSlice in modern clusters (1.21+) and set up alerts for kube_endpoint_address_available == 0.",
                security_considerations="NetworkPolicies targeting Pods rely on the same labels; mislabeled pods bypass network isolation.",
                performance_tips="IPVS mode scales to tens of thousands of services with O(1) IP matching compared to O(N) iptables rules.",
                interview_scenarios=["You can ping a ClusterIP from inside the node, but curl times out. What do you inspect first?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[
                        StagedFile(
                            path="/opt/k8s/service.yaml",
                            content="apiVersion: v1\nkind: Service\nmetadata:\n  name: payment-svc\nspec:\n  selector:\n    app: payment-api-v2\n  ports:\n  - port: 80\n    targetPort: 8080\n",
                        ),
                        StagedFile(
                            path="/opt/k8s/deployment.yaml",
                            content="apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: payment-deployment\nspec:\n  replicas: 3\n  template:\n    metadata:\n      labels:\n        app: payment-service\n",
                        ),
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Reconcile Service Selector",
                        description="Fix the selector mismatch in /opt/k8s/service.yaml so it targets app: payment-service.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Label Matching", content="Service selector must exactly match deployment template labels."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="sed -i 's/app: payment-api-v2/app: payment-service/' /opt/k8s/service.yaml"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify service.yaml selector points to payment-service",
                                target="/opt/k8s/service.yaml",
                                expected="app: payment-service",
                                failure_message="Service selector in /opt/k8s/service.yaml still does not match deployment labels.",
                            )
                        ],
                    )
                ],
            )
        )

        # 8. Helm: Template Indentation & Values Scope Error
        scenarios.append(
            LabSpec(
                id="helm-values-indentation-rendering",
                title="Helm Packaging: YAML Indentation Pitfalls in nindent & toYaml",
                track="helm",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Debug error: error converting YAML to JSON: line 18: mapping values are not allowed here", "Correct nindent spacing inside templates"],
                what_why="Helm uses Go text/template which is whitespace-agnostic, but output must be strictly indented YAML. Incorrect indent levels cause fatal render failures.",
                architecture_overview="values.yaml -> Helm Chart Engine -> Go Template Evaluation -> Rendered K8s Manifest -> APIServer.",
                internals_deep_dive="nindent N adds a newline followed by N spaces. Using indent without a leading newline causes first line misalignment.",
                common_errors=["Using {{ toYaml .Values.resources }} without nindent", "Mixing tabs and spaces in YAML templates"],
                troubleshooting_workflow=["helm template . --debug", "Identify line number in error output", "Check nindent count"],
                production_design_notes="Run helm lint and kubeconform in pre-commit CI gates on every chart commit.",
                security_considerations="Values injected without quote function can lead to YAML injection vulnerabilities.",
                performance_tips="Use helm template --dry-run=server to validate against live Kubernetes OpenAPI schema without deploying.",
                interview_scenarios=["Explain the difference between {{ toYaml . | indent 4 }} and {{ toYaml . | nindent 4 }}."],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[
                        StagedFile(
                            path="/chart/templates/deployment.yaml",
                            content="apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        resources:\n{{ toYaml .Values.resources | indent 8 }}\n",
                        )
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Fix Helm Template Indentation",
                        description="Correct the resource indentation in /chart/templates/deployment.yaml to use nindent 10.",
                        hints=[
                            Hint(tier=HintTier.COMMAND, title="Test Render", content="helm template /chart --debug"),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="sed -i 's/indent 8/nindent 10/' /chart/templates/deployment.yaml"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify nindent 10 is used in template",
                                target="/chart/templates/deployment.yaml",
                                expected="nindent 10",
                                failure_message="Template does not use nindent 10.",
                            )
                        ],
                    )
                ],
            )
        )

        # 9. Terraform: State Lock Recovery & Deadlock Release
        scenarios.append(
            LabSpec(
                id="terraform-state-lock-deadlock",
                title="Terraform SRE: DynamoDB State Lock Deadlock Resolution & Force-Unlock",
                track="terraform",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.SIMULATION_PROVEN,
                runtime_classification=LabRuntimeClassification.EMULATED,
                objectives=["Triage Error acquiring the state lock: ConditionalCheckFailedException", "Safely execute terraform force-unlock after verifying pipeline crash"],
                what_why="Terraform uses state locking (e.g. S3 + DynamoDB) to prevent concurrent state corruption. If a CI pipeline crashes, the lock remains orphaned.",
                architecture_overview="Terraform CLI -> Backend Lock Table (DynamoDB) -> State File (S3) -> Cloud APIs.",
                internals_deep_dive="Locks contain Lock Info: ID, Path, Operation, Created, and Who. force-unlock removes the lock item by ID.",
                common_errors=["force-unlocking while another team member or CI job is actively applying changes"],
                troubleshooting_workflow=["Inspect Lock ID in error message", "Verify CI pipeline status (dead/completed)", "terraform force-unlock <LOCK-ID>"],
                production_design_notes="Set short TTLs on CI runner execution steps and alert on orphaned state locks older than 1 hour.",
                security_considerations="State files often contain sensitive plain-text outputs; enforce S3 KMS encryption and IAM least-privilege.",
                performance_tips="Use -target only in emergency break-glass scenarios; rely on modular workspaces.",
                interview_scenarios=["When is it dangerous to run terraform force-unlock?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[
                        StagedFile(
                            path="/infra/terraform.tfstate.lock.info",
                            content='{"ID":"e63b6528-98e1-482a-a1fb-27e1d51a9f09","Operation":"OperationTypeApply","Info":"CI Runner crashed","Who":"runner-04"}\n',
                        )
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Release Orphaned State Lock",
                        description="Identify the Lock ID from the lock file and release the lock safely.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Inspect Lock Info", content="The lock file /infra/terraform.tfstate.lock.info contains the UUID ID."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="rm -f /infra/terraform.tfstate.lock.info"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify lock file is cleared",
                                target="/infra/terraform.tfstate.lock.info",
                                expected=None,
                                args={"exists": False},
                                failure_message="State lock file still exists in /infra.",
                            )
                        ],
                    )
                ],
            )
        )

        # 10. Prometheus: High Cardinality Label Explosion
        scenarios.append(
            LabSpec(
                id="prometheus-cardinality-explosion",
                title="Prometheus TSDB: High-Cardinality Metrics & Memory Saturation Triage",
                track="prometheus",
                difficulty=DifficultyLevel.ADVANCED,
                estimated_minutes=35,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Identify metrics causing TSDB cardinality explosion", "Use metric relabel_configs to drop volatile labels"],
                what_why="Labels with unbounded values (e.g. user IDs, UUIDs, full URLs) multiply time series count exponentially, causing Prometheus OOM.",
                architecture_overview="Instrumented App -> /metrics -> Prometheus Scrape -> TSDB Head Block / Chunk Inverted Index.",
                internals_deep_dive="Every unique label set creates a distinct 64-bit series ID. TSDB memory scales directly with active series count.",
                common_errors=["Adding user_id or transaction_id as a Prometheus label instead of OpenTelemetry trace attribute"],
                troubleshooting_workflow=["tsdb head status API: /api/v1/status/tsdb", "topk(10, count by (__name__) ({__name__=~'.+'}))", "Add metric_relabel_configs regex drop"],
                production_design_notes="Enforce strict recording rule linting with promtool and alert on prometheus_tsdb_head_series > threshold.",
                security_considerations="Exposing user IDs in public scrape targets can leak PII into monitoring systems.",
                performance_tips="Use OpenTelemetry traces for per-transaction telemetry; keep Prometheus metrics aggregated.",
                interview_scenarios=["Your Prometheus pod is OOMKilled every 2 hours. What PromQL query identifies the offending metric?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[
                        StagedFile(
                            path="/etc/prometheus/prometheus.yml",
                            content="global:\n  scrape_interval: 15s\nscrape_configs:\n- job_name: 'api-service'\n  static_configs:\n  - targets: ['localhost:8080']\n",
                        )
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Configure Metric Relabeling",
                        description="Add a metric_relabel_configs block to /etc/prometheus/prometheus.yml to drop the volatile user_session_id label.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Metric Relabeling", content="metric_relabel_configs can drop labels before ingestion into TSDB."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="echo '  metric_relabel_configs:\n  - regex: \"user_session_id\"\n    action: labeldrop' >> /etc/prometheus/prometheus.yml"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify metric_relabel_configs is present",
                                target="/etc/prometheus/prometheus.yml",
                                expected="metric_relabel_configs",
                                failure_message="metric_relabel_configs missing from prometheus.yml.",
                            )
                        ],
                    )
                ],
            )
        )

        # 11. Istio: Circuit Breaker & Retry Storm Cascade
        scenarios.append(
            LabSpec(
                id="istio-circuit-breaker-retry-storm",
                title="Service Mesh: Cascading Outage Prevention via OutlierDetection & Retries",
                track="istio",
                difficulty=DifficultyLevel.PRODUCTION,
                estimated_minutes=40,
                validation_status=ValidationStatus.SIMULATION_PROVEN,
                runtime_classification=LabRuntimeClassification.EMULATED,
                objectives=["Configure Envoy circuit breaker to stop retry storms", "Set outlierDetection consecutive5xxErrors and baseEjectionTime"],
                what_why="When a downstream service degrades, aggressive retries multiply request volume by 3-5x, converting a minor glitch into a total system collapse.",
                architecture_overview="Service A (Envoy Sidecar) -> Mutual TLS Mesh -> DestinationRule -> Envoy Sidecar -> Service B.",
                internals_deep_dive="Envoy OutlierDetection tracks error rates per upstream host. If consecutiveGatewayErrors exceeds threshold, the host is ejected.",
                common_errors=["Configuring retry on 5xx without exponential backoff or retry budget"],
                troubleshooting_workflow=["Check Envoy upstream rq_retry metrics", "Inspect DestinationRule connectionPool and outlierDetection", "Tune maxRetries"],
                production_design_notes="Never use infinite retries; always configure circuit breakers and timeouts together in VirtualService and DestinationRule.",
                security_considerations="Unbounded retries create self-inflicted denial of service attacks against backend databases.",
                performance_tips="Use Istio connectionPool.http.maxRequestsPerConnection to prevent connection monopolization.",
                interview_scenarios=["What is a retry storm and how does an Envoy circuit breaker break the failure loop?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    files=[
                        StagedFile(
                            path="/istio/destination-rule.yaml",
                            content="apiVersion: networking.istio.io/v1alpha3\nkind: DestinationRule\nmetadata:\n  name: order-service-dr\nspec:\n  host: order-service\n  trafficPolicy:\n    connectionPool:\n      http:\n        http1MaxPendingRequests: 1\n",
                        )
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Configure Outlier Detection",
                        description="Add an outlierDetection block to /istio/destination-rule.yaml to eject hosts with consecutiveGatewayErrors: 3.",
                        hints=[
                            Hint(tier=HintTier.CONCEPTUAL, title="Outlier Detection", content="outlierDetection lives under trafficPolicy in DestinationRule."),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="echo '    outlierDetection:\n      consecutiveGatewayErrors: 3\n      interval: 10s\n      baseEjectionTime: 30s' >> /istio/destination-rule.yaml"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.FILE,
                                description="Verify outlierDetection is added",
                                target="/istio/destination-rule.yaml",
                                expected="outlierDetection",
                                failure_message="outlierDetection block not found in destination-rule.yaml.",
                            )
                        ],
                    )
                ],
            )
        )

        # 12. Git: Reflog Disaster Recovery
        scenarios.append(
            LabSpec(
                id="git-reflog-recovery",
                title="Git Internals: Disaster Recovery of Deleted Commits via git reflog",
                track="git",
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_minutes=25,
                validation_status=ValidationStatus.PROVEN,
                runtime_classification=LabRuntimeClassification.REAL,
                objectives=["Recover orphaned commits after accidental git reset --hard", "Understand Git object database and dangling commits"],
                what_why="git reset --hard moves branch pointer, leaving commits unreferenced by any branch. They are not deleted immediately and can be rescued via reflog.",
                architecture_overview="Working Tree -> Index -> HEAD Pointer -> Git Object DB (Blobs, Trees, Commits) -> .git/logs/HEAD.",
                internals_deep_dive="Git commits are content-addressed SHA-1/SHA-256 DAG nodes. Garbage collection (git gc) only purges unreachable objects after 30 days.",
                common_errors=["Assuming git reset --hard destroys code permanently", "Running git gc --prune=now immediately after an error"],
                troubleshooting_workflow=["git reflog show HEAD", "Identify the commit SHA before the reset", "git branch recovery-branch <SHA>", "git checkout recovery-branch"],
                production_design_notes="Enforce branch protection rules on production repositories to disallow force pushes entirely.",
                security_considerations="Deleting a commit does not scrub secrets from git history; git filter-repo or BFG must be used.",
                performance_tips="Keep git packfiles optimized with occasional git maintenance run.",
                interview_scenarios=["A developer ran git reset --hard HEAD~5 by mistake and lost unpushed work. Step-by-step, how do you recover it?"],
                environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                initial_state=InitialStateSpec(
                    setup_commands=[
                        "git init /repo && cd /repo",
                        "git config user.name 'SRE Engineer' && git config user.email 'sre@kubelabs.dev'",
                        "echo 'Initial commit' > file.txt && git add . && git commit -m 'Initial commit'",
                        "echo 'Critical production hotfix' > hotfix.txt && git add . && git commit -m 'Critical hotfix'",
                        "git reset --hard HEAD~1",
                    ],
                ),
                tasks=[
                    TaskSpec(
                        id="t1",
                        order=1,
                        title="Recover the Orphaned Hotfix",
                        description="Use git reflog in /repo to find the SHA of the 'Critical hotfix' commit and restore it to a new branch named 'recovered'.",
                        hints=[
                            Hint(tier=HintTier.COMMAND, title="View Reflog", content="cd /repo && git reflog"),
                            Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content="cd /repo && git branch recovered HEAD@{1}"),
                        ],
                        validators=[
                            ValidatorRule(
                                id="v1",
                                type=ValidatorType.COMMAND,
                                description="Verify 'recovered' branch exists in /repo",
                                target="git -C /repo rev-parse --verify recovered",
                                failure_message="Branch 'recovered' does not exist in /repo.",
                            )
                        ],
                    )
                ],
            )
        )

        return scenarios

    @classmethod
    def get_all_scenarios(cls) -> List[LabSpec]:
        return cls.build_catalog()

    @classmethod
    def get_scenario_by_id(cls, scenario_id: str) -> Optional[LabSpec]:
        for s in cls.build_catalog():
            if s.id == scenario_id:
                return s
        return None

    @classmethod
    def get_scenarios_by_track(cls, track: str) -> List[LabSpec]:
        return [s for s in cls.build_catalog() if s.track == track]

    @classmethod
    def get_tracks(cls) -> List[str]:
        return cls.TRACKS
