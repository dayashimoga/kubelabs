import React, { useState } from 'react';
import { BookOpen, Layers, Terminal, Shield, Cpu, Play, CheckCircle2, Search, ArrowRight, ExternalLink } from 'lucide-react';

interface CurriculumTopic {
  id: string;
  title: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced' | 'Production';
  summary: string;
  architectureNotes: string;
  keyCommands: string[];
  securitySafeguards: string[];
  interviewScenario: string;
  associatedLabId?: string;
  associatedLabTitle?: string;
}

interface TrackData {
  id: string;
  name: string;
  category: string;
  description: string;
  topics: CurriculumTopic[];
}

const TRACKS_CURRICULUM: TrackData[] = [
  {
    id: 'kubernetes',
    name: 'Kubernetes Deep-Dive',
    category: 'Orchestration',
    description: 'Complete architecture from control plane etcd consensus to container runtime interfaces, CNI networking, and compound outage remediation.',
    topics: [
      {
        id: 'k8s-arch',
        title: 'Control Plane Architecture & Node Components',
        level: 'Beginner',
        summary: 'Kube-apiserver as the single state gateway, etcd raft consensus, kube-controller-manager loop reconciliation, and kube-scheduler scoring algorithms.',
        architectureNotes: 'Kubelet interacts via CRI (containerd/CRI-O), kube-proxy configures iptables/IPVS packet filtering, and CoreDNS provides service discovery.',
        keyCommands: ['kubectl get componentstatuses', 'kubectl get nodes -o wide', 'kubectl cluster-info dump'],
        securitySafeguards: ['Enforce mTLS on port 6443', 'Encrypt etcd secrets at rest via KMS', 'Restrict kubelet API access'],
        interviewScenario: 'Explain what happens under the hood when you run kubectl apply -f deployment.yaml from authentication to pod scheduling.',
      },
      {
        id: 'k8s-crashloop',
        title: 'Pod Lifecycle & Probe Troubleshooting',
        level: 'Intermediate',
        summary: 'Dissecting ContainerCreating, Running, CrashLoopBackOff, and OOMKilled states. Startup vs. Liveness vs. Readiness probe dynamics.',
        architectureNotes: 'Kubelet executes probes via exec, httpGet, or tcpSocket. Failing readiness isolates pod from EndpointSlice; failing liveness triggers container restart.',
        keyCommands: ['kubectl describe pod <name>', 'kubectl logs <name> --previous', 'kubectl get events --sort-by=.metadata.creationTimestamp'],
        securitySafeguards: ['Avoid overly aggressive probe timeouts during heavy GC cycles', 'Set initialDelaySeconds safely'],
        interviewScenario: 'How do you differentiate an application deadlocking from an OOMKilled eviction using only kubectl commands?',
        associatedLabId: 'k8s-pod-crashloop-probe',
        associatedLabTitle: 'Kubernetes Pod CrashLoop & Liveness Probes',
      },
      {
        id: 'k8s-services',
        title: 'Services, EndpointSlices & CNI Routing',
        level: 'Intermediate',
        summary: 'ClusterIP, NodePort, and LoadBalancer abstractions. iptables PREROUTING and KUBE-SERVICES chains, CoreDNS SRV records, and EndpointSlice synchronizers.',
        architectureNotes: 'Selector label mismatches leave Service with zero endpoints. CNI plugins (Cilium, Calico, Flannel) manage IPAM and overlay routing.',
        keyCommands: ['kubectl get endpointslices', 'kubectl get svc -o wide', 'kubectl run tmp --rm -it --image=curlimages/curl -- curl <svc>'],
        securitySafeguards: ['Enforce NetworkPolicy default-deny ingress/egress rules', 'Isolate multi-tenant namespaces'],
        interviewScenario: 'A Service IP is pingable but curl hangs indefinitely. Walk me through your troubleshooting methodology.',
        associatedLabId: 'k8s-service-zero-endpoints',
        associatedLabTitle: 'Kubernetes Service Zero Endpoints Mismatch',
      },
      {
        id: 'k8s-production-ops',
        title: 'Node Pressure, Taints, Tolerations & HPA',
        level: 'Production',
        summary: 'Eviction thresholds (MemoryPressure, DiskPressure), horizontal pod autoscaling via custom metric APIs, PodDisruptionBudgets, and graceful drain.',
        architectureNotes: 'Descheduler optimizes pod placement; cluster autoscaler interacts with cloud node groups based on Pending pod unschedulability.',
        keyCommands: ['kubectl top nodes', 'kubectl drain <node> --ignore-daemonsets --delete-emptydir-data', 'kubectl get hpa'],
        securitySafeguards: ['Define PodDisruptionBudgets for quorum systems', 'Configure priorityClasses to protect system pods'],
        interviewScenario: 'Design a rolling upgrade strategy for a 1000-node cluster running stateless APIs and stateful distributed databases with zero downtime.',
      },
    ],
  },
  {
    id: 'linux',
    name: 'Linux Systems & Kernel Diagnostics',
    category: 'Systems',
    description: 'Deep Linux internals covering the VFS layer, inode exhaustion, process signals, memory pressure, cgroups v2, and network socket exhaustion.',
    topics: [
      {
        id: 'linux-inodes',
        title: 'Filesystem VFS & Inode Saturation',
        level: 'Beginner',
        summary: 'Inodes store metadata (permissions, owner, size, block pointers). Creating millions of zero-byte session files depletes inodes despite gigabytes of free disk space.',
        architectureNotes: 'Ext4/XFS filesystems allocate a fixed or dynamic inode table. df -i reveals inode utilization independent of df -h.',
        keyCommands: ['df -ih', 'find / -xdev -printf "%h\n" | sort | uniq -c | sort -k 1 -nr | head -20', 'stat /var/spool'],
        securitySafeguards: ['Set up tmpfiles.d automated cleanup timers', 'Implement quota limits on user mail/session directories'],
        interviewScenario: 'A production server reports No space left on device, but df -h shows 80GB available. What command solves this puzzle?',
        associatedLabId: 'linux-inode-exhaustion',
        associatedLabTitle: 'Linux Inode Exhaustion & Root Cause',
      },
      {
        id: 'linux-zombies',
        title: 'Process Lifecycle, Signals & Zombie Reaping',
        level: 'Intermediate',
        summary: 'Fork/exec syscalls, process states (R, S, D, Z, T), and PID 1 responsibility for reaping deceased children via waitpid() syscalls.',
        architectureNotes: 'Zombie processes retain an entry in the kernel process table. If PID max is reached, no new processes can be created on the system.',
        keyCommands: ['ps aux | awk \'$8=="Z" {print}\'', 'pstree -p -s <pid>', 'kill -SIGCHLD <parent_pid>'],
        securitySafeguards: ['Always use dumb-init or tini in containers', 'Monitor /proc/sys/kernel/pid_max'],
        interviewScenario: 'Why cannot a zombie process be terminated with kill -9, and how do you cleanly remove it from the kernel table?',
      },
    ],
  },
  {
    id: 'docker',
    name: 'Docker & OCI Container Engine',
    category: 'Containers',
    description: 'OCI specs, Linux namespaces (mnt, pid, net, ipc, uts, user), cgroups v2 resource accounting, and multi-stage Dockerfile optimization.',
    topics: [
      {
        id: 'docker-pid1',
        title: 'PID 1 Signal Trapping & Graceful Shutdown',
        level: 'Intermediate',
        summary: 'Containers running shell scripts as entrypoint trap SIGTERM, causing docker stop to wait 10s before issuing ungraceful SIGKILL.',
        architectureNotes: 'PID 1 in a PID namespace has default signal masking. Signals without explicit handlers are ignored by the kernel.',
        keyCommands: ['docker stop -t 2 <container>', 'podman top <container> pid,comm', 'exec "$@" in entrypoint.sh'],
        securitySafeguards: ['Drop root privileges using USER directive', 'Mount read-only root filesystems'],
        interviewScenario: 'Explain the difference between ENTRYPOINT ["executable", "param"] and ENTRYPOINT executable param.',
        associatedLabId: 'docker-pid1-signals',
        associatedLabTitle: 'Docker PID 1 Signal Trapping & Zombie Reaping',
      },
    ],
  },
  {
    id: 'sre-resilience',
    name: 'SRE & Incident Engineering',
    category: 'Reliability',
    description: 'SLI/SLO mathematics, error budgets, cascading failure propagation, retry storms, circuit breakers, and blameless incident reviews.',
    topics: [
      {
        id: 'sre-cascading',
        title: 'Cascading Latency Spikes & Queue Starvation',
        level: 'Production',
        summary: 'Downstream database locking increases API response latency, leading to upstream connection pool starvation, thread pool saturation, and 503 storms.',
        architectureNotes: 'Mitigation requires request timeouts, exponential backoff with full jitter, and Envoy circuit breakers with outlier detection.',
        keyCommands: ['kubectl logs -l app=checkout --tail=50', 'promql: sum(rate(http_requests_total{status=~"5.."}[1m]))', 'promql: histogram_quantile(0.99, ...)'],
        securitySafeguards: ['Implement rate limiters at API gateway', 'Establish shed-load shedding policies'],
        interviewScenario: 'Your checkout API error rate spikes to 45% during Black Friday. Walk through the first 5 minutes of your incident triage.',
        associatedLabId: 'checkout-latency-spike',
        associatedLabTitle: 'Cascading Latency Spike & Queue Saturation',
      },
    ],
  },
  {
    id: 'observability',
    name: 'Observability (Prometheus, OTel, Loki)',
    category: 'Telemetry',
    description: 'High-cardinality time series, OpenTelemetry trace context propagation (W3C traceparent), log structured querying, and Alertmanager routing.',
    topics: [
      {
        id: 'otel-tracing',
        title: 'Distributed Tracing & Context Propagation',
        level: 'Intermediate',
        summary: 'Tracing asynchronous distributed microservice requests using span IDs, parent IDs, and baggage items to isolate multi-tier bottlenecks.',
        architectureNotes: 'OTel collector receives OTLP gRPC/HTTP payloads, executes tail-based sampling processors, and exports to Jaeger/Tempo storage backends.',
        keyCommands: ['curl -v -H "traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01" http://localhost:8080/order'],
        securitySafeguards: ['Scrub PII and JWT tokens from span attributes', 'Enforce TLS on OTLP collector ingestion'],
        interviewScenario: 'How do you troubleshoot missing spans in an asynchronous Kafka event-driven architecture?',
      },
    ],
  },
  {
    id: 'gitops',
    name: 'GitOps & Argo CD',
    category: 'Delivery',
    description: 'Declarative Git-as-single-source-of-truth, Argo CD Application reconciliation loops, self-heal, automated pruning, and drift detection.',
    topics: [
      {
        id: 'argocd-drift',
        title: 'Reconciliation Loops, OutOfSync & CRD Drift',
        level: 'Intermediate',
        summary: 'Detecting differences between desired Git commit state and live Kubernetes etcd state. Resolving sync wave ordering and immutable field errors.',
        architectureNotes: 'Argo CD repo-server renders manifests via Kustomize/Helm; application-controller compares live state and applies patches.',
        keyCommands: ['argocd app get <name>', 'argocd app diff <name>', 'argocd app sync <name> --prune'],
        securitySafeguards: ['Restrict Argo CD RBAC permissions per project', 'Sign Git commits with GPG keys'],
        interviewScenario: 'A cluster admin manually edited a live Deployment. How does Argo CD behave with self-heal disabled vs. enabled?',
      },
    ],
  },
];

