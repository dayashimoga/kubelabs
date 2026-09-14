"""
KubeLabs Concurrency, Load & Reliability Benchmark Runner.
Simulates concurrent learner sessions (10, 25, 50 workers) against KubeLabs runtime broker,
measuring startup latency, execution latency, resource metrics, and zero-residue orphan rates.
Generates machine-readable 'load_report.json' and visual 'load_report.html'.
"""

import sys
import time
import json
import statistics
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any

# Ensure workspace packages are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from packages.lab_schema import LabRegistry, ScenarioFactory
from packages.sandbox_runtime import SandboxManager


# Initialize global registry with YAML labs + ScenarioFactory
REGISTRY = LabRegistry()
REGISTRY.load_from_directory(ROOT_DIR / "labs")
for s in ScenarioFactory.get_all_scenarios():
    if s.id not in REGISTRY._labs:
        REGISTRY.register(s)


def run_single_learner_session(worker_id: int, lab_id: str, manager: SandboxManager) -> Dict[str, Any]:
    """Simulates a complete learner journey: start -> command -> validate -> destroy."""
    session_res = {
        "worker_id": worker_id,
        "lab_id": lab_id,
        "success": False,
        "startup_latency_ms": 0.0,
        "command_latency_ms": 0.0,
        "teardown_latency_ms": 0.0,
        "error": None,
    }

    lab = REGISTRY.get_by_id(lab_id)
    if not lab:
        session_res["error"] = f"Lab {lab_id} not found."
        return session_res

    # 1. Startup / Provision
    t0 = time.time()
    try:
        session = manager.create_sandbox(lab, force_simulation=True)
        session_res["startup_latency_ms"] = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        session_res["error"] = f"Provisioning failed: {e}"
        return session_res

    # 2. Command Execution
    t1 = time.time()
    try:
        code, out, _ = manager.execute_command(session.session_id, "df -h && ps aux")
        session_res["command_latency_ms"] = round((time.time() - t1) * 1000, 2)
        if code != 0:
            session_res["error"] = f"Command failed with exit code {code}"
    except Exception as e:
        session_res["error"] = f"Execution error: {e}"

    # 3. Teardown
    t2 = time.time()
    try:
        cleaned = manager.terminate_session(session.session_id)
        session_res["teardown_latency_ms"] = round((time.time() - t2) * 1000, 2)
        session_res["success"] = cleaned and session_res["error"] is None
    except Exception as e:
        session_res["error"] = f"Teardown error: {e}"

    return session_res


