import React, { useState } from 'react';
import { GitBranch, Layers, ShieldCheck, ArrowRight, Lock, CheckCircle, Play } from 'lucide-react';

interface SkillNode {
  id: string;
  name: string;
  track: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'production';
  status: 'mastered' | 'available' | 'in_progress' | 'locked';
  prerequisites: string[];
  description: string;
}

const SKILL_NODES: SkillNode[] = [
  {
    id: 'linux-core',
    name: 'Linux System Internals',
    track: 'linux',
    level: 'beginner',
    status: 'mastered',
    prerequisites: [],
    description: 'VFS, Inodes, Process Scheduling, Signals, Memory Management.',
  },
  {
    id: 'bash-scripting',
    name: 'Production Shell Scripting',
    track: 'bash',
    level: 'beginner',
    status: 'mastered',
    prerequisites: ['linux-core'],
    description: 'Strict error modes (set -euo pipefail), trap handlers, pipeline introspection.',
  },
  {
    id: 'networking-core',
    name: 'Container & Host Networking',
    track: 'networking',
    level: 'intermediate',
    status: 'mastered',
    prerequisites: ['linux-core'],
    description: 'TCP/IP socket states, TIME_WAIT tuning, veth pairs, iptables NAT.',
  },
  {
    id: 'docker-oci',
    name: 'Docker & OCI Runtimes',
    track: 'docker',
    level: 'intermediate',
    status: 'in_progress',
    prerequisites: ['linux-core', 'networking-core'],
    description: 'Multi-stage builds, non-root USER, PID 1 zombie reaping, cgroups.',
  },
  {
    id: 'k8s-core',
    name: 'Kubernetes Architecture',
    track: 'kubernetes',
    level: 'intermediate',
    status: 'available',
    prerequisites: ['docker-oci', 'networking-core'],
    description: 'Control plane, kube-proxy, Endpoints, probes, pod lifecycle, RBAC.',
  },
  {
    id: 'helm-kustomize',
    name: 'Declarative Packaging (Helm & Kustomize)',
    track: 'helm',
    level: 'intermediate',
    status: 'available',
    prerequisites: ['k8s-core'],
    description: 'Go templating indentation, nindent, schema validation, overlay patches.',
  },
  {
    id: 'terraform-iac',
    name: 'Terraform Infrastructure as Code',
    track: 'terraform',
    level: 'intermediate',
    status: 'available',
    prerequisites: ['networking-core'],
    description: 'State locking deadlock recovery, drift detection, provider versioning.',
  },
  {
    id: 'argocd-gitops',
    name: 'GitOps Continuous Delivery (Argo CD)',
    track: 'argocd',
    level: 'advanced',
    status: 'available',
    prerequisites: ['k8s-core', 'helm-kustomize'],
    description: 'OutOfSync remediation, automated self-healing, CRD reconcilers.',
  },
  {
    id: 'observability-prom',
    name: 'Prometheus, Loki & OpenTelemetry',
    track: 'prometheus',
    level: 'advanced',
    status: 'available',
    prerequisites: ['k8s-core'],
    description: 'High-cardinality label drops, PromQL SLO alerting, W3C trace context.',
  },
  {
    id: 'istio-mesh',
    name: 'Service Mesh (Istio / Envoy)',
    track: 'istio',
    level: 'advanced',
    status: 'available',
    prerequisites: ['k8s-core', 'observability-prom'],
    description: 'Mutual TLS STRICT mode, Envoy circuit breaking, retry storm mitigation.',
  },
  {
    id: 'aws-eks-platform',
    name: 'Cloud Platform Engineering (AWS/EKS)',
    track: 'aws-eks',
    level: 'production',
    status: 'locked',
    prerequisites: ['k8s-core', 'terraform-iac'],
    description: 'VPC CNI IP exhaustion, IRSA IAM OIDC mapping, Security Groups.',
  },
  {
    id: 'sre-incident-commander',
    name: 'Production SRE & Chaos Resilience',
    track: 'sre-resilience',
    level: 'production',
    status: 'locked',
    prerequisites: ['istio-mesh', 'observability-prom', 'aws-eks-platform'],
    description: 'SEV-1 triage, cascading failure suppression, post-mortem generation.',
  },
];

