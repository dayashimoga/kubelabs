# KubeLabs Learner & User Guide

## 1. Getting Started
KubeLabs is designed for hands-on learning through real failure diagnosis.
Navigate to the web interface at `http://localhost:5173`.

## 2. Navigating the SRE Console
- **Dashboard**: Review your overall engineering mastery percentage, skill radar across 12 disciplines, weak areas with targeted practice recommendations, and recent incident logs.
- **Hands-on Labs**: Filter labs by track (`Linux`, `Docker`, `Kubernetes`, `Terraform`, `Argo CD`, `Istio`, etc.) or difficulty. Click "Start Lab" to spawn an isolated sandbox.
- **Incident Simulator**: Enter the live SEV-1 / SEV-2 Incident War Room. Triage cascading production outages against live telemetry, formulate hypotheses, test them, apply remediation, and generate an SRE post-mortem scorecard.
- **Assessments & Quizzes**: Test your knowledge across 8 question types (MCQ, multi-select, ordering, command prediction, log analysis, YAML fixing, architecture scenarios, and production troubleshooting).

## 3. The 9-Panel Lab Workspace
When you launch a lab, the workspace provides:
1. **Instructions**: Review the objectives, system architecture, and failure symptoms.
2. **Topology**: Explore the interactive visual service graph.
3. **Terminal**: Full interactive PTY terminal session directly connected to your sandbox container.
4. **Editor**: Monaco code editor for editing configuration files (`yaml`, `json`, `sh`).
5. **Telemetry**: Real-time PromQL metrics graphs, streaming log viewers, and OpenTelemetry trace waterfalls.
6. **Diagnostic Assistant**: Ask guided questions:
   - *What should I inspect next?*
   - *Why did this fail?*
   - *Which command should I run?*
   - *Explain this output.*
   - *Show another possible root cause.*
   - *Show the correct solution.*
7. **Layered Hints**: Unlock hints level-by-level (Conceptual $\rightarrow$ Area $\rightarrow$ Command $\rightarrow$ Clue $\rightarrow$ Solution) if stuck.
8. **State Validation**: Click "Run State Validation" to test whether your fix resolved the root cause.
9. **Fullscreen & Resizing**: Toggle fullscreen or resize panels for distraction-free investigation.