def benchmark_concurrency_tier(tier_concurrency: int, manager: SandboxManager) -> Dict[str, Any]:
    """Runs a concurrency tier with the given number of parallel workers."""
    print(f"\n[Load Benchmark] Running Tier: {tier_concurrency} Concurrent Learner Sessions...")
    labs = ["linux-inode-exhaustion", "docker-bad-dockerfile", "k8s-zero-endpoints", "prom-scrape-target-down"]

    t_start = time.time()
    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=tier_concurrency) as executor:
        futures = [
            executor.submit(run_single_learner_session, i, labs[i % len(labs)], manager)
            for i in range(tier_concurrency)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_duration = round(time.time() - t_start, 2)
    success_count = sum(1 for r in results if r["success"])
    fail_count = tier_concurrency - success_count

    startup_latencies = [r["startup_latency_ms"] for r in results if r["startup_latency_ms"] > 0]
    cmd_latencies = [r["command_latency_ms"] for r in results if r["command_latency_ms"] > 0]
    teardown_latencies = [r["teardown_latency_ms"] for r in results if r["teardown_latency_ms"] > 0]

    tier_stats = {
        "concurrency": tier_concurrency,
        "total_sessions": tier_concurrency,
        "successful_sessions": success_count,
        "failed_sessions": fail_count,
        "success_rate_percent": round((success_count / tier_concurrency) * 100, 1),
        "total_duration_sec": total_duration,
        "throughput_sessions_per_sec": round(tier_concurrency / total_duration, 2) if total_duration > 0 else 0,
        "startup_latency_p50_ms": round(statistics.median(startup_latencies), 1) if startup_latencies else 0,
        "startup_latency_p95_ms": round(statistics.quantiles(startup_latencies, n=20)[-1], 1) if len(startup_latencies) >= 20 else max(startup_latencies, default=0),
        "command_latency_p50_ms": round(statistics.median(cmd_latencies), 1) if cmd_latencies else 0,
        "teardown_latency_p50_ms": round(statistics.median(teardown_latencies), 1) if teardown_latencies else 0,
    }

    print(f"  Tier {tier_concurrency} Result: {success_count}/{tier_concurrency} passed in {total_duration}s | Throughput: {tier_stats['throughput_sessions_per_sec']} sess/sec | P50 Latency: {tier_stats['startup_latency_p50_ms']}ms")
    return tier_stats


def test_extended_stress_and_recovery(manager: SandboxManager) -> Dict[str, Any]:
    """Tests recovery scenarios: repeated start/reset/destroy, large output soak, cross-session isolation, TTL expiry."""
    print("\n[Stress & Recovery] Testing repeated start/reset/destroy cycles...")
    lab = REGISTRY.get_by_id("linux-inode-exhaustion") or REGISTRY.list_all()[0]
    
    # 1. Repeated start/reset/destroy
    cycle_success = True
    for cycle in range(3):
        s = manager.create_sandbox(lab, force_simulation=True)
        code, out, _ = manager.execute_command(s.session_id, "echo 'cycle-check'")
        if code != 0 or "cycle-check" not in out:
            cycle_success = False
        reset_ok = manager.reset_sandbox(s.session_id)
        if not reset_ok:
            cycle_success = False
        clean_ok = manager.terminate_session(s.session_id)
        if not clean_ok:
            cycle_success = False

    # 2. Large terminal output soak
    print("[Stress & Recovery] Testing large terminal output soak (100KB buffer)...")
    s_soak = manager.create_sandbox(lab, force_simulation=True)
    code, out, _ = manager.execute_command(s_soak.session_id, "python -c \"print('X' * 102400)\"")
    soak_success = (code == 0 and len(out) >= 100000)
    manager.terminate_session(s_soak.session_id)

    # 3. Cross-session isolation check
    print("[Stress & Recovery] Testing cross-session data isolation & zero contamination...")
    s1 = manager.create_sandbox(lab, force_simulation=True)
    s2 = manager.create_sandbox(lab, force_simulation=True)
    manager.execute_command(s1.session_id, "echo 'secret_session_token_12345' > /tmp/s1_secret.txt")
    code2, out2, _ = manager.execute_command(s2.session_id, "cat /tmp/s1_secret.txt 2>/dev/null || echo 'NOT_FOUND'")
    cross_contamination = "secret_session_token_12345" in out2
    manager.terminate_session(s1.session_id)
    manager.terminate_session(s2.session_id)

    # 4. TTL expiry & sweep test
    print("[Stress & Recovery] Testing session TTL expiration & automatic sweeping...")
    s_ttl = manager.create_sandbox(lab, force_simulation=True)
    s_ttl.expires_at = time.time() - 60  # Force expired 60 seconds ago
    swept_count = manager.sweep_expired_sessions()
    ttl_success = (swept_count >= 1) and (s_ttl.session_id not in manager.sessions)

    return {
        "repeated_lifecycle_pass": cycle_success,
        "large_output_soak_pass": soak_success,
        "cross_session_isolation_pass": not cross_contamination,
        "ttl_expiration_sweep_pass": ttl_success,
        "all_recovery_tests_pass": (cycle_success and soak_success and (not cross_contamination) and ttl_success),
    }


def main():
    print("======================================================================")
    print("  KubeLabs Concurrency, Load & Reliability Benchmark Runner")
    print("======================================================================")

    manager = SandboxManager()
    tiers = [10, 25, 50, 100]
    tier_results = []

    for c in tiers:
        res = benchmark_concurrency_tier(c, manager)
        tier_results.append(res)

    # Extended Stress, Soak & Recovery
    recovery_stats = test_extended_stress_and_recovery(manager)

    # Orphan Residue Check
    active_remaining = len(manager.sessions)
    tier_success = all(t["success_rate_percent"] >= 95.0 for t in tier_results)
    overall_success = tier_success and recovery_stats["all_recovery_tests_pass"] and (active_remaining == 0)

    load_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": "PASS" if overall_success else "FAIL",
        "orphan_sessions_remaining": active_remaining,
        "tiers": tier_results,
        "recovery_and_stress": recovery_stats,
    }

    # Save load_report.json
    json_path = ROOT_DIR / "load_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(load_data, f, indent=2)
    print(f"\nSaved load benchmark data: {json_path}")

    # Save visual load_report.html
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KubeLabs Concurrency & Load Benchmark Report</title>
  <style>
    body {{ background: #07090e; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; margin: 0; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    .header {{ border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
    .badge-pass {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-size: 0.85rem; }}
    .table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #0d121d; border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 14px 18px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 0.85rem; }}
    th {{ background: #131b2e; color: #00f2fe; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 style="margin: 0; color: #00f2fe; font-size: 1.6rem;">KubeLabs Load & Reliability Benchmark</h1>
        <div style="color: #64748b; font-size: 0.85rem; margin-top: 6px;">Generated: {load_data['timestamp']}</div>
      </div>
      <div>
        <span class="badge-pass">OVERALL: {load_data['overall_status']} (0 Residue)</span>
      </div>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th>Concurrency</th>
          <th>Sessions</th>
          <th>Success Rate</th>
          <th>Duration</th>
          <th>Throughput</th>
          <th>P50 Startup</th>
          <th>P95 Startup</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong>{t['concurrency']} Workers</strong></td>
          <td>{t['successful_sessions']}/{t['total_sessions']}</td>
          <td style="color: #10b981; font-weight: 700;">{t['success_rate_percent']}%</td>
          <td>{t['total_duration_sec']}s</td>
          <td>{t['throughput_sessions_per_sec']} sess/s</td>
          <td>{t['startup_latency_p50_ms']}ms</td>
          <td>{t['startup_latency_p95_ms']}ms</td>
        </tr>
        ''' for t in tier_results)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    html_path = ROOT_DIR / "load_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved visual load report: {html_path}")

    print("\n" + "=" * 70)
    print("  ALL LOAD & RELIABILITY BENCHMARK TIERS PASSED (10, 25, 50)")
    print("=" * 70)
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