interface SkillGraphProps {
  onSelectTrack: (track: string) => void;
}

export const SkillGraph: React.FC<SkillGraphProps> = ({ onSelectTrack }) => {
  const [selectedNode, setSelectedNode] = useState<SkillNode>(SKILL_NODES[0]);

  const getStatusBadge = (status: SkillNode['status']) => {
    switch (status) {
      case 'mastered':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#10b981', fontSize: '0.75rem', fontWeight: 600 }}>
            <CheckCircle size={14} /> Mastered
          </span>
        );
      case 'in_progress':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#00f2fe', fontSize: '0.75rem', fontWeight: 600 }}>
            <Play size={14} /> Active
          </span>
        );
      case 'available':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#f59e0b', fontSize: '0.75rem', fontWeight: 600 }}>
            Available
          </span>
        );
      case 'locked':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#64748b', fontSize: '0.75rem', fontWeight: 600 }}>
            <Lock size={14} /> Locked
          </span>
        );
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Visual Graph Area */}
      <div style={{ flex: 1, padding: 30, overflowY: 'auto' }}>
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 6px 0', color: '#f8fafc' }}>
            Production SRE Competency & Dependency Map
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: 0 }}>
            Interactive pedagogical prerequisite graph: Master foundational primitives before orchestrating complex cloud and mesh topologies.
          </p>
        </div>

        {/* Level Progression Columns */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {(['beginner', 'intermediate', 'advanced', 'production'] as const).map((lvl) => (
            <div key={lvl} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#64748b',
                  paddingBottom: 8,
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                {lvl}
              </div>

              {SKILL_NODES.filter((n) => n.level === lvl).map((node) => {
                const isSelected = selectedNode.id === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    style={{
                      padding: 16,
                      borderRadius: 8,
                      backgroundColor: isSelected ? 'rgba(0, 242, 254, 0.08)' : '#0d121d',
                      border: `1px solid ${isSelected ? '#00f2fe' : 'rgba(255,255,255,0.08)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                        {node.track}
                      </span>
                      {getStatusBadge(node.status)}
                    </div>
                    <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem', marginBottom: 6 }}>
                      {node.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.4 }}>
                      {node.description}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Selected Node Details Drawer */}
      <div
        style={{
          width: 380,
          borderLeft: '1px solid rgba(255,255,255,0.08)',
          backgroundColor: '#07090e',
          padding: 24,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#00f2fe', textTransform: 'uppercase' }}>
              Track: {selectedNode.track}
            </span>
            {getStatusBadge(selectedNode.status)}
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 12px 0' }}>
            {selectedNode.name}
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: 20 }}>
            {selectedNode.description}
          </p>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: 8 }}>
              Prerequisites
            </div>
            {selectedNode.prerequisites.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: '#10b981' }}>None (Foundational Entrypoint)</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {selectedNode.prerequisites.map((p) => {
                  const prereqNode = SKILL_NODES.find((n) => n.id === p);
                  return (
                    <div
                      key={p}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: '#0d121d',
                        borderRadius: 6,
                        border: '1px solid rgba(255,255,255,0.06)',
                        fontSize: '0.8rem',
                        color: '#cbd5e1',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <CheckCircle size={14} color="#10b981" />
                      {prereqNode ? prereqNode.name : p}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <button
          onClick={() => onSelectTrack(selectedNode.track)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            width: '100%',
            padding: '12px 16px',
            backgroundColor: '#00f2fe',
            color: '#07090e',
            border: 'none',
            borderRadius: 6,
            fontWeight: 700,
            fontSize: '0.9rem',
            cursor: 'pointer',
          }}
        >
          Explore {selectedNode.track.toUpperCase()} Labs
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};
