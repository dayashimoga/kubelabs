"""
REST API endpoints for User Dashboard, Mastery Radar, and Recommendations.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard_summary():
    """Returns technology mastery, weak areas, troubleshooting score, and recommended next topics."""
    return {
        "user": {
            "username": "sre-engineer",
            "role": "Site Reliability Engineer",
            "overall_mastery": 74,
            "troubleshooting_rating": "Senior SRE (Level 4)",
            "labs_completed": 18,
            "incidents_resolved": 7,
            "average_incident_score": 88,
        },
        "radar": [
            {"technology": "Linux", "mastery": 85, "labs_count": 12},
            {"technology": "Networking", "mastery": 78, "labs_count": 8},
            {"technology": "Docker", "mastery": 90, "labs_count": 10},
            {"technology": "Kubernetes", "mastery": 82, "labs_count": 16},
            {"technology": "Helm/Kustomize", "mastery": 75, "labs_count": 6},
            {"technology": "Terraform", "mastery": 70, "labs_count": 7},
            {"technology": "Ansible", "mastery": 68, "labs_count": 5},
            {"technology": "GitOps/ArgoCD", "mastery": 80, "labs_count": 6},
            {"technology": "Observability", "mastery": 72, "labs_count": 8},
            {"technology": "Service Mesh", "mastery": 65, "labs_count": 5},
            {"technology": "AWS / EKS", "mastery": 74, "labs_count": 9},
            {"technology": "Incident Response", "mastery": 84, "labs_count": 12},
        ],
        "weak_areas": [
            {
                "topic": "Istio Circuit Breaking & Retry Budgets",
                "track": "istio",
                "severity": "Medium",
                "recommendation": "Complete Lab: Istio Cascading Retry Storm Mitigation",
            },
            {
                "topic": "AWS VPC CNI IP Calculation & ENI Allocation",
                "track": "aws-eks",
                "severity": "High",
                "recommendation": "Complete Lab: AWS EKS VPC CNI IP Exhaustion Remediation",
            },
            {
                "topic": "PostgreSQL Connection Pool Mathematical Limits",
                "track": "sre-incidents",
                "severity": "High",
                "recommendation": "Complete Scenario: PostgreSQL Max Connection Saturation",
            },
        ],
        "recent_activity": [
            {"type": "incident", "id": "checkout-latency-spike", "title": "Checkout Latency Spike", "score": 92, "timestamp": "2 hours ago"},
            {"type": "lab", "id": "linux-inode-exhaustion", "title": "Linux Filesystem Inode Exhaustion", "score": 100, "timestamp": "1 day ago"},
            {"type": "assessment", "id": "q-k8s-01", "title": "Kubernetes Probe Diagnostic", "score": 100, "timestamp": "2 days ago"},
        ],
        "recommended_next": {
            "type": "incident",
            "id": "coredns-intermittent-resolution-failure",
            "title": "Intermittent Cluster-Wide DNS Resolution Timeouts",
            "track": "kubernetes",
            "reason": "Reinforces CoreDNS scaling, ndots:5 query amplification, and NodeLocal DNSCache architecture.",
        },
    }
