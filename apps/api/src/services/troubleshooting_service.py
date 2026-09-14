"""
Step-by-Step Troubleshooting and Layered Hint Service.
Implements progressive diagnostic guidance:
Symptom -> Evidence -> Hypothesis -> Commands -> Telemetry -> Scope -> Root Cause -> Fix -> Verify -> Prevention
"""

from typing import Any, Dict, List, Optional
from packages.lab_schema import LabSpec, TaskSpec, Hint, HintTier


class TroubleshootingAdvisor:
    """Provides contextual, non-spoiling SRE diagnostic advice."""

    def __init__(self):
        pass

    def get_hint_for_tier(self, task: TaskSpec, requested_tier: int) -> Optional[Hint]:
        """Fetch a specific hint tier (1=Conceptual, 2=Area, 3=Command, 4=Strong Clue, 5=Full Solution)."""
        for h in task.hints:
            if h.tier == requested_tier or h.tier.value == requested_tier:
                return h
        return None

    def answer_diagnostic_question(
        self,
        lab: LabSpec,
        task: TaskSpec,
        question: str,
        recent_command: Optional[str] = None,
        recent_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer canonical learner questions contextually without giving away the full answer."""
        q_lower = question.lower()

        # 1. "What should I inspect next?"
        if "what should i inspect next" in q_lower or "inspect next" in q_lower:
            area_hint = self.get_hint_for_tier(task, 2) or self.get_hint_for_tier(task, 1)
            target_area = area_hint.content if area_hint else "system resource utilization and error logs"
            return {
                "question": question,
                "tier": 2,
                "category": "Inspection Target",
                "guidance": (
                    f"Focus your investigation on: **{target_area}**.\n\n"
                    "Remember the SRE workflow: observe the symptom, check resource limits (CPU, memory, disk, inodes, sockets), "
                    "and review recent error logs before jumping to configuration edits."
                ),
            }

        # 2. "Why did this fail?"
        if "why did this fail" in q_lower or "why did it fail" in q_lower:
            concept_hint = self.get_hint_for_tier(task, 1)
            clue = concept_hint.content if concept_hint else lab.what_why
            return {
                "question": question,
                "tier": 1,
                "category": "Failure Mechanics",
                "guidance": (
                    f"Conceptual direction:\n{clue}\n\n"
                    "Think about the contract between the orchestrator and the underlying runtime. "
                    "Did a health check timeout? Did a cgroup limit terminate the process? Did a network rule drop the SYN packet?"
                ),
            }

        # 3. "Which command should I run?"
        if "which command" in q_lower or "command should i run" in q_lower:
            cmd_hint = self.get_hint_for_tier(task, 3)
            if cmd_hint:
                return {
                    "question": question,
                    "tier": 3,
                    "category": "Diagnostic Command",
                    "guidance": (
                        f"Recommended diagnostic command:\n```bash\n{cmd_hint.content}\n```\n"
                        "Run this command in the terminal to collect authoritative evidence."
                    ),
                }
            return {
                "question": question,
                "tier": 3,
                "category": "Diagnostic Command",
                "guidance": "Try running `dmesg -T`, `journalctl -xe`, `top`, or `kubectl describe` on the target resource.",
            }

        # 4. "Explain this output"
        if "explain this output" in q_lower or "explain output" in q_lower:
            snippet = recent_output[:300] if recent_output else "No output supplied."
            return {
                "question": question,
                "tier": 4,
                "category": "Output Analysis",
                "guidance": (
                    f"Analyzing output snippet:\n```\n{snippet}\n```\n"
                    "Key indicator: look closely at the error codes (e.g. exit 137 = OOMKilled, exit 127 = command not found, "
                    "HTTP 504 = gateway read timeout, IUse% 100% = inode starvation). "
                    "Notice that normal metrics may mask inode or socket exhaustion."
                ),
            }

        # 5. "Show another possible root cause"
        if "another possible root cause" in q_lower or "alternative root cause" in q_lower:
            return {
                "question": question,
                "tier": 4,
                "category": "Differential Diagnosis",
                "guidance": (
                    "Consider differential root causes:\n"
                    "1. Kernel resource exhaustion (ephemeral port exhaustion, file descriptor leaks, arp table overflow).\n"
                    "2. Network layer blocks (security group rules, iptables/eBPF drop, DNS loop).\n"
                    "3. Concurrency starvation (thread pool saturation, connection pool leaks, lock contention).\n"
                    "4. Configuration drift (ConfigMap mounted as read-only volume, incorrect selector labels)."
                ),
            }

        # 6. "Show the correct solution"
        if "correct solution" in q_lower or "show solution" in q_lower:
            sol_hint = self.get_hint_for_tier(task, 5)
            solution = sol_hint.content if sol_hint else "Remediation involves adjusting configuration parameters and verifying system state."
            return {
                "question": question,
                "tier": 5,
                "category": "Full Remediation & Explanation",
                "guidance": (
                    f"### Verified Solution:\n{solution}\n\n"
                    f"**Post-Mortem & Recurrence Prevention:**\n{lab.production_design_notes or 'Automate verification in CI/CD.'}"
                ),
            }

        # General response
        return {
            "question": question,
            "tier": 2,
            "category": "General Advice",
            "guidance": f"Review task '{task.title}': {task.description}. Follow the SRE diagnostic path: Symptom -> Evidence -> Hypothesis -> Verify.",
        }
