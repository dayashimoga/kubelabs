import React, { useState } from 'react';
import { Search, Filter, AlertTriangle, Terminal, Play, CheckCircle, Tag, Layers, Cpu, Compass } from 'lucide-react';

interface IssueItem {
  id: string;
  symptom: string;
  technology: string;
  subsystem: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced' | 'Production';
  runtime: 'REAL' | 'MULTI-CONTAINER' | 'KUBERNETES' | 'SIMULATED';
  observableEvidence: string;
  suggestedDiagnostic: string;
  labId: string;
}

const TROUBLESHOOTING_DATABASE: IssueItem[] = [
  {
    id: 'ts-k8s-01',
    symptom: 'Pod status CrashLoopBackOff: back-off 5m restarting failed container',
    technology: 'Kubernetes',
    subsystem: 'Kubelet / Probes',
    level: 'Intermediate',
    runtime: 'KUBERNETES',
    observableEvidence: 'Container restarts repeatedly every 10 seconds; events indicate Liveness probe failed HTTP 500.',
    suggestedDiagnostic: 'kubectl describe pod <name> && kubectl logs <name> --previous',
    labId: 'k8s-pod-crashloop-probe',
  },
  {
    id: 'ts-k8s-02',
    symptom: '503 Service Unavailable / Connection Refused on Service Endpoint',
    technology: 'Kubernetes',
    subsystem: 'Kube-Proxy / Endpoints',
    level: 'Intermediate',
    runtime: 'KUBERNETES',
    observableEvidence: 'ClusterIP responds with connection refused; Endpoints list is empty (<none>).',
    suggestedDiagnostic: 'kubectl get endpoints <svc> -o yaml && kubectl get pods --show-labels',
    labId: 'k8s-service-zero-endpoints',
  },
  {
    id: 'ts-linux-01',
    symptom: 'No space left on device error despite 85GB free disk blocks',
    technology: 'Linux',
    subsystem: 'VFS / Inodes',
    level: 'Beginner',
    runtime: 'REAL',
    observableEvidence: 'touch test.txt fails with ENOSPC; df -h reports 15% used, but df -i shows 100% inode saturation.',
    suggestedDiagnostic: 'df -i && find / -xdev -printf "%h\n" | sort | uniq -c | sort -nr | head -10',
    labId: 'linux-inode-exhaustion',
  },
  {
    id: 'ts-docker-01',
    symptom: 'Container takes exactly 10s to stop and loses in-flight transactions',
    technology: 'Docker',
    subsystem: 'Kernel Signals / PID 1',
    level: 'Intermediate',
    runtime: 'REAL',
    observableEvidence: 'docker stop hangs for exactly 10 seconds before forcefully sending SIGKILL; logs show ungraceful exit.',
    suggestedDiagnostic: 'podman top <c_name> pid,comm && cat entrypoint.sh',
    labId: 'docker-pid1-signals',
  },
  {
    id: 'ts-sre-01',
    symptom: '503 Spike & P99 Latency degradation cascading across checkout flow',
    technology: 'SRE',
    subsystem: 'Connection Pools / Outages',
    level: 'Production',
    runtime: 'MULTI-CONTAINER',
    observableEvidence: 'Frontend latency spikes from 45ms to 4200ms; HTTP 503 errors spike to 38% under normal request rates.',
    suggestedDiagnostic: 'promql: sum(rate(http_requests_total{status=~"5.."}[1m]))',
    labId: 'checkout-latency-spike',
  },
  {
    id: 'ts-gitops-01',
    symptom: 'Argo CD Application OutOfSync and perpetual sync wave loop',
    technology: 'GitOps',
    subsystem: 'Reconciliation Controller',
    level: 'Advanced',
    runtime: 'SIMULATED',
    observableEvidence: 'Application controller reports OutOfSync diff on immutable field spec.clusterIP.',
    suggestedDiagnostic: 'argocd app diff <app> && kubectl get app <app> -o yaml',
    labId: 'argocd-drift-out-of-sync',
  },
  {
    id: 'ts-istio-01',
    symptom: '503 UC (Upstream Connection Termination) with strict mTLS enabled',
    technology: 'Istio',
    subsystem: 'Envoy Sidecar / mTLS',
    level: 'Advanced',
    runtime: 'MULTI-CONTAINER',
    observableEvidence: 'Envoy access log shows 503 UC; PeerAuthentication requires STRICT mTLS while client sends plaintext.',
    suggestedDiagnostic: 'istioctl proxy-config cluster <pod> && istioctl authn tls-check <pod>',
    labId: 'istio-retry-storm-cascade',
  },
  {
    id: 'ts-tf-01',
    symptom: 'Terraform Error acquiring the state lock on DynamoDB/S3 backend',
    technology: 'Terraform',
    subsystem: 'State Storage Backend',
    level: 'Intermediate',
    runtime: 'REAL',
    observableEvidence: 'Plan/Apply fails: ConditionalCheckFailedException lock already held by abandoned CI runner ID.',
    suggestedDiagnostic: 'terraform force-unlock -force <LOCK_ID>',
    labId: 'terraform-state-lock-recovery',
  },
  {
    id: 'ts-k8s-03',
    symptom: 'OOMKilled Pod Termination (Exit Code 137) during data ingestion',
    technology: 'Kubernetes',
    subsystem: 'Kernel Cgroups / Memory',
    level: 'Intermediate',
    runtime: 'KUBERNETES',
    observableEvidence: 'Pod terminated abruptly; Last State: Terminated with Reason: OOMKilled, Exit Code: 137.',
    suggestedDiagnostic: 'kubectl describe pod <name> | grep -E "Reason|Limits"',
    labId: 'k8s-pod-crashloop-probe',
  },
  {
    id: 'ts-net-01',
    symptom: 'DNS query timeout lookup failed: Temporary failure in name resolution',
    technology: 'Networking',
    subsystem: 'CoreDNS / Resolver',
    level: 'Beginner',
    runtime: 'REAL',
    observableEvidence: 'dig api.internal times out after 5000ms; /etc/resolv.conf points to unreachable nameserver IP.',
    suggestedDiagnostic: 'cat /etc/resolv.conf && dig @8.8.8.8 google.com',
    labId: 'linux-inode-exhaustion',
  },
];

