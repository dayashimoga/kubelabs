"""
Scenario Injector: Dynamically injects and fixes real-world SRE and DevOps failures.
Decouples base environment creation from failure state generation.
"""

from typing import Dict, Any, Tuple, Optional
import shlex


class ScenarioInjector:
    """Injects, tests, and repairs realistic failure modes in container or simulation sandboxes."""

    FAULT_CATALOG = {
        "linux_inode_exhaustion": {
            "inject": (
                "mkdir -p /var/spool/mail_queue && "
                "python3 -c \"import os; [open(f'/var/spool/mail_queue/msg_{i}.lock', 'w').close() for i in range(50000)]\" || "
                "touch /tmp/inode_exhaustion_triggered"
            ),
            "repair": "rm -rf /var/spool/mail_queue/*.lock /tmp/inode_exhaustion_triggered",
            "verify": "test -f /tmp/inode_exhaustion_triggered || ls -1 /var/spool/mail_queue/*.lock 2>/dev/null | head -n 1",
        },
        "linux_disk_full": {
            "inject": "dd if=/dev/zero of=/var/log/app_audit.log bs=1M count=100 2>/dev/null || touch /tmp/disk_full_active",
            "repair": "truncate -s 0 /var/log/app_audit.log && rm -f /tmp/disk_full_active",
            "verify": "test -f /tmp/disk_full_active || test -s /var/log/app_audit.log",
        },
        "linux_dns_failure": {
            "inject": "echo 'nameserver 198.51.100.254' > /etc/resolv.conf",
            "repair": "echo 'nameserver 1.1.1.1\nnameserver 8.8.8.8' > /etc/resolv.conf",
            "verify": "grep -q '198.51.100.254' /etc/resolv.conf",
        },
        "linux_zombie_process": {
            "inject": "python3 -c \"import os, time; pid = os.fork(); pid == 0 and os._exit(0); time.sleep(86400)\" &",
            "repair": "pkill -f 'import os, time; pid = os.fork'",
            "verify": "ps aux | grep -i '[Zz]'",
        },
        "linux_port_conflict": {
            "inject": "python3 -c \"import socket, time; s = socket.socket(); s.bind(('0.0.0.0', 8080)); s.listen(1); time.sleep(86400)\" &",
            "repair": "pkill -f 's.bind((\\'0.0.0.0\\', 8080))'",
            "verify": "netstat -tuln 2>/dev/null | grep -q 8080 || ss -tuln 2>/dev/null | grep -q 8080",
        },
        "k8s_zero_endpoints": {
            "inject": (
                "kubectl apply -f - <<'EOF'\n"
                "apiVersion: v1\nkind: Service\nmetadata:\n  name: payment-svc\nspec:\n"
                "  selector:\n    app: payment-api-v2\n  ports:\n  - port: 80\n    targetPort: 8080\n"
                "EOF"
            ),
            "repair": (
                "kubectl apply -f - <<'EOF'\n"
                "apiVersion: v1\nkind: Service\nmetadata:\n  name: payment-svc\nspec:\n"
                "  selector:\n    app: payment-service\n  ports:\n  - port: 80\n    targetPort: 8080\n"
                "EOF"
            ),
            "verify": "kubectl get endpoints payment-svc -o jsonpath='{.subsets}' | grep -q 'addresses'",
        },
        "k8s_crashloop_probe": {
            "inject": "sed -i 's|port: 8080|port: 9999|g' /etc/kubernetes/manifests/web-app.yaml 2>/dev/null || touch /tmp/k8s_crashloop_active",
            "repair": "sed -i 's|port: 9999|port: 8080|g' /etc/kubernetes/manifests/web-app.yaml 2>/dev/null && rm -f /tmp/k8s_crashloop_active",
            "verify": "grep -q '9999' /etc/kubernetes/manifests/web-app.yaml 2>/dev/null || test -f /tmp/k8s_crashloop_active",
        },
        "prometheus_cardinality_explosion": {
            "inject": "python3 -c \"import os; open('/tmp/high_cardinality.flag', 'w').write('USER_SESSION_ID_RANDOM_UUID')\"",
            "repair": "rm -f /tmp/high_cardinality.flag && sed -i '/user_session_id/d' /etc/prometheus/recording_rules.yml 2>/dev/null || true",
            "verify": "test -f /tmp/high_cardinality.flag",
        },
        "istio_mtls_denial": {
            "inject": "touch /tmp/istio_mtls_strict_mismatch.flag",
            "repair": "rm -f /tmp/istio_mtls_strict_mismatch.flag",
            "verify": "test -f /tmp/istio_mtls_strict_mismatch.flag",
        },
    }

    @classmethod
    def list_available_faults(cls) -> Dict[str, Dict[str, str]]:
        return cls.FAULT_CATALOG

    @classmethod
    def inject(cls, exec_fn, fault_name: str) -> Tuple[bool, str]:
        """Run the injection command using the provided execution function."""
        if fault_name not in cls.FAULT_CATALOG:
            return False, f"Unknown fault scenario: {fault_name}"
        cmd = cls.FAULT_CATALOG[fault_name]["inject"]
        code, out, err = exec_fn(cmd)
        if code == 0:
            return True, f"Fault {fault_name} successfully injected."
        return False, f"Failed to inject fault: {err or out}"

    @classmethod
    def repair(cls, exec_fn, fault_name: str) -> Tuple[bool, str]:
        """Apply repair command using the provided execution function."""
        if fault_name not in cls.FAULT_CATALOG:
            return False, f"Unknown fault scenario: {fault_name}"
        cmd = cls.FAULT_CATALOG[fault_name]["repair"]
        code, out, err = exec_fn(cmd)
        if code == 0:
            return True, f"Fault {fault_name} repaired."
        return False, f"Failed to repair fault: {err or out}"

    @classmethod
    def is_fault_active(cls, exec_fn, fault_name: str) -> bool:
        """Verify whether the fault is still active."""
        if fault_name not in cls.FAULT_CATALOG:
            return False
        cmd = cls.FAULT_CATALOG[fault_name]["verify"]
        code, _, _ = exec_fn(cmd)
        return code == 0
