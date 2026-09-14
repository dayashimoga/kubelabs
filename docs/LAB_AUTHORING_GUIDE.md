# KubeLabs Lab Authoring & Contribution Guide

## 1. Directory Conventions
All lab definitions reside in `labs/<track_name>/<lab_id>.yaml`.
Examples:
- `labs/linux/linux-inode-exhaustion.yaml`
- `labs/kubernetes/k8s-crashloop-probe.yaml`
- `labs/istio/istio-circuit-breaker-retry-storm.yaml`

## 2. Mandatory YAML Fields Checklist
Every lab manifest must include:
- [x] `id`: Unique lowercase hyphenated slug (e.g. `docker-bad-dockerfile`)
- [x] `version`: Semantic version string (`1.0.0`)
- [x] `title`: Human-readable descriptive title
- [x] `track`: Target discipline matching curriculum tracks
- [x] `difficulty`: `beginner`, `intermediate`, `advanced`, or `production`
- [x] `estimated_minutes`: Estimated time required
- [x] `validation_status`: `PROVEN`, `SIMULATION-PROVEN`, `IMPLEMENTED-UNPROVEN`, or `HARDWARE/CLOUD-REQUIRED`
- [x] `objectives`: List of bulleted learning goals
- [x] `what_why`: Concise explanation of system impact
- [x] `troubleshooting_workflow`: Ordered diagnostic steps
- [x] `environment`: Container image, CPU/mem quotas, capability drops
- [x] `initial_state`: Initial files staged and failure commands injected
- [x] `tasks`: Ordered tasks with 5-tier layered hints and state validators

## 3. Best Practices for State Validators
- **Never match shell history**: Avoid validating by checking what commands the learner typed. Instead, check the final result on disk, in the process table, or over the network.
- **Ensure idempotent assertions**: Validators should not modify the system while testing.
- **Provide clear failure feedback**: Write actionable `failure_message` strings that guide the user without spoiling the answer.

## 4. Testing Your New Lab
Verify the lab passes Pydantic schema validation:
```bash
pytest tests/unit/test_lab_schemas.py -k <lab_id> -v
```
Test the lab in a real container sandbox:
```bash
python scripts/test_lab_execution.py --lab-id <lab_id>
```
