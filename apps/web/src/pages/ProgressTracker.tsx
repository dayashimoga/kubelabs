import React, { useState } from 'react';
import { Award, CheckCircle2, Trophy, Clock, Zap, Download, RefreshCw, BarChart2, ShieldCheck, FileText } from 'lucide-react';

interface TrackProgress {
  track: string;
  category: string;
  totalLabs: number;
  completedLabs: number;
  score: number;
}

const TRACK_STATS: TrackProgress[] = [
  { track: 'Linux Systems', category: 'Foundations', totalLabs: 3, completedLabs: 3, score: 96 },
  { track: 'Docker Containers', category: 'Containers', totalLabs: 3, completedLabs: 2, score: 92 },
  { track: 'Kubernetes Deep-Dive', category: 'Orchestration', totalLabs: 5, completedLabs: 4, score: 88 },
  { track: 'Helm & Kustomize', category: 'Packaging', totalLabs: 2, completedLabs: 2, score: 95 },
  { track: 'Terraform IaC', category: 'Infrastructure', totalLabs: 3, completedLabs: 2, score: 90 },
  { track: 'GitOps & Argo CD', category: 'Delivery', totalLabs: 3, completedLabs: 2, score: 85 },
  { track: 'Prometheus & Grafana', category: 'Observability', totalLabs: 4, completedLabs: 3, score: 94 },
  { track: 'OpenTelemetry & Tracing', category: 'Observability', totalLabs: 3, completedLabs: 2, score: 87 },
  { track: 'Istio Service Mesh', category: 'Networking', totalLabs: 3, completedLabs: 2, score: 84 },
  { track: 'SRE Incident War Room', category: 'Reliability', totalLabs: 4, completedLabs: 3, score: 91 },
  { track: 'AWS EKS Architecture', category: 'Cloud', totalLabs: 3, completedLabs: 2, score: 89 },
  { track: 'DevSecOps & RBAC', category: 'Security', totalLabs: 3, completedLabs: 3, score: 98 },
];

export const ProgressTracker: React.FC = () => {
  const [showCertificate, setShowCertificate] = useState(false);

  const totalPossibleLabs = TRACK_STATS.reduce((acc, t) => acc + t.totalLabs, 0);
  const totalCompletedLabs = TRACK_STATS.reduce((acc, t) => acc + t.completedLabs, 0);
  const overallPercentage = Math.round((totalCompletedLabs / totalPossibleLabs) * 100);
  const averageScore = Math.round(TRACK_STATS.reduce((acc, t) => acc + t.score, 0) / TRACK_STATS.length);

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Learner Progress & Certification
          </h1>
          <p style={{ margin: '6px 0 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
            Auditable tracking of hands-on lab completions, state validator scorecards, and engineering mastery badges.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => setShowCertificate(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Award size={16} /> View Certified Credential
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <div style={{ backgroundColor: '#0d121d', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem' }}>
            <span>Curriculum Progress</span>
            <CheckCircle2 size={16} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: 8 }}>
            {overallPercentage}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: 4 }}>
            {totalCompletedLabs} of {totalPossibleLabs} Labs Mastered
          </div>
        </div>

        <div style={{ backgroundColor: '#0d121d', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem' }}>
            <span>Average SRE Score</span>
            <Trophy size={16} color="#00f2fe" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#00f2fe', marginTop: 8 }}>
            {averageScore} / 100
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
            State-based validator average
          </div>
        </div>

        <div style={{ backgroundColor: '#0d121d', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem' }}>
            <span>Mean Time to Mitigate</span>
            <Clock size={16} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: 8 }}>
            3m 14s
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: 4 }}>
            Top 5% across cohort
          </div>
        </div>

        <div style={{ backgroundColor: '#0d121d', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem' }}>
            <span>Active Tier</span>
            <ShieldCheck size={16} color="#3b82f6" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginTop: 12 }}>
            Senior SRE
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
            Level 4 Mastery Rank
          </div>
        </div>
      </div>

      {/* Track Mastery Table */}
      <div
        style={{
          backgroundColor: '#0d121d',
          border: '1px solid var(--border-subtle)',
          borderRadius: 8,
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#f8fafc', fontWeight: 700 }}>
            Domain Competency Breakdown
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>12 Core Engineering Tracks</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {TRACK_STATS.map((t, idx) => {
            const pct = Math.round((t.completedLabs / t.totalLabs) * 100);
            return (
              <div
                key={t.track}
                style={{
                  padding: '14px 20px',
                  borderBottom: idx === TRACK_STATS.length - 1 ? 'none' : '1px solid rgba(255,255,255,0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 16,
                }}
              >
                <div style={{ width: 220 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f1f5f9' }}>{t.track}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{t.category}</div>
                </div>

                <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div
                    style={{
                      flex: 1,
                      height: 8,
                      backgroundColor: '#07090e',
                      borderRadius: 4,
                      overflow: 'hidden',
                      border: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <div
                      style={{
                        width: `${pct}%`,
                        height: '100%',
                        backgroundColor: pct === 100 ? '#10b981' : '#00f2fe',
                        borderRadius: 4,
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '0.8rem', color: '#cbd5e1', width: 45, textAlign: 'right' }}>
                    {pct}%
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 160, justifyContent: 'flex-end' }}>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    {t.completedLabs}/{t.totalLabs} Labs
                  </span>
                  <span
                    className="badge badge-beginner"
                    style={{
                      color: t.score >= 90 ? '#10b981' : '#00f2fe',
                      borderColor: t.score >= 90 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(0, 242, 254, 0.3)',
                    }}
                  >
                    {t.score}% Score
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Certificate Modal */}
      {showCertificate && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(7, 9, 14, 0.9)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 720,
              backgroundColor: '#0d121d',
              border: '2px solid #00f2fe',
              borderRadius: 12,
              padding: 40,
              boxShadow: '0 0 50px rgba(0, 242, 254, 0.2)',
              position: 'relative',
              textAlign: 'center',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
              <div
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#07090e',
                }}
              >
                <Award size={36} />
              </div>
            </div>

            <div style={{ fontSize: '0.8rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#00f2fe', fontWeight: 800 }}>
              Certificate of Production Engineering Excellence
            </div>

            <h2 style={{ fontSize: '1.8rem', color: '#f8fafc', fontWeight: 800, margin: '12px 0 6px 0' }}>
              Certified Kubernetes & Site Reliability Engineer
            </h2>

            <div style={{ fontSize: '0.9rem', color: '#94a3b8', maxWidth: 500, margin: '0 auto 24px auto', lineHeight: 1.6 }}>
              This certifies that the learner has demonstrated operational proficiency in real-world root cause analysis,
              cascading failure mitigation, and state-based system validation across distributed Kubernetes architectures.
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 16,
                padding: '16px 20px',
                backgroundColor: '#07090e',
                borderRadius: 8,
                marginBottom: 28,
                border: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>VERIFIED LABS</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9' }}>{totalCompletedLabs} Completed</div>
              </div>
              <div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>SRE SCORE</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981' }}>{averageScore}% Pass Rate</div>
              </div>
              <div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>VERIFICATION ID</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#00f2fe', fontFamily: 'monospace', marginTop: 4 }}>
                  KL-2026-SRE-8842
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
              <button onClick={() => setShowCertificate(false)} className="btn btn-secondary">
                Close
              </button>
              <button
                onClick={() => {
                  alert('Certificate exported as PDF/JSON record: KL-2026-SRE-8842');
                  setShowCertificate(false);
                }}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Download size={16} /> Download Credential Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
