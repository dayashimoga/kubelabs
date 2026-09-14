# KubeLabs Operational Runbook & Day-2 Management

## 1. Routine Maintenance Workflows

### 1.1 Reloading Labs Without Restarting Backend
When new lab YAML manifests are committed to `labs/`:
```bash
curl -X POST http://localhost:8000/api/v1/labs/reload
```
The `LabRegistry` rescans the directory and atomically updates in-memory indexes without terminating active sessions.

### 1.2 Backing Up Learner Progress Database
```bash
# SQLite backup
sqlite3 kubelabs.db ".backup 'backups/kubelabs_$(date +%Y%m%d).db'"

# PostgreSQL backup
pg_dump -U kubelabs_user -h postgres-db kubelabs_prod > backups/backup_$(date +%Y%m%d).sql
```

## 2. Emergency Outage Runbooks

### 2.1 Host Container Table Exhaustion
- **Trigger Alert**: `PodmanContainerLimitReached` (> 150 active containers on single host).
- **Remediation**:
  1. Trigger immediate emergency TTL sweep:
     `podman rm -f $(podman ps -aq --filter "label=kubelabs.sandbox_id")`
  2. Scale worker node group or restart podman system service.

### 2.2 Corrupted Lab Spec in Production
- **Symptom**: `500 Internal Server Error` when opening `/labs/broken-lab-id`.
- **Remediation**:
  1. Inspect registry logs for `ValidationError`.
  2. Run `pytest tests/unit/test_lab_schemas.py` to identify YAML syntax or typing violations.
  3. Revert git commit and trigger lab reload.
