"""
High-Fidelity Deterministic SRE Simulator for KubeLabs.
Enables instant, realistic simulation of multi-tier cloud architectures,
Kubernetes clusters, telemetry pipelines, and diagnostic terminal interactions.
"""

import os
import re
import json
import time
from typing import Any, Dict, List, Optional, Tuple


class DeterministicSimulator:
    """Stateful simulation of system, cluster, and cloud environments."""

    def __init__(
        self,
        lab_id: str,
        seed_data: Optional[Dict[str, Any]] = None,
        initial_files: Optional[List[Any]] = None,
    ):
        self.lab_id = lab_id
        self.state: Dict[str, Any] = {
            "filesystem": {},
            "processes": [],
            "network_ports": {},
            "k8s": {
                "pods": {},
                "services": {},
                "deployments": {},
                "configmaps": {},
                "pvcs": {},
                "networkpolicies": {},
                "events": [],
            },
            "aws": {
                "vpcs": {},
                "subnets": {},
                "security_groups": {},
                "iam_roles": {},
                "eks_nodes": {},
                "albs": {},
            },
            "telemetry": {
                "metrics": {},
                "logs": [],
                "traces": [],
                "alerts": [],
            },
            "git": {
                "branch": "main",
                "clean": True,
                "commits": [],
            },
            "history": [],
        }
        if seed_data:
            self._apply_seed_data(seed_data)
        if initial_files:
            for f in initial_files:
                f_path = getattr(f, "path", None) or (f.get("path") if isinstance(f, dict) else None)
                f_content = getattr(f, "content", None) or (f.get("content") if isinstance(f, dict) else None)
                if f_path and f_content is not None:
                    self._sync_file_change(f_path, f_content)

    def _sync_file_change(self, path: str, content: str):
        """Reconcile cluster state and filesystem when files are edited or created."""
        self.state["filesystem"][path] = content
        norm_path = path.lstrip("/")
        self.state["filesystem"][norm_path] = content
        self.state["filesystem"][f"/{norm_path}"] = content
        self.state["filesystem"][os.path.basename(path)] = content

        # Reconcile Service selector and endpoints if service.yaml
        if "service.yaml" in path.lower() or "kind: Service" in content:
            name_m = re.search(r"name:\s*([^\s\n]+)", content)
            svc_name = name_m.group(1) if name_m else (list(self.state["k8s"]["services"].keys())[0] if self.state["k8s"]["services"] else "checkout-svc")

            sel_m = re.search(r"selector:\s*\n(?:\s+[^\n]+\n)*?\s+app:\s*([^\s\n]+)", content)
            app_val = sel_m.group(1) if sel_m else None

            if svc_name in self.state["k8s"]["services"]:
                sdata = self.state["k8s"]["services"][svc_name]
                if app_val:
                    sdata["selector"] = f"app={app_val}"
                    matched = False
                    for pod_name, pdata in self.state["k8s"]["pods"].items():
                        p_labels = pdata.get("labels", {})
                        if isinstance(p_labels, dict) and p_labels.get("app") == app_val:
                            matched = True
                            break
                    if matched:
                        sdata["endpoints"] = ["10.244.1.44:8080"]
                    else:
                        sdata["endpoints"] = []

    def _apply_seed_data(self, seed: Dict[str, Any]):
        for section, content in seed.items():
            if section in self.state and isinstance(self.state[section], dict) and isinstance(content, dict):
                self.state[section].update(content)
            else:
                self.state[section] = content

    def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """Process a simulated shell command and return (exit_code, stdout, stderr)."""
        cmd_clean = cmd.strip()
        self.state["history"].append(cmd_clean)

        # 1. Linux storage commands
        if cmd_clean == "df -h":
            return 0, (
                "Filesystem      Size  Used Avail Use% Mounted on\n"
                "/dev/root        20G   14G  5.2G  73% /\n"
                "tmpfs           1.9G     0  1.9G   0% /dev/shm\n"
                "/dev/nvme0n1p1   50G   48G  1.2G  98% /var/log\n"
                "/dev/sdb1       100G   22G   74G  23% /data\n"
            ), ""

        if cmd_clean == "df -i":
            # Check if this lab is linux-inode-exhaustion
            is_inode_exhausted = self.state.get("inode_exhausted", True)
            if is_inode_exhausted:
                return 0, (
                    "Filesystem       Inodes   IUsed   IFree IUse% Mounted on\n"
                    "/dev/root       1310720  421000  889720   33% /\n"
                    "/dev/nvme0n1p1  3276800 3276800       0  100% /var/spool/clientmqueue\n"
                    "/dev/sdb1       6553600  124000 6429600    2% /data\n"
                ), ""
            else:
                return 0, (
                    "Filesystem       Inodes   IUsed   IFree IUse% Mounted on\n"
                    "/dev/root       1310720  421000  889720   33% /\n"
                    "/dev/nvme0n1p1  3276800   45000 3231800    2% /var/spool/clientmqueue\n"
                    "/dev/sdb1       6553600  124000 6429600    2% /data\n"
                ), ""

        if "find /var/spool" in cmd_clean and "-delete" in cmd_clean:
            self.state["inode_exhausted"] = False
            return 0, "", ""

        # 2. Kubernetes commands
        if cmd_clean.startswith("kubectl get pods") or cmd_clean.startswith("kubectl get pod"):
            show_labels = "--show-labels" in cmd_clean
            pods = self.state["k8s"]["pods"]
            if not pods:
                return 0, "No resources found in default namespace.\n", ""
            if show_labels:
                lines = ["NAME                                READY   STATUS             RESTARTS   AGE   LABELS"]
            else:
                lines = ["NAME                                READY   STATUS             RESTARTS   AGE"]
            for pod_name, pdata in pods.items():
                ready = pdata.get("ready", "0/1")
                status = pdata.get("status", "Running")
                restarts = str(pdata.get("restarts", 0))
                age = pdata.get("age", "12m")
                if show_labels:
                    labels_dict = pdata.get("labels", {})
                    if isinstance(labels_dict, dict):
                        labels_str = ",".join(f"{k}={v}" for k, v in labels_dict.items()) or "<none>"
                    else:
                        labels_str = str(labels_dict) if labels_dict else "<none>"
                    lines.append(f"{pod_name:<35} {ready:<7} {status:<18} {restarts:<10} {age:<5} {labels_str}")
                else:
                    lines.append(f"{pod_name:<35} {ready:<7} {status:<18} {restarts:<10} {age}")
            return 0, "\n".join(lines) + "\n", ""

        if cmd_clean.startswith("kubectl describe pod"):
            parts = cmd_clean.split()
            pod_name = parts[3] if len(parts) > 3 else "unknown"
            pod_data = self.state["k8s"]["pods"].get(pod_name, {})
            events = pod_data.get("events", [
                "Warning  FailedMount     2m (x5 over 10m)  kubelet  MountVolume.SetUp failed for volume 'app-config' : configmap 'app-config-v2' not found",
                "Warning  BackOff         1m (x8 over 9m)   kubelet  Back-off restarting failed container",
            ])
            output = f"""Name:             {pod_name}
Namespace:        default
Node:             ip-10-0-3-12.ec2.internal/10.0.3.12
Status:           {pod_data.get('status', 'CrashLoopBackOff')}
IP:               10.244.1.44
Containers:
  app:
    Container ID:   containerd://e98a3b8...
    Image:          registry.internal.corp/checkout-api:v2.1.0
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    137 (OOMKilled)
Events:
  Type     Reason          Age                 From     Message
  ----     ------          ----                ----     -------
"""
            for ev in events:
                output += f"  {ev}\n"
            return 0, output, ""

        if cmd_clean.startswith("kubectl describe svc") or cmd_clean.startswith("kubectl describe service"):
            parts = cmd_clean.split()
            target_svc = parts[3] if len(parts) > 3 and not parts[3].startswith("-") else None
            services = self.state["k8s"]["services"]
            if not target_svc:
                target_svc = list(services.keys())[0] if services else "checkout-svc"
            sdata = services.get(target_svc, {})
            if not sdata and services:
                target_svc, sdata = next(iter(services.items()))

            eps = ",".join(sdata.get("endpoints", [])) or "<none>"
            ports = sdata.get("ports", "80/TCP")
            port_num = ports.split("/")[0] if "/" in ports else "80"
            proto = ports.split("/")[1] if "/" in ports else "TCP"
            cluster_ip = sdata.get("cluster_ip", "10.96.12.44")
            stype = sdata.get("type", "ClusterIP")
            selector = sdata.get("selector", "app=checkout-api-v2")

            output = f"""Name:              {target_svc}
Namespace:         default
Labels:            <none>
Annotations:       <none>
Selector:          {selector}
Type:              {stype}
IP Family Policy:  SingleStack
IP Families:       IPv4
IP:                {cluster_ip}
IPs:               {cluster_ip}
Port:              <unset>  {port_num}/{proto}
TargetPort:        8080/{proto}
Endpoints:         {eps}
Session Affinity:  None
Events:            <none>
"""
            return 0, output, ""

        if cmd_clean.startswith("kubectl describe ep") or cmd_clean.startswith("kubectl describe endpoints"):
            parts = cmd_clean.split()
            target_svc = parts[3] if len(parts) > 3 and not parts[3].startswith("-") else None
            services = self.state["k8s"]["services"]
            if not target_svc:
                target_svc = list(services.keys())[0] if services else "checkout-svc"
            sdata = services.get(target_svc, {})
            eps = ",".join(sdata.get("endpoints", [])) or "<none>"
            if eps != "<none>":
                output = f"""Name:         {target_svc}
Namespace:    default
Labels:       <none>
Annotations:  endpoints.kubernetes.io/last-change-trigger-time: 2026-09-15T03:00:00Z
Subsets:
  Addresses:          {eps}
  NotReadyAddresses:  <none>
  Ports:
    Name     Port  Protocol
    ----     ----  --------
    <unset>  8080  TCP

Events:  <none>
"""
            else:
                output = f"""Name:         {target_svc}
Namespace:    default
Labels:       <none>
Annotations:  <none>
Subsets:
Events:  <none>
"""
            return 0, output, ""

        if cmd_clean.startswith("kubectl get svc") or cmd_clean.startswith("kubectl get services"):
            services = self.state["k8s"]["services"]
            parts = cmd_clean.split()
            target_svc = parts[3] if len(parts) > 3 and not parts[3].startswith("-") else None
            lines = ["NAME              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE"]
            for svc_name, sdata in services.items():
                if target_svc and svc_name != target_svc:
                    continue
                stype = sdata.get("type", "ClusterIP")
                cip = sdata.get("cluster_ip", "10.96.0.12")
                eip = sdata.get("external_ip", "<none>")
                ports = sdata.get("ports", "80/TCP")
                age = sdata.get("age", "1d")
                lines.append(f"{svc_name:<17} {stype:<11} {cip:<16} {eip:<13} {ports:<16} {age}")
            return 0, "\n".join(lines) + "\n", ""

        if cmd_clean.startswith("kubectl get ep") or cmd_clean.startswith("kubectl get endpoints"):
            services = self.state["k8s"]["services"]
            parts = cmd_clean.split()
            target_svc = parts[3] if len(parts) > 3 and not parts[3].startswith("-") else None
            lines = ["NAME              ENDPOINTS                                   AGE"]
            for svc_name, sdata in services.items():
                if target_svc and svc_name != target_svc:
                    continue
                eps = ",".join(sdata.get("endpoints", [])) or "<none>"
                age = sdata.get("age", "1d")
                lines.append(f"{svc_name:<17} {eps:<43} {age}")
            return 0, "\n".join(lines) + "\n", ""

        if cmd_clean.startswith("kubectl apply"):
            for path, content in list(self.state.get("filesystem", {}).items()):
                self._sync_file_change(path, content)
            return 0, "service/checkout-svc configured\n", ""

        # 3. AWS & EKS commands
        if "aws eks describe-cluster" in cmd_clean:
            return 0, json.dumps({
                "cluster": {
                    "name": "prod-useast1-core",
                    "status": "ACTIVE",
                    "version": "1.30",
                    "endpoint": "https://A89BF4.gr7.us-east-1.eks.amazonaws.com",
                    "roleArn": "arn:aws:iam::123456789012:role/eks-cluster-role",
                    "resourcesVpcConfig": {
                        "subnetIds": ["subnet-01234", "subnet-05678"],
                        "securityGroupIds": ["sg-0a1b2c3d"],
                        "clusterSecurityGroupId": ["sg-09876543"],
                    },
                }
            }, indent=2), ""

        # 4. Networking & socket commands
        if cmd_clean in ["netstat -tlpn", "ss -tlpn"]:
            return 0, (
                "Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name\n"
                "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      842/sshd: /usr/sbin\n"
                "tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1024/postgres\n"
                "tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      2341/envoy\n"
                "tcp        0      0 127.0.0.1:9090          0.0.0.0:*               LISTEN      1120/prometheus\n"
            ), ""

        # 5. Generic shell commands and file editing
        if cmd_clean.startswith("echo"):
            return 0, cmd_clean[5:].strip().strip("\"'") + "\n", ""

        if cmd_clean == "whoami":
            return 0, "sre-engineer\n", ""

        if cmd_clean == "pwd":
            return 0, "/home/sre-engineer/workspace\n", ""

        if cmd_clean == "uptime":
            return 0, " 10:04:12 up 42 days,  3:18,  2 users,  load average: 8.42, 6.15, 4.30\n", ""

        if "docker.sock" in cmd_clean or "podman.sock" in cmd_clean:
            return 1, "", "ls: /var/run/docker.sock: No such file or directory\nls: /run/podman/podman.sock: No such file or directory\n"

        if cmd_clean.startswith("sed "):
            match = re.search(r"s/([^/]+)/([^/]+)/([gI]*)", cmd_clean)
            if match:
                old_str, new_str, flags = match.groups()
                file_target = cmd_clean.split()[-1].strip("'\"")
                matched_file = False
                for path, content in list(self.state.get("filesystem", {}).items()):
                    if (
                        path == file_target
                        or path.endswith(file_target)
                        or file_target.endswith(path)
                        or os.path.basename(path) == os.path.basename(file_target)
                    ):
                        updated = content.replace(old_str, new_str)
                        self._sync_file_change(path, updated)
                        matched_file = True
                if matched_file:
                    return 0, "", ""
                return 1, "", f"sed: can't read {file_target}: No such file or directory\n"

        if cmd_clean in ["ls", "ls /workspace", "ls -la", "ls -l /workspace", "ls /home/sre-engineer/workspace", "ls service.yaml", "ls /workspace/service.yaml"]:
            fs_files = list(self.state.get("filesystem", {}).keys())
            basenames = sorted(list(set(os.path.basename(p) for p in fs_files if p))) or ["service.yaml"]
            return 0, "  ".join(basenames) + "\n", ""

        if cmd_clean.startswith("grep "):
            parts = cmd_clean.split()
            pattern = parts[1].strip("'\"")
            target_path = parts[-1] if len(parts) > 2 else ""
            content = ""
            for p, c in self.state.get("filesystem", {}).items():
                if p.endswith(target_path) or target_path.endswith(p) or os.path.basename(p) == os.path.basename(target_path):
                    content = c
                    break
            if content:
                matching_lines = [l for l in content.splitlines() if pattern in l]
                if matching_lines:
                    return 0, "\n".join(matching_lines) + "\n", ""
                return 1, "", ""

        if cmd_clean.startswith("vi ") or cmd_clean.startswith("nano "):
            filename = cmd_clean.split()[-1]
            return 0, f"Tip: Use the Code Editor tab in the workspace to edit {filename} and click 'Save File', or use sed -i in this shell.\n", ""

        if cmd_clean.startswith("cat "):
            target_path = cmd_clean.split(None, 1)[1].strip()
            # 1. Exact match in filesystem
            if target_path in self.state.get("filesystem", {}):
                return 0, self.state["filesystem"][target_path] + "\n", ""
            # 2. Suffix or basename match
            for p, c in self.state.get("filesystem", {}).items():
                if (
                    p.endswith(target_path)
                    or target_path.endswith(p)
                    or os.path.basename(p) == os.path.basename(target_path)
                ):
                    return 0, c + "\n", ""
            if "service.yaml" in target_path:
                svc_name = list(self.state["k8s"]["services"].keys())[0] if self.state["k8s"]["services"] else "checkout-svc"
                sel = self.state["k8s"]["services"].get(svc_name, {}).get("selector", "app=checkout-api-v2")
                app_part = sel.split("=")[1] if "=" in sel else "checkout-api-v2"
                return 0, f"apiVersion: v1\nkind: Service\nmetadata:\n  name: {svc_name}\nspec:\n  selector:\n    app: {app_part}\n", ""
            if "shadow" in target_path:
                return 1, "", f"cat: {target_path}: Permission denied\n"
            return 1, "", f"cat: {target_path}: No such file or directory\n"

        if "print('X'" in cmd_clean or "large_buffer" in cmd_clean:
            return 0, ("X" * 102400) + "\n", ""

        # Default fallback
        return 0, f"Executed: {cmd_clean}\n", ""

    def get_topology(self) -> Dict[str, Any]:
        """Return dynamic architecture graph of nodes, edges, and statuses."""
        return self.state.get("topology", {
            "nodes": [
                {"id": "ingress", "label": "ALB Ingress", "type": "alb", "status": "healthy"},
                {"id": "api-gateway", "label": "API Gateway", "type": "gateway", "status": "healthy"},
                {"id": "order-svc", "label": "Order Service", "type": "service", "status": "degraded"},
                {"id": "payment-svc", "label": "Payment Service", "type": "service", "status": "healthy"},
                {"id": "postgres-db", "label": "PostgreSQL DB", "type": "database", "status": "healthy"},
                {"id": "redis-cache", "label": "Redis Cluster", "type": "cache", "status": "healthy"},
            ],
            "edges": [
                {"source": "ingress", "target": "api-gateway", "protocol": "https", "status": "normal"},
                {"source": "api-gateway", "target": "order-svc", "protocol": "grpc", "status": "slow"},
                {"source": "order-svc", "target": "payment-svc", "protocol": "http", "status": "normal"},
                {"source": "order-svc", "target": "postgres-db", "protocol": "tcp", "status": "normal"},
                {"source": "order-svc", "target": "redis-cache", "protocol": "tcp", "status": "normal"},
            ],
        })

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Return live timeseries metrics (Latency, RPS, Error Rate, CPU, Memory)."""
        now = int(time.time())
        return {
            "timestamp": now,
            "requests_per_second": 1420.5,
            "error_rate_5xx_percent": 18.4,
            "latency_p50_ms": 12.4,
            "latency_p95_ms": 285.0,
            "latency_p99_ms": 1840.2,
            "cpu_utilization_percent": 88.5,
            "memory_usage_mb": 1780.0,
            "active_db_connections": 198,
            "max_db_connections": 200,
        }

    def get_telemetry_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent log stream items."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return [
            {"timestamp": now, "level": "INFO", "service": "api-gateway", "message": "POST /v2/orders 200 14ms"},
            {"timestamp": now, "level": "WARN", "service": "order-svc", "message": "Connection pool acquisition took 1420ms (active=198/200)"},
            {"timestamp": now, "level": "ERROR", "service": "order-svc", "message": "java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms."},
            {"timestamp": now, "level": "ERROR", "service": "api-gateway", "message": "upstream connect error or disconnect/reset before headers. reset reason: connection timeout"},
        ]

    def get_telemetry_traces(self) -> List[Dict[str, Any]]:
        """Return distributed trace spans."""
        return [
            {
                "trace_id": "8f3b2a1c0d4e5f6a",
                "span_id": "span-001",
                "parent_id": None,
                "service": "api-gateway",
                "operation": "POST /checkout",
                "duration_ms": 3050,
                "status": "ERROR",
                "tags": {"http.status_code": 504, "http.method": "POST"},
            },
            {
                "trace_id": "8f3b2a1c0d4e5f6a",
                "span_id": "span-002",
                "parent_id": "span-001",
                "service": "order-svc",
                "operation": "processOrder",
                "duration_ms": 3042,
                "status": "ERROR",
                "tags": {"error": True, "error.type": "SQLTransientConnectionException"},
            },
            {
                "trace_id": "8f3b2a1c0d4e5f6a",
                "span_id": "span-003",
                "parent_id": "span-002",
                "service": "postgres",
                "operation": "hikari.getConnection",
                "duration_ms": 3000,
                "status": "ERROR",
                "tags": {"db.system": "postgresql", "error.message": "connection pool exhausted"},
            },
        ]
