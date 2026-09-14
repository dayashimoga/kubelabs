import React, { useEffect, useState } from 'react';
import { DashboardData } from '../types';
import { Award, AlertOctagon, TrendingUp, CheckCircle, ArrowRight, ShieldCheck, Terminal, BookOpen } from 'lucide-react';

interface DashboardProps {
  onSelectLab: (labId: string) => void;
  onSelectIncident: (incidentId: string) => void;
  onNavigate: (view: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onSelectLab, onSelectIncident, onNavigate }) => {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetch('/api/v1/dashboard')
      .then((res) => res.json())
      .then((d) => setData(d))
      .catch((err) => console.error('Error loading dashboard:', err));
  }, []);

  if (!data) {
    return <div style={{ padding: 40, color: '#94a3b8' }}>Loading SRE Dashboard...</div>;
  }

  return (
    <div style={{ padding: '28px 36px', display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Top Banner */}
      <div
        className="glass-panel"
        style={{
          padding: 24,
          background: 'linear-gradient(135deg, rgba(20, 27, 45, 0.8) 0%, rgba(13, 18, 29, 0.9) 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '0.85rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase' }}>
            Site Reliability Engineering Console
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4 }}>
            Welcome back, <span style={{ color: '#f1f5f9' }}>{data.user.username}</span>
          </h1>
          <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: 4 }}>
            Role: <strong style={{ color: '#cbd5e1' }}>{data.user.role}</strong> | Rank:{' '}
            <span style={{ color: '#00f2fe', fontWeight: 600 }}>{data.user.troubleshooting_rating}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00f2fe' }}>{data.user.overall_mastery}%</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Overall Mastery</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#10b981' }}>{data.user.labs_completed}</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Labs Completed</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f59e0b' }}>{data.user.incidents_resolved}</div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>SEV Incidents Solved</div>
          </div>
        </div>
      </div>

      {/* Recommended Next Topic Banner */}
      {data.recommended_next && (
        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            borderLeft: '4px solid #00f2fe',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                backgroundColor: 'rgba(0, 242, 254, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={20} color="#00f2fe" />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#00f2fe', fontWeight: 600 }}>
                RECOMMENDED NEXT PRACTICE
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9' }}>
                {data.recommended_next.title}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{data.recommended_next.reason}</div>
            </div>
          </div>
          <button
            onClick={() => onSelectIncident(data.recommended_next.id)}
            className="btn btn-primary"
          >
            Launch Scenario <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* Grid: Technology Mastery & Weak Areas */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
        {/* Technology Mastery Breakdown */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>Technology Mastery Radar</div>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>12 Disciplines</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
            {data.radar.map((r, idx) => (
              <div key={idx} style={{ backgroundColor: '#0d121d', padding: 12, borderRadius: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, color: '#f1f5f9' }}>{r.technology}</span>
                  <span style={{ color: '#00f2fe', fontWeight: 700 }}>{r.mastery}%</span>
                </div>
                {/* Progress bar */}
                <div style={{ width: '100%', height: 6, backgroundColor: '#1e293b', borderRadius: 3, overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${r.mastery}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #3b82f6 0%, #00f2fe 100%)',
                    }}
                  />
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 4 }}>
                  {r.labs_count} hands-on labs completed
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weak Areas & Targeted Training */}
        <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
            <AlertOctagon size={18} color="#f59e0b" />
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>Weak Areas & Remediation</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1 }}>
            {data.weak_areas.map((w, idx) => (
              <div
                key={idx}
                style={{
                  padding: 14,
                  borderRadius: 6,
                  backgroundColor: '#0d121d',
                  borderLeft: `3px solid ${w.severity === 'High' ? '#f43f5e' : '#f59e0b'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f1f5f9' }}>{w.topic}</span>
                  <span
                    className={w.severity === 'High' ? 'badge badge-production' : 'badge badge-intermediate'}
                    style={{ fontSize: '0.65rem' }}
                  >
                    {w.severity} Priority
                  </span>
                </div>
                <div style={{ fontSize: '0.775rem', color: '#94a3b8', marginTop: 6 }}>
                  {w.recommendation}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => onNavigate('assessments')}
            className="btn btn-secondary"
            style={{ marginTop: 16, width: '100%' }}
          >
            Take Skill Diagnostic Quiz
          </button>
        </div>
      </div>
    </div>
  );
};
