import React, { useState, useEffect } from 'react';
import { IncidentSummary, IncidentDetail, IncidentScore } from '../types';
import { TopologyViewer } from '../components/Topology/TopologyViewer';
import { TelemetryViewer } from '../components/Telemetry/TelemetryViewer';
import { TerminalView } from '../components/Terminal/TerminalView';
import { AlertOctagon, Flame, ShieldCheck, CheckCircle, HelpCircle, Activity, Award } from 'lucide-react';

interface IncidentSimulatorProps {
  initialIncidentId?: string;
}

export const IncidentSimulator: React.FC<IncidentSimulatorProps> = ({ initialIncidentId }) => {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [activeId, setActiveId] = useState<string>(initialIncidentId || 'checkout-latency-spike');
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [session, setSession] = useState<any>(null);
  const [hypothesesResults, setHypothesesResults] = useState<{ [id: string]: any }>({});
  const [mitigationCmd, setMitigationCmd] = useState('');
  const [mitigationStatus, setMitigationStatus] = useState<any>(null);
  const [finalScore, setFinalScore] = useState<IncidentScore | null>(null);

  useEffect(() => {
    fetch('/api/v1/incidents')
      .then((res) => res.json())
      .then((data) => setIncidents(data));
  }, []);

  useEffect(() => {
    if (!activeId) return;

    fetch(`/api/v1/incidents/${activeId}`)
      .then((res) => res.json())
      .then((data) => setIncident(data));

    // Start live incident session
    fetch(`/api/v1/incidents/${activeId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: `inc-${Date.now().toString().slice(-6)}` }),
    })
      .then((res) => res.json())
      .then((s) => {
        setSession(s);
        setFinalScore(null);
        setMitigationStatus(null);
      });
  }, [activeId]);

  const handleTestHypothesis = async (hypId: string) => {
    if (!session) return;
    const res = await fetch(`/api/v1/incidents/session/${session.session_id}/hypothesis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hypothesis_id: hypId }),
    });
    const data = await res.json();
    setHypothesesResults((prev) => ({ ...prev, [hypId]: data }));
  };

  const handleApplyMitigation = async () => {
    if (!session || !mitigationCmd) return;
    const res = await fetch(`/api/v1/incidents/session/${session.session_id}/mitigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: mitigationCmd }),
    });
    const data = await res.json();
    setMitigationStatus(data);
  };

  const handleResolve = async () => {
    if (!session) return;
    const res = await fetch(`/api/v1/incidents/session/${session.session_id}/resolve`, {
      method: 'POST',
    });
    const data = await res.json();
    setFinalScore(data.score);
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Banner */}
      <div
        className="glass-panel"
        style={{
          padding: 20,
          background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.15) 0%, rgba(13, 18, 29, 0.9) 100%)',
          borderLeft: '4px solid #f43f5e',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <Flame size={32} color="#f43f5e" />
          <div>
            <div style={{ fontSize: '0.75rem', color: '#f43f5e', fontWeight: 700, letterSpacing: '0.05em' }}>
              LIVE SEV-1 / SEV-2 INCIDENT WAR ROOM
            </div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f1f5f9' }}>
              {incident?.title || 'Loading Scenario...'}
            </h1>
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: 2 }}>{incident?.impact}</div>
          </div>
        </div>

        {/* Incident Selector */}
        <select
          value={activeId}
          onChange={(e) => setActiveId(e.target.value)}
          style={{
            padding: '8px 14px',
            borderRadius: 6,
            backgroundColor: '#141b2d',
            color: '#f1f5f9',
            border: '1px solid rgba(255,255,255,0.15)',
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          {incidents.map((inc) => (
            <option key={inc.id} value={inc.id}>
              [{inc.severity}] {inc.title}
            </option>
          ))}
        </select>
      </div>

      {/* Grid: Topology & Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.2fr', gap: 20 }}>
        {/* Left Column: Topology & Hypotheses */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {incident && <TopologyViewer topology={incident.topology} />}

          {/* Initial Symptoms */}
          <div className="glass-panel" style={{ padding: 18 }}>
            <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 600, textTransform: 'uppercase' }}>
              Detected Symptoms & Alerts
            </div>
            <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: '0.825rem', color: '#cbd5e1', lineHeight: 1.6 }}>
              {incident?.initial_symptoms.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>

          {/* SRE Hypotheses Testing */}
          <div className="glass-panel" style={{ padding: 18 }}>
            <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase' }}>
              Investigate & Test Hypotheses
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
              {incident?.hypotheses.map((h) => {
                const result = hypothesesResults[h.id];
                return (
                  <div key={h.id} style={{ backgroundColor: '#0d121d', padding: 10, borderRadius: 6 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9' }}>{h.statement}</span>
                      <button
                        onClick={() => handleTestHypothesis(h.id)}
                        className="btn btn-secondary"
                        style={{ padding: '3px 8px', fontSize: '0.7rem' }}
                      >
                        Test Hypothesis
                      </button>
                    </div>
                    {result && (
                      <div
                        style={{
                          marginTop: 6,
                          fontSize: '0.75rem',
                          color: result.disproven_by ? '#f43f5e' : '#10b981',
                        }}
                      >
                        {result.disproven_by ? `Disproven: ${result.disproven_by}` : 'Supported by telemetry!'}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Telemetry & Mitigation Terminal */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ height: 320 }}>
            <TelemetryViewer isPerturbed={!finalScore} />
          </div>

          {/* Mitigation Command Box */}
          <div className="glass-panel" style={{ padding: 18 }}>
            <div style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 600, textTransform: 'uppercase' }}>
              Execute SRE Remediation & Mitigation
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <input
                type="text"
                value={mitigationCmd}
                onChange={(e) => setMitigationCmd(e.target.value)}
                placeholder="e.g. kubectl rollout restart deployment/checkout-service"
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 6,
                  backgroundColor: '#07090e',
                  color: '#f1f5f9',
                  border: '1px solid rgba(255,255,255,0.1)',
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                }}
              />
              <button onClick={handleApplyMitigation} className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
                Apply Fix
              </button>
            </div>

            {mitigationStatus && (
              <div
                style={{
                  marginTop: 10,
                  fontSize: '0.8rem',
                  padding: 8,
                  borderRadius: 4,
                  backgroundColor: mitigationStatus.mitigated ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                  color: mitigationStatus.mitigated ? '#10b981' : '#f43f5e',
                }}
              >
                {mitigationStatus.feedback}
              </div>
            )}

            <button
              onClick={handleResolve}
              className="btn btn-secondary"
              style={{ marginTop: 12, width: '100%', borderColor: '#10b981', color: '#10b981' }}
            >
              Verify Incident Resolution & Generate Scorecard
            </button>
          </div>

          {/* SRE Scorecard Modal / Panel */}
          {finalScore && (
            <div
              className="glass-panel"
              style={{
                padding: 20,
                borderLeft: '4px solid #10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Award size={20} color="#10b981" />
                <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f1f5f9' }}>
                  SRE Post-Mortem Score: {finalScore.total_score} / 100
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, fontSize: '0.75rem' }}>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Detection: <strong>{finalScore.detection_score}%</strong>
                </div>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Investigation: <strong>{finalScore.investigation_score}%</strong>
                </div>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Root Cause: <strong>{finalScore.root_cause_score}%</strong>
                </div>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Fix Correctness: <strong>{finalScore.fix_score}%</strong>
                </div>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Verification: <strong>{finalScore.verification_score}%</strong>
                </div>
                <div style={{ backgroundColor: '#0d121d', padding: 8, borderRadius: 4 }}>
                  Prevention: <strong>{finalScore.prevention_score}%</strong>
                </div>
              </div>

              <div style={{ marginTop: 12, fontSize: '0.8rem', color: '#cbd5e1' }}>
                {finalScore.feedback.map((f, i) => (
                  <div key={i}>• {f}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
