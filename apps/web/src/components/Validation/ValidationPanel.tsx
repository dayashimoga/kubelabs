import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { ValidationReport } from '../../types';

interface ValidationPanelProps {
  report: ValidationReport | null;
  onValidate: () => void;
  isValidating: boolean;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ report, onValidate, isValidating }) => {
  return (
    <div
      style={{
        padding: 16,
        backgroundColor: '#0d121d',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldCheck size={16} color="#00f2fe" />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
            State-Based Validator
          </span>
        </div>
        <button
          onClick={onValidate}
          disabled={isValidating}
          className="btn btn-primary"
          style={{ padding: '6px 14px', fontSize: '0.8rem' }}
        >
          {isValidating ? 'Validating State...' : 'Run State Validation'}
        </button>
      </div>

      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Status Header */}
          <div
            style={{
              padding: 12,
              borderRadius: 6,
              backgroundColor:
                report.overall_status === 'PASS'
                  ? 'rgba(16, 185, 129, 0.1)'
                  : report.overall_status === 'PARTIAL'
                  ? 'rgba(245, 158, 11, 0.1)'
                  : 'rgba(244, 63, 94, 0.1)',
              border: `1px solid ${
                report.overall_status === 'PASS'
                  ? '#10b981'
                  : report.overall_status === 'PARTIAL'
                  ? '#f59e0b'
                  : '#f43f5e'
              }`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {report.overall_status === 'PASS' ? (
                <CheckCircle2 size={18} color="#10b981" />
              ) : report.overall_status === 'PARTIAL' ? (
                <AlertTriangle size={18} color="#f59e0b" />
              ) : (
                <XCircle size={18} color="#f43f5e" />
              )}
              <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                STATUS: {report.overall_status} ({report.total_score} / {report.max_possible_score} pts)
              </span>
            </div>
            <span style={{ fontWeight: 700, fontSize: '1rem', color: '#00f2fe' }}>
              {report.percentage}%
            </span>
          </div>

          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{report.summary}</div>

          {/* Rule Breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
            {report.items.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 12px',
                  borderRadius: 4,
                  backgroundColor: '#141b2d',
                  border: '1px solid rgba(255,255,255,0.05)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 8,
                }}
              >
                {item.passed ? (
                  <CheckCircle2 size={14} color="#10b981" style={{ marginTop: 2, flexShrink: 0 }} />
                ) : (
                  <XCircle size={14} color="#f43f5e" style={{ marginTop: 2, flexShrink: 0 }} />
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9' }}>
                      {item.description}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: item.passed ? '#10b981' : '#f43f5e', fontWeight: 600 }}>
                      {item.score_awarded} / {item.max_score} pts
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: item.passed ? '#94a3b8' : '#f87171', marginTop: 2 }}>
                    {item.feedback}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
