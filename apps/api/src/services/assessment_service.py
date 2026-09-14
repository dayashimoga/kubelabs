"""
Assessment Service: Evaluates quizzes and practical tests across 8 question types.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Question(BaseModel):
    id: str
    track: str
    type: str  # mcq, multi_select, ordering, command_prediction, log_analysis, yaml_fixing, architecture, troubleshooting
    difficulty: str
    prompt: str
    snippet: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Any
    explanation: str


# Catalog of multi-domain assessments
QUESTIONS: List[Question] = [
    Question(
        id="q-linux-01",
        track="linux",
        type="mcq",
        difficulty="intermediate",
        prompt="A filesystem has 40GB of free space reported by `df -h`, yet creating an empty file with `touch test.txt` fails with 'No space left on device'. What is the most probable root cause?",
        options=[
            "The disk partition is mounted in read-only mode",
            "The filesystem has exhausted its available inode allocation",
            "The kernel max file descriptor limit (ulimit -n) has been reached",
            "The reserved block percentage (5%) prevents non-root writes",
        ],
        correct_answer=1,
        explanation="When a filesystem runs out of inodes (IUse% 100% in `df -i`), no new file entries can be created in directory blocks, regardless of remaining raw disk block capacity.",
    ),
    Question(
        id="q-k8s-01",
        track="kubernetes",
        type="log_analysis",
        difficulty="advanced",
        prompt="Analyze the following Kubernetes event log. What is the fundamental root cause of the Pod CrashLoopBackOff?",
        snippet="""Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  4m                 default-scheduler  Successfully assigned default/api-worker to worker-02
  Normal   Pulled     3m55s              kubelet            Container image "redis:7-alpine" already present on machine
  Normal   Created    3m54s              kubelet            Created container redis
  Normal   Started    3m54s              kubelet            Started container redis
  Warning  Unhealthy  3m40s (x3 over 3m) kubelet            Liveness probe failed: HTTP probe failed with statuscode: 404
  Warning  Killing    3m40s              kubelet            Container redis failed liveness probe, will be restarted""",
        options=[
            "The container image binary is missing",
            "The liveness probe was configured with an HTTP GET probe on a Redis server which speaks Redis RESP protocol rather than HTTP",
            "The worker node ran out of memory (OOMKilled)",
            "The kubelet failed to mount the configuration volume",
        ],
        correct_answer=1,
        explanation="Standard Redis does not speak HTTP. Configuring an `httpGet` liveness probe against port 6379 causes the probe to fail with 404 or connection reset, leading kubelet to repeatedly kill the container.",
    ),
    Question(
        id="q-networking-01",
        track="networking",
        type="ordering",
        difficulty="intermediate",
        prompt="Order the TCP three-way handshake and connection teardown sequence chronologically from first to last:",
        options=[
            "Client sends SYN",
            "Server responds with SYN-ACK",
            "Client sends ACK (Connection Established)",
            "Client sends FIN to terminate",
            "Server responds with ACK, then FIN",
            "Client sends final ACK and enters TIME_WAIT",
        ],
        correct_answer=[0, 1, 2, 3, 4, 5],
        explanation="Standard TCP connection establishment proceeds SYN -> SYN-ACK -> ACK. Termination initiates with FIN -> ACK/FIN -> ACK, followed by the 2MSL TIME_WAIT state to ensure delayed segments drain.",
    ),
    Question(
        id="q-yaml-01",
        track="yaml-json",
        type="yaml_fixing",
        difficulty="beginner",
        prompt="Identify the fatal syntax/semantic error in this Kubernetes Deployment fragment:",
        snippet="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: "80" """,
        options=[
            "`containerPort` must be an integer (80), not a quoted string ('80')",
            "The `spec.selector` field is missing, which is mandatory in apps/v1 Deployments",
            "The image version must not have minor tags",
            "The `apiVersion` must be extensions/v1beta1",
        ],
        correct_answer=1,
        explanation="In `apps/v1`, `spec.selector` is mandatory and must match the template metadata labels (`spec.selector.matchLabels.app: web-app`). Omitting `spec.selector` causes the Kubernetes API server to reject the manifest with a validation error.",
    ),
    Question(
        id="q-sre-01",
        track="sre",
        type="multi_select",
        difficulty="advanced",
        prompt="Which of the following techniques directly prevent cascading retry storms during downstream service degradation? (Select all that apply)",
        options=[
            "Exponential backoff with full jitter on client retries",
            "Circuit breakers (e.g. Netflix Hystrix / Envoy outlier detection)",
            "Retrying immediately without delay for up to 50 attempts",
            "Token-bucket client retry budgets (capping retries to <= 20% of normal traffic)",
            "Adaptive concurrency limits (e.g. TCP Vegas style queuing delay limits)",
        ],
        correct_answer=[0, 1, 3, 4],
        explanation="Immediate unjittered retries guarantee cascading overload. Exponential backoff with jitter spreads load, circuit breakers shed failing calls early, retry budgets limit overall retry amplification, and adaptive concurrency limits prevent queuing saturation.",
    ),
]


class AssessmentService:
    def __init__(self):
        self.questions = QUESTIONS

    def get_questions_for_track(self, track: str) -> List[Dict[str, Any]]:
        results = []
        for q in self.questions:
            if q.track == track or track == "all":
                item = q.model_dump()
                # Do not leak correct answer to client
                item.pop("correct_answer")
                item.pop("explanation")
                results.append(item)
        return results

    def grade_submission(self, track: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Grade learner answers and return detailed explanations."""
        score = 0
        total = 0
        details = []

        for q in self.questions:
            if q.track == track or track == "all":
                total += 1
                user_ans = answers.get(q.id)
                is_correct = (user_ans == q.correct_answer)
                if is_correct:
                    score += 1

                details.append({
                    "question_id": q.id,
                    "prompt": q.prompt,
                    "user_answer": user_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": is_correct,
                    "explanation": q.explanation,
                })

        percentage = round((score / total) * 100.0, 1) if total > 0 else 100.0
        return {
            "score": score,
            "total_questions": total,
            "percentage": percentage,
            "passed": percentage >= 75.0,
            "details": details,
        }