interface CurriculumBrowserProps {
  onSelectLab?: (labId: string) => void;
}

export const CurriculumBrowser: React.FC<CurriculumBrowserProps> = ({ onSelectLab }) => {
  const [selectedTrackId, setSelectedTrackId] = useState<string>('kubernetes');
  const [selectedTopicId, setSelectedTopicId] = useState<string>('k8s-arch');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'theory' | 'commands' | 'interview'>('theory');

  const selectedTrack = TRACKS_CURRICULUM.find((t) => t.id === selectedTrackId) || TRACKS_CURRICULUM[0];
  const selectedTopic = selectedTrack.topics.find((tp) => tp.id === selectedTopicId) || selectedTrack.topics[0];

  const filteredTopics = selectedTrack.topics.filter(
    (tp) =>
      tp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tp.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            SRE & DevOps Curriculum Guides
          </h1>
          <p style={{ margin: '6px 0 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
            Exhaustive, 15-dimension engineering curriculum organized from foundational systems to production resilience.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#0d121d',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6,
              padding: '6px 12px',
              gap: 8,
              width: 240,
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Search topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f1f5f9',
                fontSize: '0.85rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>
        </div>
      </div>

      {/* Track Selector Bar */}
      <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
        {TRACKS_CURRICULUM.map((tr) => {
          const isActive = tr.id === selectedTrackId;
          return (
            <button
              key={tr.id}
              onClick={() => {
                setSelectedTrackId(tr.id);
                setSelectedTopicId(tr.topics[0]?.id || '');
              }}
              className="btn"
              style={{
                backgroundColor: isActive ? '#00f2fe' : '#0d121d',
                color: isActive ? '#07090e' : '#cbd5e1',
                fontWeight: isActive ? 700 : 500,
                border: isActive ? '1px solid #00f2fe' : '1px solid var(--border-subtle)',
                padding: '8px 16px',
                borderRadius: 8,
                fontSize: '0.85rem',
                whiteSpace: 'nowrap',
              }}
            >
              {tr.name}
            </button>
          );
        })}
      </div>

      {/* Split Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24, alignItems: 'start' }}>
        {/* Topic Index Sidebar */}
        <div
          style={{
            backgroundColor: '#0d121d',
            border: '1px solid var(--border-subtle)',
            borderRadius: 8,
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: 4 }}>
            {selectedTrack.name} Modules ({filteredTopics.length})
          </div>
          {filteredTopics.map((topic) => {
            const isSel = topic.id === selectedTopic.id;
            return (
              <div
                key={topic.id}
                onClick={() => setSelectedTopicId(topic.id)}
                style={{
                  padding: '12px 14px',
                  borderRadius: 6,
                  backgroundColor: isSel ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                  border: isSel ? '1px solid rgba(0, 242, 254, 0.4)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease-in-out',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: isSel ? 700 : 500, fontSize: '0.875rem', color: isSel ? '#00f2fe' : '#f1f5f9' }}>
                    {topic.title}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                  <span className="badge badge-beginner" style={{ fontSize: '0.65rem' }}>
                    {topic.level}
                  </span>
                  {topic.associatedLabId && (
                    <span style={{ fontSize: '0.65rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Terminal size={10} /> Lab Available
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Main Guide Content Panel */}
        <div
          style={{
            backgroundColor: '#0d121d',
            border: '1px solid var(--border-subtle)',
            borderRadius: 8,
            padding: 28,
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          {/* Topic Title & Badges */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span className="badge badge-intermediate">{selectedTopic.level} Module</span>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Track: {selectedTrack.name}</span>
              </div>
              <h2 style={{ margin: 0, fontSize: '1.4rem', color: '#f8fafc', fontWeight: 800 }}>
                {selectedTopic.title}
              </h2>
            </div>

            {selectedTopic.associatedLabId && onSelectLab && (
              <button
                onClick={() => onSelectLab(selectedTopic.associatedLabId!)}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: 8 }}
              >
                <Play size={16} /> Launch Interactive Lab
              </button>
            )}
          </div>

          {/* Subtabs */}
          <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 10 }}>
            <button
              onClick={() => setActiveTab('theory')}
              style={{
                background: 'none',
                border: 'none',
                color: activeTab === 'theory' ? '#00f2fe' : '#94a3b8',
                fontWeight: activeTab === 'theory' ? 700 : 500,
                cursor: 'pointer',
                fontSize: '0.9rem',
                borderBottom: activeTab === 'theory' ? '2px solid #00f2fe' : '2px solid transparent',
                paddingBottom: 6,
              }}
            >
              Theory & Architecture
            </button>
            <button
              onClick={() => setActiveTab('commands')}
              style={{
                background: 'none',
                border: 'none',
                color: activeTab === 'commands' ? '#00f2fe' : '#94a3b8',
                fontWeight: activeTab === 'commands' ? 700 : 500,
                cursor: 'pointer',
                fontSize: '0.9rem',
                borderBottom: activeTab === 'commands' ? '2px solid #00f2fe' : '2px solid transparent',
                paddingBottom: 6,
              }}
            >
              Essential Diagnostic Commands
            </button>
            <button
              onClick={() => setActiveTab('interview')}
              style={{
                background: 'none',
                border: 'none',
                color: activeTab === 'interview' ? '#00f2fe' : '#94a3b8',
                fontWeight: activeTab === 'interview' ? 700 : 500,
                cursor: 'pointer',
                fontSize: '0.9rem',
                borderBottom: activeTab === 'interview' ? '2px solid #00f2fe' : '2px solid transparent',
                paddingBottom: 6,
              }}
            >
              Interview Challenge & Security
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'theory' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div>
                <h4 style={{ margin: '0 0 8px 0', color: '#f1f5f9', fontSize: '0.95rem' }}>Concept Overview</h4>
                <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {selectedTopic.summary}
                </p>
              </div>

              <div
                style={{
                  padding: 16,
                  borderRadius: 6,
                  backgroundColor: 'rgba(0, 242, 254, 0.04)',
                  border: '1px solid rgba(0, 242, 254, 0.2)',
                }}
              >
                <h4 style={{ margin: '0 0 6px 0', color: '#00f2fe', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Layers size={14} /> Architectural Internals
                </h4>
                <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.875rem', lineHeight: 1.5 }}>
                  {selectedTopic.architectureNotes}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'commands' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <h4 style={{ margin: 0, color: '#f1f5f9', fontSize: '0.95rem' }}>Diagnostic Command Arsenal</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {selectedTopic.keyCommands.map((cmd, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 6,
                      backgroundColor: '#07090e',
                      border: '1px solid rgba(255,255,255,0.06)',
                      fontFamily: 'monospace',
                      color: '#00f2fe',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span>{cmd}</span>
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Terminal Ready</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'interview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div
                style={{
                  padding: 16,
                  borderRadius: 6,
                  backgroundColor: 'rgba(245, 158, 11, 0.05)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                }}
              >
                <h4 style={{ margin: '0 0 8px 0', color: '#f59e0b', fontSize: '0.9rem' }}>
                  Principal SRE / Staff Interview Scenario
                </h4>
                <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.875rem', lineHeight: 1.5, fontStyle: 'italic' }}>
                  "{selectedTopic.interviewScenario}"
                </p>
              </div>

              <div>
                <h4 style={{ margin: '0 0 10px 0', color: '#f1f5f9', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Shield size={16} color="#10b981" /> DevSecOps & Production Safeguards
                </h4>
                <ul style={{ margin: 0, paddingLeft: 20, color: '#cbd5e1', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  {selectedTopic.securitySafeguards.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
