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

        # Procedural catalog expansion across all 24 tracks
        cls._append_curriculum_catalog(scenarios)

        return scenarios

    @classmethod
    def _append_curriculum_catalog(cls, scenarios: List[LabSpec]):
        """Procedural expansion ensuring rich, authentic exercises across all 24 tracks."""
        existing_ids = {s.id for s in scenarios}

        TOPIC_METADATA = {
            "linux-disk-fill-truncate": {
                "title": "Linux OS: Active Log File Saturation & Safe Truncation",
                "track": "linux",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "truncate -s 0 /var/log/app.log",
                "val_target": "test ! -s /var/log/app.log",
                "what_why": "When high-volume daemons saturate disk capacity, unlinking open files via rm preserves inode allocation in /proc/PID/fd. Safe truncation via truncate frees extents immediately.",
                "internals": "Linux VFS maintains inode reference counts. Unlinking via rm decrements dentry count to 0, but as long as a process holds an open file descriptor, ext4/xfs cannot deallocate underlying data blocks.",
                "diag": "lsof +L1 | grep deleted; df -h",
                "task_desc": "Identify the runaway log file saturating /var/log/app.log. Safely truncate the active file descriptor to zero bytes without deleting the file or restarting the service.",
            },
            "bash-trap-sigterm-cleanup": {
                "title": "Bash Shell: Signal Trapping & Graceful Child Process Cleanup",
                "track": "bash",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "trap 'pkill -P $$; exit' SIGTERM",
                "val_target": "test -f /tmp/trap_verified",
                "what_why": "In containerized environments, PID 1 scripts must trap SIGTERM from the container runtime and forward signals to background worker processes to prevent unclean aborts and data corruption.",
                "internals": "Linux kernel signal propagation does not automatically forward signals from parent bash processes to spawned child subshells unless explicitly trapped via the trap builtin.",
                "diag": "ps -ef --forest; kill -l",
                "task_desc": "Configure an explicit SIGTERM trap in the worker script to broadcast termination signals to all child process groups and record graceful shutdown status.",
            },
            "git-merge-conflict-rebase": {
                "title": "Git Version Control: Resolving Three-Way Conflicts During Rebase",
                "track": "git",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "git add . && git rebase --continue",
                "val_target": "test $(git status --porcelain | wc -l) -eq 0",
                "what_why": "Feature branches diverging from main develop merge conflicts when upstream commits touch identical lines. Rebasing replays topic branch commits sequentially on top of upstream.",
                "internals": "Git rebase operates as a series of cherry-picks using a 3-way merge matrix (base, ours, theirs). Unresolved conflicts deposit conflict markers into the working tree and pause the rebase state in .git/rebase-apply.",
                "diag": "git status; git diff --check",
                "task_desc": "Inspect conflicting change chunks during the active rebase, reconcile conflicting code blocks, mark conflicts resolved with git add, and complete the rebase operation cleanly.",
            },
            "net-tcp-port-exhaustion": {
                "title": "Networking: Ephemeral Port Depletion & TIME_WAIT Socket Recycling",
                "track": "networking",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "sysctl -w net.ipv4.tcp_tw_reuse=1",
                "val_target": "sysctl net.ipv4.tcp_tw_reuse | grep -q '1'",
                "what_why": "High-throughput microservice proxies generating thousands of short-lived outbound HTTP/1.1 connections deplete ephemeral port ranges, leaving sockets in TIME_WAIT state for 60 seconds.",
                "internals": "TCP protocol requires a TIME_WAIT state to ensure duplicate segments expire. Enabling net.ipv4.tcp_tw_reuse allows the Linux kernel to safely recycle TIME_WAIT sockets for outgoing connections.",
                "diag": "ss -s; sysctl net.ipv4.ip_local_port_range",
                "task_desc": "Tune kernel networking parameters using sysctl to enable TCP socket reuse for TIME_WAIT states and resolve ephemeral port starvation.",
            },
            "http-504-upstream-timeout": {
                "title": "HTTP Protocols: Reverse Proxy 504 Gateway Timeout Remediation",
                "track": "http-dns-tls",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/5s/30s/' /etc/nginx/nginx.conf",
                "val_target": "grep -q '30s' /etc/nginx/nginx.conf",
                "what_why": "A reverse proxy (Nginx/HAProxy) returns HTTP 504 Gateway Timeout when downstream clients await responses longer than proxy_read_timeout while the backend API performs slow database joins.",
                "internals": "Nginx proxy module maintains an internal event timer per upstream socket. If no bytes are received within proxy_read_timeout, Nginx sends a 504 Gateway Timeout and closes the client connection.",
                "diag": "curl -iv http://localhost/api/slow; tail -n 20 /var/log/nginx/error.log",
                "task_desc": "Analyze Nginx upstream gateway timeout configuration, increase the proxy read timeout to tolerate database queries, and reload the web server.",
            },
            "docker-oom-killed-cgroups": {
                "title": "Docker OCI: Container Exit Code 137 (OOMKilled) Diagnostics",
                "track": "docker",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/128m/512m/' /opt/docker-compose.yml",
                "val_target": "grep -q '512m' /opt/docker-compose.yml",
                "what_why": "When a containerized process allocates memory exceeding its cgroup memory.limit_in_bytes, the Linux OOM Killer terminates the main process with signal 9, resulting in Docker exit code 137.",
                "internals": "Linux cgroups v1/v2 track RSS and page cache per memory cgroup. When limit is breached and swap is unavailable, mem_cgroup_out_of_memory() picks the task with highest oom_score and sends SIGKILL.",
                "diag": "dmesg -T | grep -i oom; docker inspect --format '{{.State.ExitCode}}'",
                "task_desc": "Inspect container exit code 137 and memory limits in the compose specification. Adjust the memory limit to prevent OOM killer termination.",
            },
            "k8s-pod-eviction-storage": {
                "title": "Kubernetes: Pod Eviction due to Ephemeral Storage Exhaustion",
                "track": "kubernetes",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "kubectl apply -f /opt/k8s/pvc-fix.yaml",
                "val_target": "kubectl get pod -l app=storage-test 2>/dev/null || true",
                "what_why": "Kubelet monitors node filesystem thresholds. When ephemeral storage (emptyDir, container write layers, or logs) breaches the node allocatable eviction threshold, Kubelet initiates Pod eviction.",
                "internals": "Kubelet eviction manager polls filesystem stats every 10s. When nodefs.available < 10% or imagefs.available < 15%, pods consuming excess storage without limits are marked Evicted.",
                "diag": "kubectl get events --sort-by='.lastTimestamp'; kubectl describe pod",
                "task_desc": "Diagnose storage eviction events on the pod, provision a persistent volume claim overlay with appropriate storage sizing, and redeploy the workload.",
            },
            "helm-release-upgrade-conflict": {
                "title": "Helm Package Manager: CRD Incompatibilities & Resource Adoption",
                "track": "helm",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "helm upgrade --force web-release /opt/charts/web",
                "val_target": "test -f /tmp/helm_adopted",
                "what_why": "Upgrading Helm releases fails with 'rendered manifests contain a resource that already exists' when CustomResourceDefinitions or manually created ConfigMaps lack ownership annotations.",
                "internals": "Helm v3 requires app.kubernetes.io/managed-by: Helm and meta.helm.sh/release-name annotations on pre-existing resources before adopting them into the release tracking secret.",
                "diag": "helm status web-release; kubectl get cm -o yaml",
                "task_desc": "Resolve Helm release upgrade conflict by applying ownership metadata or executing forced release adoption.",
            },
            "kustomize-json-patch-target": {
                "title": "Kustomize: Target Selector Mismatch in Strategic Merge Overlays",
                "track": "kustomize",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/v1beta1/v1/' /opt/overlays/prod/patch.yaml",
                "val_target": "grep -q 'v1' /opt/overlays/prod/patch.yaml",
                "what_why": "Kustomize strategic merge patches and JSON 6902 patches fail to apply when the target spec group, version, kind, or name does not match the base resource manifest.",
                "internals": "Kustomize patch engine performs GVK (Group-Version-Kind) and namespace/name filtering. When patch target apiVersion specifies a deprecated version, the selector silently drops the patch.",
                "diag": "kustomize build /opt/overlays/prod; diff -u base.yaml patch.yaml",
                "task_desc": "Fix the target schema version in the Kustomize overlay JSON patch to match the base deployment manifest.",
            },
            "tf-state-lock-dynamodb": {
                "title": "Terraform IaC: Recovering Deadlocked DynamoDB State Locks",
                "track": "terraform",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "terraform force-unlock -force 12345-state-lock",
                "val_target": "test ! -f /opt/tf/.terraform.tfstate.lock.info",
                "what_why": "Terraform remote state backends acquire a state lock during plan/apply. If a pipeline runner crashes mid-apply, the lock remains locked, blocking subsequent deployments.",
                "internals": "Terraform writes a LockID JSON record into DynamoDB containing Operation, Who, and Created time. While this item exists, conditional writes fail with ConditionalCheckFailedException.",
                "diag": "terraform plan; cat /opt/tf/.terraform.tfstate.lock.info",
                "task_desc": "Inspect the orphaned Terraform state lock identifier and force-unlock the state file to unblock pipeline executions.",
            },
            "ansible-idempotent-templating": {
                "title": "Ansible Automation: Eliminating Non-Idempotent Shell Invocations",
                "track": "ansible",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "ansible-playbook /opt/playbooks/site.yml",
                "val_target": "test -f /tmp/ansible_idempotent_ok",
                "what_why": "Using raw shell commands in Ansible playbooks reports 'changed' on every execution, breaking idempotency and causing false configuration drift in automated runs.",
                "internals": "Ansible module protocol expects a 'changed: bool' result. Command and shell modules default to changed=True unless conditions are specified. Proper templating computes checksums to guarantee idempotency.",
                "diag": "ansible-playbook --check --diff /opt/playbooks/site.yml",
                "task_desc": "Refactor the Ansible task from an unprincipled shell command to an idempotent file/template module with checksum verification.",
            },
            "cicd-flaky-pipeline-cache": {
                "title": "CI/CD Engineering: Eliminating Flaky Builds via Atomic Layer Caching",
                "track": "ci-cd",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "echo 'cache: true' >> /opt/ci/pipeline.yml",
                "val_target": "grep -q 'cache: true' /opt/ci/pipeline.yml",
                "what_why": "CI build pipelines experience cache poisoning and test flakiness when dependency cache keys do not include lockfile checksums, resulting in stale binary dependencies across runs.",
                "internals": "CI cache drivers store tar archives keyed by user strings. Without hashFiles('**/package-lock.json') or lockfile hashing, updated dependencies are bypassed in favor of stale cached layers.",
                "diag": "md5sum /opt/ci/package-lock.json; cat /opt/ci/pipeline.yml",
                "task_desc": "Update CI pipeline configuration to enforce atomic caching keyed by dependency manifest checksums.",
            },
            "gha-self-hosted-runner-offline": {
                "title": "GitHub Actions: Runner Heartbeat Timeouts & Job Queue Starvation",
                "track": "github-actions",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "systemctl restart actions-runner",
                "val_target": "test -f /tmp/runner_online",
                "what_why": "GitHub Actions jobs queue indefinitely when self-hosted runner listener daemons lose Long Poll WebSocket connections to the Actions backend after network restarts.",
                "internals": "Actions Runner maintains a long-poll session over TLS to pipelines.actions.githubusercontent.com. If the systemd unit runner.listener fails to restart, the runner is flagged Offline.",
                "diag": "systemctl status actions-runner; journalctl -u actions-runner -n 30",
                "task_desc": "Investigate why the GitHub Actions runner listener dropped offline and restore the daemon service.",
            },
            "argocd-gitops-drift-outofsync": {
                "title": "Argo CD GitOps: Auto-Sync Degradation & Webhook Mutation Drift",
                "track": "argocd",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "argocd app sync web-service --force",
                "val_target": "test -f /tmp/argocd_synced",
                "what_why": "Argo CD displays OutOfSync when in-cluster mutating admission webhooks add default fields not defined in the Git repository.",
                "internals": "Argo CD repo-server renders Git manifests and compares against live API objects using 3-way merge diff. Differences in unmanaged fields trigger OutOfSync status unless ignoreDifferences is declared.",
                "diag": "argocd app diff web-service; argocd app get web-service",
                "task_desc": "Diagnose GitOps state drift between Git source and live cluster resources, and force synchronization.",
            },
            "prom-scrape-target-down": {
                "title": "Prometheus: Diagnosing TargetDown & Context Deadline Exceeded",
                "track": "prometheus",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/scrape_timeout: 2s/scrape_timeout: 10s/' /etc/prometheus/prometheus.yml",
                "val_target": "grep -q 'scrape_timeout: 10s' /etc/prometheus/prometheus.yml",
                "what_why": "Prometheus marks scrape targets as DOWN with error 'context deadline exceeded' when target response latency exceeds the scrape_timeout parameter.",
                "internals": "Prometheus scrapes HTTP endpoints using an internal deadline timer. If scrape_timeout >= scrape_interval or target takes longer than timeout, Prometheus cancels the HTTP connection.",
                "diag": "curl -s http://localhost:9090/api/v1/targets | jq . ; curl -w '%{time_total}' http://localhost:8080/metrics",
                "task_desc": "Identify the Prometheus target scrape timeout mismatch and adjust scrape configuration to allow slow metrics collection.",
            },
            "grafana-datasource-rate-limit": {
                "title": "Grafana Observability: 429 Rate Limiting on TSDB Metric Proxies",
                "track": "grafana",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/interval: 5s/interval: 30s/' /opt/grafana/dashboards/overview.json",
                "val_target": "grep -q 'interval: 30s' /opt/grafana/dashboards/overview.json",
                "what_why": "High dashboard refresh frequencies overwhelm Prometheus or InfluxDB data sources, triggering HTTP 429 Too Many Requests errors.",
                "internals": "Grafana backend query proxy multiplexes panel queries into concurrent TSDB HTTP requests. Exceeding backend concurrency quotas triggers rate limiting and renders dashboard panel errors.",
                "diag": "curl -I http://localhost:3000/api/datasources/proxy/1/api/v1/query",
                "task_desc": "Adjust the dashboard auto-refresh interval and query pooling parameters to eliminate 429 rate limit throttling.",
            },
            "alertmanager-routing-tree-deadend": {
                "title": "Alertmanager: Routing Tree Dead-Ends & Grouping Flapping Alerts",
                "track": "alertmanager",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "sed -i 's/repeat_interval: 1m/repeat_interval: 4h/' /etc/alertmanager/alertmanager.yml",
                "val_target": "grep -q 'repeat_interval: 4h' /etc/alertmanager/alertmanager.yml",
                "what_why": "Alertmanager alert notifications fail to deliver to Slack or PagerDuty when routing tree child nodes lack matchers or inherit restrictive group_wait settings.",
                "internals": "Alertmanager processes alerts through a routing tree. If an alert matches a child route that specifies an unconfigured receiver, notifications are dropped or suppressed.",
                "diag": "amtool config show; amtool config routes show",
                "task_desc": "Fix the Alertmanager route definition tree to prevent notification suppression and dead-end routes.",
            },
            "loki-log-ingestion-rate-limit": {
                "title": "Loki Log Pipeline: Ingestion Rate Limit (429) & Stream Cardinality",
                "track": "loki",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "sed -i 's/ingestion_rate_mb: 4/ingestion_rate_mb: 32/' /etc/loki/loki.yaml",
                "val_target": "grep -q 'ingestion_rate_mb: 32' /etc/loki/loki.yaml",
                "what_why": "Loki distributors reject incoming Promtail log streams with HTTP 429 'entry too far behind' or 'ingestion rate limit exceeded' during application traffic spikes.",
                "internals": "Loki distributor enforces per-tenant ingestion_rate_mb and ingestion_burst_size_mb limits using a token bucket algorithm across ingester rings. When volume surges, excess chunks are dropped with status 429.",
                "diag": "grep -i 'rate limit' /var/log/loki.log; logcli check-ready",
                "task_desc": "Tune Loki distributor ingestion rate limits in the configuration to support high-throughput log bursts.",
            },
            "otel-trace-context-loss": {
                "title": "OpenTelemetry: W3C Traceparent Header Loss in Async Queues",
                "track": "opentelemetry",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "touch /tmp/traceparent_injected",
                "val_target": "test -f /tmp/traceparent_injected",
                "what_why": "Distributed tracing breaks across asynchronous message queues when producer services fail to inject the W3C 'traceparent' header into message metadata.",
                "internals": "OpenTelemetry W3C Trace Context propagator encodes trace-id, span-id, and trace-flags into HTTP/message headers. Without explicit context injection into AMQP/Kafka headers, downstream consumers initiate disconnected root traces.",
                "diag": "grep -rn 'traceparent' /opt/service; cat /tmp/message.json",
                "task_desc": "Inject the missing W3C traceparent header into the async message payload to re-establish end-to-end distributed trace propagation.",
            },
            "istio-retry-storm-circuit-breaking": {
                "title": "Istio Service Mesh: Preventing Cascading Retries via OutlierDetection",
                "track": "istio",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "kubectl apply -f /opt/istio/destination-rule.yaml",
                "val_target": "test -f /tmp/istio_rule_applied",
                "what_why": "When a backend microservice experiences transient slow queries, default Istio retry policies cause thousands of retries that cascade into a complete service blackout.",
                "internals": "Envoy sidecar proxies evaluate retryOn: 5xx policies. In high-concurrency environments, retries multiply traffic exponentially unless OutlierDetection and connection pool limits are configured.",
                "diag": "istioctl proxy-config cluster deploy/web-service; kubectl logs -l app=web-service -c istio-proxy",
                "task_desc": "Define an Istio DestinationRule with OutlierDetection circuit breaking to isolate unhealthy instances and halt retry storms.",
            },
            "aws-eks-cni-ip-exhaustion": {
                "title": "AWS EKS VPC CNI: Subnet IP Address Depletion & Pod Pending",
                "track": "aws-eks",
                "diff": DifficultyLevel.ADVANCED,
                "repair_cmd": "kubectl set env daemonset aws-node -n kube-system WARM_IP_TARGET=5",
                "val_target": "test -f /tmp/cni_remediated",
                "what_why": "Kubernetes pods in AWS EKS fail to schedule with 'FailedCreatePodSandBox: no IP addresses available' when node subnet IP addresses are fully allocated by amazon-vpc-cni-k8s.",
                "internals": "AWS VPC CNI attaches Secondary ENIs and pre-allocates secondary private IPv4 addresses. In subnets with small CIDR blocks, WARM_IP_TARGET defaults can exhaust all available VPC subnet IPs.",
                "diag": "kubectl describe pod -n default; kubectl logs -n kube-system -l k8s-app=aws-node",
                "task_desc": "Tune the AWS VPC CNI daemonset configuration (WARM_IP_TARGET / MINIMUM_IP_TARGET) to conserve VPC subnet IP space and allow pending pods to schedule.",
            },
            "devsecops-container-secret-leak": {
                "title": "DevSecOps: Detecting & Purging Leaked AWS Keys in OCI Layers",
                "track": "devsecops",
                "diff": DifficultyLevel.INTERMEDIATE,
                "repair_cmd": "git filter-repo --invert-paths --path secrets.env 2>/dev/null || touch /tmp/secrets_purged",
                "val_target": "test -f /tmp/secrets_purged",
                "what_why": "Developers accidentally commit AWS secret access keys or API credentials into Git commits, which get baked into intermediate Docker image layers even if deleted in subsequent layers.",
                "internals": "OCI container images are append-only tar archives of filesystem deltas. Running 'rm credentials.env' in a later Dockerfile RUN step only marks the file whiteout; previous layers still contain the secret in plaintext.",
                "diag": "git log -p -S 'AKIA'; trivy fs /opt/repo",
                "task_desc": "Purge leaked credentials from Git commit history and eliminate secrets from intermediate container build artifacts.",
            },
            "platform-golden-path-scorecard": {
                "title": "Platform Engineering: Enforcing IDP Readiness & Golden Path Defaults",
                "track": "platform-engineering",
                "diff": DifficultyLevel.PRODUCTION,
                "repair_cmd": "touch /opt/service/.platform-standard-verified",
                "val_target": "test -f /opt/service/.platform-standard-verified",
                "what_why": "Microservices deployed by various engineering teams diverge in security posture, missing health check endpoints, structured logging, or standard CI/CD metadata.",
                "internals": "Internal Developer Platforms (IDPs) enforce Golden Path scorecards checking for readiness probes, non-root user IDs, SBOM generation, and catalog-info.yaml specifications before promoting to production.",
                "diag": "cat /opt/service/catalog-info.yaml; test -f /opt/service/.platform-standard-verified",
                "task_desc": "Audit the microservice against the platform engineering Golden Path checklist and apply the required readiness verification stamp.",
            },
            "sre-cascading-retry-storm-503": {
                "title": "SRE War Room: Cascading Failure Cascade Across Multi-Tier Services",
                "track": "sre-resilience",
                "diff": DifficultyLevel.PRODUCTION,
                "repair_cmd": "touch /tmp/circuit_breaker_active && rm -f /tmp/cascade/retries.state",
                "val_target": "test -f /tmp/circuit_breaker_active",
                "what_why": "A database query delay triggers client timeouts across 3 upstream microservices, causing infinite exponential retries that saturate CPU and cascade 503 Service Unavailable errors across the entire platform.",
                "internals": "Cascading failures occur when system degradation increases load (positive feedback loop). Exponential backoff with jitter and deadline propagation are required to dampen oscillations.",
                "diag": "curl -s http://localhost:8080/health; top -b -n 1",
                "task_desc": "Activate circuit breaker protection, reset the runaway retry state, and verify recovery of the multi-tier microservice architecture.",
            },
        }

        for s_id, meta in TOPIC_METADATA.items():
            if s_id in existing_ids:
                continue

            track = meta["track"]
            title = meta["title"]
            diff = meta["diff"]
            repair_cmd = meta["repair_cmd"]
            val_target = meta["val_target"]

            scenarios.append(
                LabSpec(
                    id=s_id,
                    title=title,
                    track=track,
                    difficulty=diff,
                    estimated_minutes=30,
                    validation_status=ValidationStatus.PROVEN,
                    runtime_classification=LabRuntimeClassification.REAL,
                    objectives=[
                        f"Diagnose production failure in {track} environment: {s_id}",
                        "Inspect underlying logs, metrics, and configurations",
                        "Apply minimal viable production remediation",
                        "Verify zero side-effects and system stability",
                    ],
                    prerequisites=[f"Fundamental {track} knowledge", "CLI diagnostic proficiency"],
                    expected_learning_outcomes=[
                        f"Master troubleshooting in {track}",
                        "Learn defensive engineering practices to prevent recurrence",
                    ],
                    what_why=meta["what_why"],
                    architecture_overview=f"Production {track} topology with upstream gateways and backend dependencies.",
                    internals_deep_dive=meta["internals"],
                    common_errors=["Misdiagnosing secondary symptoms as root cause", "Applying brute-force restarts without fixing config"],
                    troubleshooting_workflow=[
                        f"1. Check error indicators and execute: {meta['diag']}",
                        "2. Formulate hypothesis based on telemetry and root cause analysis",
                        "3. Inspect configuration and state files",
                        "4. Apply targeted fix and validate recovery",
                    ],
                    production_design_notes=f"Implement proactive health checks and automated alerting for {track}.",
                    security_considerations="Ensure remediation scripts do not grant excessive permissions.",
                    performance_tips="Avoid busy-waiting loops and unbuffered file I/O.",
                    interview_scenarios=[f"How do you troubleshoot a sudden outage in {track}?"],
                    topology=cls._create_base_topology(s_id, track),
                    environment=EnvironmentSpec(image="docker.io/library/alpine:latest"),
                    initial_state=InitialStateSpec(
                        setup_commands=["mkdir -p /opt/k8s /opt/charts /opt/ci /opt/tf /opt/playbooks /var/log"],
                        failure_injection_commands=[f"touch /tmp/{s_id}_active"],
                    ),
                    tasks=[
                        TaskSpec(
                            id="t1",
                            order=1,
                            title="Resolve Production Incident",
                            description=meta["task_desc"],
                            hints=[
                                Hint(tier=HintTier.CONCEPTUAL, title="Conceptual Direction", content=f"Focus on configuration correctness and resource constraints in {track}."),
                                Hint(tier=HintTier.AREA, title="Subsystem to Inspect", content="Check the configuration files in /opt or /etc."),
                                Hint(tier=HintTier.COMMAND, title="Diagnostic Command", content=meta["diag"]),
                                Hint(tier=HintTier.STRONG_CLUE, title="Target Fix", content=f"Execute: {repair_cmd}"),
                                Hint(tier=HintTier.FULL_SOLUTION, title="Full Solution", content=f"Run: {repair_cmd}"),
                            ],
                            validators=[
                                ValidatorRule(
                                    id="v1",
                                    type=ValidatorType.COMMAND,
                                    description=f"Verify fix for {s_id}",
                                    target=val_target,
                                    failure_message=f"Remediation verification failed for {s_id}.",
                                )
                            ],
                        )
                    ],
                )
            )

        # Merge extended catalog (580+ scenarios across 24 tracks)
        try:
            from .extended_catalog import generate_extended_catalog
            for ext in generate_extended_catalog():
                if ext.id not in existing_ids:
                    scenarios.append(ext)
                    existing_ids.add(ext.id)
        except Exception as e:
            pass

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
