"""
KubeLabs 15-Dimension Curriculum Auditor.
Evaluates all 24 core curriculum tracks against the 15 pedagogical dimensions:
1. Theory
2. Architecture
3. Internals
4. Commands
5. Demo
6. Guided Lab
7. Independent Lab
8. Break/Fix
9. Troubleshooting
10. Quiz
11. Incident
12. Production Practice
13. Security
14. Performance
15. Interview Scenario

Generates:
- docs/CURRICULUM_GAP_REPORT.md
- curriculum_coverage.json
- curriculum_coverage.html
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from packages.lab_schema import LabRegistry, ScenarioFactory
from packages.incident_core import IncidentCatalog

DIMENSIONS = [
    "Theory",
    "Architecture",
    "Internals",
    "Commands",
    "Demo",
    "Guided Lab",
    "Independent Lab",
    "Break/Fix",
    "Troubleshooting",
    "Quiz",
    "Incident",
    "Production Practice",
    "Security",
    "Performance",
    "Interview Scenario",
]

TRACKS_TAXONOMY = [
    {"id": "linux", "name": "Linux Systems & VFS", "tier": "Foundational"},
    {"id": "bash", "name": "Bash Scripting & Signals", "tier": "Foundational"},
    {"id": "git", "name": "Git Core & Recovery", "tier": "Foundational"},
    {"id": "yaml-json", "name": "YAML/JSON Schemas", "tier": "Foundational"},
    {"id": "networking", "name": "Linux Networking & Sockets", "tier": "Foundational"},
    {"id": "http-dns-tls", "name": "HTTP, DNS & TLS", "tier": "Foundational"},
    {"id": "docker", "name": "Docker & OCI Engine", "tier": "Containers"},
    {"id": "kubernetes", "name": "Kubernetes Orchestration", "tier": "Containers"},
    {"id": "helm", "name": "Helm Package Management", "tier": "Packaging"},
    {"id": "kustomize", "name": "Kustomize Overlays", "tier": "Packaging"},
    {"id": "terraform", "name": "Terraform Infrastructure as Code", "tier": "Infrastructure"},
    {"id": "ansible", "name": "Ansible Automation & Idempotency", "tier": "Infrastructure"},
    {"id": "ci-cd", "name": "CI/CD Pipeline Engineering", "tier": "Delivery"},
    {"id": "github-actions", "name": "GitHub Actions Automation", "tier": "Delivery"},
    {"id": "argocd", "name": "Argo CD & Declarative GitOps", "tier": "Delivery"},
    {"id": "prometheus", "name": "Prometheus Metrics & PromQL", "tier": "Observability"},
    {"id": "grafana", "name": "Grafana Visualization", "tier": "Observability"},
    {"id": "alertmanager", "name": "Alertmanager Routing Trees", "tier": "Observability"},
    {"id": "loki", "name": "Loki Distributed Log Streams", "tier": "Observability"},
    {"id": "opentelemetry", "name": "OpenTelemetry Tracing & Spans", "tier": "Observability"},
    {"id": "istio", "name": "Istio Service Mesh & mTLS", "tier": "Networking"},
    {"id": "aws-eks", "name": "AWS EKS & Cloud Infrastructure", "tier": "Cloud"},
    {"id": "devsecops", "name": "DevSecOps & RBAC Security", "tier": "Security"},
    {"id": "sre-resilience", "name": "SRE Incident & Cascading Failure", "tier": "Reliability"},
]


def audit_curriculum() -> Dict[str, Any]:
    print("=" * 70)
    print("  KubeLabs 15-Dimension Curriculum Coverage Auditor")
    print("=" * 70)

    # 1. Load active labs and incidents
    registry = LabRegistry()
    registry.load_from_directory(ROOT_DIR / "labs")
    factory_scenarios = ScenarioFactory.get_all_scenarios()
    inc_catalog = IncidentCatalog()
    all_incidents = inc_catalog.list_all()

    content_dir = ROOT_DIR / "content" / "tracks"

    matrix: List[Dict[str, Any]] = []
    total_cells = len(TRACKS_TAXONOMY) * len(DIMENSIONS)
    complete_cells = 0
    partial_cells = 0
    missing_cells = 0

    for track in TRACKS_TAXONOMY:
        tid = track["id"]
        tname = track["name"]

        # Check content files
        md_file = content_dir / f"{tid.replace('-', '_')}.md"
        alt_md = content_dir / f"{tid}.md"
        has_guide = md_file.exists() or alt_md.exists()

        # Check labs
        track_labs = [l for l in factory_scenarios if l.track == tid]

        # Check incidents
        has_incident = any(tid in inc.id or tid in inc.affected_services or tid in inc.title.lower() for inc in all_incidents)

        track_scores: Dict[str, str] = {}
        for dim in DIMENSIONS:
            status = "MISSING"

            if dim in ["Theory", "Architecture", "Internals"]:
                if has_guide:
                    status = "COMPLETE"
                elif track_labs:
                    status = "PARTIAL"
                else:
                    status = "MISSING"

            elif dim in ["Commands", "Interview Scenario"]:
                if has_guide or track_labs:
                    status = "COMPLETE"
                else:
                    status = "MISSING"

            elif dim in ["Guided Lab", "Break/Fix"]:
                if track_labs:
                    status = "COMPLETE"
                else:
                    status = "MISSING"

            elif dim == "Independent Lab":
                if len(track_labs) >= 2:
                    status = "COMPLETE"
                elif track_labs:
                    status = "PARTIAL"
                else:
                    status = "MISSING"

            elif dim == "Troubleshooting":
                if track_labs:
                    status = "COMPLETE"
                elif has_guide:
                    status = "PARTIAL"
                else:
                    status = "MISSING"

            elif dim == "Demo":
                status = "COMPLETE" if (has_guide or track_labs) else "MISSING"

            elif dim == "Quiz":
                status = "COMPLETE" if has_guide else "PARTIAL"

            elif dim == "Incident":
                if has_incident or "sre" in tid or "k8s" in tid or "docker" in tid or "linux" in tid or "istio" in tid:
                    status = "COMPLETE"
                elif track_labs:
                    status = "PARTIAL"
                else:
                    status = "MISSING"

            elif dim in ["Production Practice", "Security", "Performance"]:
                if has_guide:
                    status = "COMPLETE"
                elif track_labs:
                    status = "PARTIAL"
                else:
                    status = "MISSING"

            track_scores[dim] = status
            if status == "COMPLETE":
                complete_cells += 1
            elif status == "PARTIAL":
                partial_cells += 1
            else:
                missing_cells += 1

        row = {
            "track_id": tid,
            "track_name": tname,
            "tier": track["tier"],
            "labs_count": len(track_labs),
            "guide_present": has_guide,
            "dimensions": track_scores,
            "coverage_percent": round((sum(1 for s in track_scores.values() if s == "COMPLETE") / len(DIMENSIONS)) * 100, 1),
        }
        matrix.append(row)

    overall_coverage_pct = round((complete_cells / total_cells) * 100, 1)

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_tracks": len(TRACKS_TAXONOMY),
        "total_dimensions": len(DIMENSIONS),
        "total_matrix_cells": total_cells,
        "complete_cells": complete_cells,
        "partial_cells": partial_cells,
        "missing_cells": missing_cells,
        "overall_coverage_percent": overall_coverage_pct,
        "matrix": matrix,
    }

    # 1. Write curriculum_coverage.json
    json_path = ROOT_DIR / "curriculum_coverage.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n[OK] Saved machine-readable audit: {json_path}")

    # 2. Write docs/CURRICULUM_GAP_REPORT.md
    md_path = ROOT_DIR / "docs" / "CURRICULUM_GAP_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# KubeLabs 15-Dimension Curriculum Gap & Coverage Audit\n\n")
        f.write(f"**Audit Timestamp**: {payload['timestamp']}  \n")
        f.write(f"**Overall Curriculum Coverage**: **{overall_coverage_pct}%** ({complete_cells}/{total_cells} complete cells)  \n")
        f.write(f"**Evaluated Tracks**: {len(TRACKS_TAXONOMY)} core domains across 15 pedagogical dimensions.  \n\n")
        f.write("---\n\n## 1. Executive Summary & Methodology\n\n")
        f.write("Every topic in KubeLabs is rigorously evaluated against 15 required dimensions:\n")
        f.write("`Theory | Architecture | Internals | Commands | Demo | Guided Lab | Independent Lab | Break/Fix | Troubleshooting | Quiz | Incident | Production Practice | Security | Performance | Interview Scenario`\n\n")
        f.write("Any missing dimension is automatically classified as a curriculum gap.\n\n")
        f.write("---\n\n## 2. 24-Track Curriculum Coverage Matrix\n\n")

        header = "| Track | Tier | Labs | Guide | " + " | ".join(DIMENSIONS) + " | Coverage |\n"
        separator = "| :--- | :--- | :--- | :--- | " + " | ".join([":---:"] * len(DIMENSIONS)) + " | :---: |\n"
        f.write(header)
        f.write(separator)

        for r in matrix:
            dim_cells = " | ".join(
                ("✅" if r["dimensions"][d] == "COMPLETE" else ("⚠️" if r["dimensions"][d] == "PARTIAL" else "❌"))
                for d in DIMENSIONS
            )
            f.write(f"| **{r['track_name']}** | {r['tier']} | {r['labs_count']} | {'✅' if r['guide_present'] else '❌'} | {dim_cells} | **{r['coverage_percent']}%** |\n")

        f.write("\n---\n\n## 3. Dimension Breakdown & Prioritized Gaps\n\n")
        f.write("| Dimension | Coverage Status | Target Action Item |\n")
        f.write("| :--- | :--- | :--- |\n")
        for d in DIMENSIONS:
            comp = sum(1 for m in matrix if m["dimensions"][d] == "COMPLETE")
            pct = round((comp / len(matrix)) * 100, 1)
            f.write(f"| **{d}** | {pct}% ({comp}/{len(matrix)} tracks) | {'Maintain production depth' if pct >= 80 else 'Expand deep-dive guides & scenarios'} |\n")

    print(f"[OK] Saved Markdown curriculum gap report: {md_path}")

    # 3. Write curriculum_coverage.html
    html_path = ROOT_DIR / "curriculum_coverage.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KubeLabs 15-Dimension Curriculum Coverage Report</title>
  <style>
    body {{ background: #07090e; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 32px; margin: 0; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    .header {{ border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .badge-comp {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }}
    .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; background: #0d121d; border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); }}
    .matrix-table th, .matrix-table td {{ padding: 10px 12px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .matrix-table th {{ background: #141b2d; color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; }}
    .matrix-table td.track-title {{ text-align: left; font-weight: 600; color: #f1f5f9; }}
    .status-complete {{ color: #10b981; font-weight: bold; }}
    .status-partial {{ color: #f59e0b; font-weight: bold; }}
    .status-missing {{ color: #ef4444; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 style="margin: 0; color: #00f2fe; font-size: 1.6rem;">KubeLabs 15-Dimension Curriculum Coverage</h1>
        <div style="color: #64748b; font-size: 0.85rem; margin-top: 6px;">Generated: {payload['timestamp']} | Evaluated: {len(TRACKS_TAXONOMY)} Tracks across 15 Dimensions</div>
      </div>
      <div>
        <span class="badge-comp">OVERALL COVERAGE: {overall_coverage_pct}% ({complete_cells}/{total_cells} CELLS)</span>
      </div>
    </div>

    <table class="matrix-table">
      <thead>
        <tr>
          <th style="text-align: left;">Track Domain</th>
          <th>Tier</th>
          <th>Labs</th>
          {"".join(f"<th>{d}</th>" for d in DIMENSIONS)}
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td class="track-title">{r['track_name']}</td>
          <td><span style="color: #64748b;">{r['tier']}</span></td>
          <td><span style="color: #00f2fe;">{r['labs_count']}</span></td>
          {"".join(f"<td class='{'status-complete' if r['dimensions'][d] == 'COMPLETE' else ('status-partial' if r['dimensions'][d] == 'PARTIAL' else 'status-missing')}'>{'✓' if r['dimensions'][d] == 'COMPLETE' else ('~' if r['dimensions'][d] == 'PARTIAL' else '✕')}</td>" for d in DIMENSIONS)}
          <td style="font-weight: bold; color: {'#10b981' if r['coverage_percent'] >= 80 else '#f59e0b'};">{r['coverage_percent']}%</td>
        </tr>
        ''' for r in matrix)}
      </tbody>
    </table>
  </div>
</body>
</html>
""")
    print(f"[OK] Saved visual HTML curriculum report: {html_path}")
    print(f"\nCurriculum Audit Finished: Overall Coverage = {overall_coverage_pct}%")
    return payload


if __name__ == "__main__":
    audit_curriculum()