const SEARCH_QUICK_TERMS = [
  'CrashLoopBackOff',
  '503',
  'OOMKilled',
  'DNS',
  'Pending',
  'High CPU',
  'Terraform lock',
  'Argo OutOfSync',
];

interface TroubleshootingLibraryProps {
  onSelectLab?: (labId: string) => void;
}

export const TroubleshootingLibrary: React.FC<TroubleshootingLibraryProps> = ({ onSelectLab }) => {
  const [query, setQuery] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('All');
  const [techFilter, setTechFilter] = useState<string>('All');

  const filtered = TROUBLESHOOTING_DATABASE.filter((item) => {
    const matchesQuery =
      item.symptom.toLowerCase().includes(query.toLowerCase()) ||
      item.technology.toLowerCase().includes(query.toLowerCase()) ||
      item.observableEvidence.toLowerCase().includes(query.toLowerCase());
    const matchesLevel = levelFilter === 'All' || item.level === levelFilter;
    const matchesTech = techFilter === 'All' || item.technology === techFilter;
    return matchesQuery && matchesLevel && matchesTech;
  });

  const getLevelBadgeClass = (lvl: string) => {
    switch (lvl) {
      case 'Beginner':
        return 'badge-beginner';
      case 'Intermediate':
        return 'badge-intermediate';
      case 'Advanced':
        return 'badge-advanced';
      case 'Production':
        return 'badge-production';
      default:
        return 'badge-beginner';
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          Production Troubleshooting Library
        </h1>
        <p style={{ margin: '6px 0 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
          Searchable repository of canonical distributed systems failures, symptom patterns, and live sandbox reproductions.
        </p>
      </div>

      {/* Search & Quick Filters Bar */}
      <div
        style={{
          backgroundColor: '#0d121d',
          border: '1px solid var(--border-subtle)',
          borderRadius: 8,
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#07090e',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6,
              padding: '8px 14px',
              gap: 10,
            }}
          >
            <Search size={16} color="#64748b" />
            <input
              type="text"
              placeholder="Search symptoms (e.g. CrashLoopBackOff, 503, DNS, OOMKilled)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f1f5f9',
                fontSize: '0.9rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            style={{
              backgroundColor: '#07090e',
              border: '1px solid var(--border-subtle)',
              color: '#cbd5e1',
              borderRadius: 6,
              padding: '8px 12px',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            <option value="All">All Tiers</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
            <option value="Production">Production</option>
          </select>

          <select
            value={techFilter}
            onChange={(e) => setTechFilter(e.target.value)}
            style={{
              backgroundColor: '#07090e',
              border: '1px solid var(--border-subtle)',
              color: '#cbd5e1',
              borderRadius: 6,
              padding: '8px 12px',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            <option value="All">All Technologies</option>
            <option value="Kubernetes">Kubernetes</option>
            <option value="Linux">Linux</option>
            <option value="Docker">Docker</option>
            <option value="SRE">SRE & Incident</option>
            <option value="GitOps">GitOps</option>
            <option value="Istio">Istio</option>
            <option value="Terraform">Terraform</option>
            <option value="Networking">Networking</option>
          </select>
        </div>

        {/* Quick Search Tags */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Quick Filters:</span>
          {SEARCH_QUICK_TERMS.map((term) => (
            <button
              key={term}
              onClick={() => setQuery(term)}
              className="btn btn-secondary"
              style={{
                fontSize: '0.75rem',
                padding: '3px 10px',
                borderRadius: 4,
                backgroundColor: query === term ? 'rgba(0, 242, 254, 0.15)' : '#07090e',
                color: query === term ? '#00f2fe' : '#94a3b8',
                borderColor: query === term ? '#00f2fe' : 'var(--border-subtle)',
              }}
            >
              {term}
            </button>
          ))}
          {query && (
            <button
              onClick={() => setQuery('')}
              style={{
                background: 'none',
                border: 'none',
                color: '#f43f5e',
                fontSize: '0.75rem',
                cursor: 'pointer',
                marginLeft: 4,
              }}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: '#94a3b8' }}>
        <span>Showing {filtered.length} production failure scenarios</span>
        <span>Grouped by Severity & Technology</span>
      </div>

      {/* Issues Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))', gap: 16 }}>
        {filtered.map((item) => (
          <div
            key={item.id}
            style={{
              backgroundColor: '#0d121d',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 20,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: 14,
              transition: 'border-color 0.2s',
            }}
          >
            <div>
              {/* Badges row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className={`badge ${getLevelBadgeClass(item.level)}`}>{item.level}</span>
                  <span style={{ fontSize: '0.75rem', color: '#cbd5e1', fontWeight: 600 }}>
                    {item.technology} • {item.subsystem}
                  </span>
                </div>
                <span className="badge badge-beginner" style={{ fontSize: '0.65rem' }}>
                  {item.runtime}
                </span>
              </div>

              {/* Symptom Headline */}
              <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', color: '#f8fafc', fontWeight: 700, lineHeight: 1.4 }}>
                {item.symptom}
              </h3>

              {/* Observable Evidence (Root cause NOT spoiled!) */}
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 6,
                  backgroundColor: '#07090e',
                  border: '1px solid rgba(255,255,255,0.05)',
                  fontSize: '0.8rem',
                  color: '#94a3b8',
                  lineHeight: 1.5,
                  marginBottom: 10,
                }}
              >
                <div style={{ color: '#f59e0b', fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase', marginBottom: 2 }}>
                  Observed Symptom Evidence:
                </div>
                {item.observableEvidence}
              </div>

              {/* Suggested Diagnostic Probe */}
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                <span style={{ fontWeight: 600, color: '#94a3b8' }}>First Diagnostic Command: </span>
                <code style={{ color: '#00f2fe', fontFamily: 'monospace' }}>{item.suggestedDiagnostic}</code>
              </div>
            </div>

            {/* Action Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              {onSelectLab && (
                <button
                  onClick={() => onSelectLab(item.labId)}
                  className="btn btn-primary"
                  style={{ fontSize: '0.8rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <Play size={14} /> Reproduce & Troubleshoot
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
