import React, { useState, useEffect } from 'react';
import { LabDetail, ValidationReport } from '../types';
import { TerminalView } from '../components/Terminal/TerminalView';
import { CodeEditor } from '../components/Editor/CodeEditor';
import { TopologyViewer } from '../components/Topology/TopologyViewer';
import { TelemetryViewer } from '../components/Telemetry/TelemetryViewer';
import { LayeredHintsDialog } from '../components/Hints/LayeredHintsDialog';
import { ValidationPanel } from '../components/Validation/ValidationPanel';
import {
  BookOpen,
  Terminal as TermIcon,
  ShieldAlert,
  Cpu,
  Layers,
  HelpCircle,
  Activity,
  Maximize2,
  Minimize2,
  RotateCcw,
  ShieldCheck,
  FileCode,
  CheckCircle2,
} from 'lucide-react';

interface LabWorkspaceProps {
  labId: string;
  onBack: () => void;
}

export const LabWorkspace: React.FC<LabWorkspaceProps> = ({ labId, onBack }) => {
  const [lab, setLab] = useState<LabDetail | null>(null);
  const [session, setSession] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'instructions' | 'architecture' | 'editor' | 'telemetry' | 'resources'>('instructions');
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [isTerminalFullscreen, setIsTerminalFullscreen] = useState(false);
  const [isEditorFullscreen, setIsEditorFullscreen] = useState(false);
  const [editorContent, setEditorContent] = useState<string>(
    '# Configuration file\napiVersion: v1\nkind: Pod\nmetadata:\n  name: app\n'
  );

  useEffect(() => {
    // 1. Fetch lab details
    fetch(`/api/v1/labs/${labId}`)
      .then((res) => res.json())
      .then((data) => {
        setLab(data);
        if (data.initial_state?.files?.[0]?.content) {
          setEditorContent(data.initial_state.files[0].content);
        }
      });

    // 2. Start sandbox session
    fetch(`/api/v1/labs/${labId}/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_simulation: false }),
    })
      .then((res) => res.json())
      .then((s) => setSession(s))
      .catch((err) => console.error('Error starting lab session:', err));
  }, [labId]);

  const handleRunValidation = async () => {
    if (!session || !lab?.tasks?.[0]) return;
    setIsValidating(true);
    try {
      const res = await fetch(`/api/v1/labs/session/${session.session_id}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: lab.tasks[0].id }),
      });
      const report = await res.json();
      setValidationReport(report);
    } catch (e) {
      console.error(e);
    } finally {
      setIsValidating(false);
    }
  };

  const handleResetEnvironment = async () => {
    if (!session) return;
    setIsResetting(true);
    try {
      const res = await fetch(`/api/v1/labs/session/${session.session_id}/reset`, { method: 'POST' });
      const data = await res.json();
      if (data.reset) {
        setResetMessage('Sandbox environment reset to initial failure state.');
        setTimeout(() => setResetMessage(null), 4000);
      }
    } catch (e) {
      console.error('Failed to reset sandbox:', e);
    } finally {
      setIsResetting(false);
    }
  };

  const handleAskAdvisor = async (question: string) => {
    if (!session || !lab?.tasks?.[0]) return { guidance: 'Session not active.' };
    const res = await fetch(`/api/v1/labs/session/${session.session_id}/advisor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: lab.tasks[0].id,
        question: question,
      }),
    });
    return res.json();
  };

  const getRuntimeBadge = (classification?: string) => {
    const cls = classification || session?.runtime_classification || 'REAL';
    if (cls === 'REAL') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontSize: '0.7rem', fontWeight: 700, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          ● REAL RUNTIME
        </span>
      );
    } else if (cls === 'EMULATED') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', fontSize: '0.7rem', fontWeight: 700, border: '1px solid rgba(245, 158, 11, 0.3)' }}>
          ● EMULATED
        </span>
      );
    } else if (cls === 'SIMULATED') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(0, 242, 254, 0.15)', color: '#00f2fe', fontSize: '0.7rem', fontWeight: 700, border: '1px solid rgba(0, 242, 254, 0.3)' }}>
          ● SIMULATED
        </span>
      );
    } else {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px', borderRadius: 4, backgroundColor: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', fontSize: '0.7rem', fontWeight: 700, border: '1px solid rgba(168, 85, 247, 0.3)' }}>
          ● CLOUD-REQUIRED
        </span>
      );
    }
  };

  if (!lab || !session) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16 }}>
        <div style={{ width: 40, height: 40, border: '3px solid rgba(0,242,254,0.2)', borderTopColor: '#00f2fe', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Initializing isolated rootless container sandbox environment for <strong style={{ color: '#00f2fe' }}>{labId}</strong>...
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Workspace Header */}
      <div
        style={{
          height: 52,
          padding: '0 20px',
          backgroundColor: '#0d121d',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={onBack} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
            ← All Labs
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9' }}>{lab.title}</span>
            <span className="badge badge-intermediate" style={{ fontSize: '0.65rem' }}>
              {lab.track}
            </span>
            {getRuntimeBadge(session?.runtime_classification)}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {resetMessage && (
            <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>
              ✓ {resetMessage}
            </span>
          )}

          <button
            onClick={handleResetEnvironment}
            disabled={isResetting}
            className="btn btn-secondary"
            style={{ padding: '5px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
            title="Reset sandbox to initial failure state"
          >
            <RotateCcw size={13} /> {isResetting ? 'Resetting...' : 'Reset'}
          </button>

          <div style={{ height: 20, width: 1, backgroundColor: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />

          <button
            onClick={() => setActiveTab('instructions')}
            className="btn"
            style={{
              padding: '5px 12px',
              fontSize: '0.75rem',
              backgroundColor: activeTab === 'instructions' ? '#141b2d' : 'transparent',
              color: activeTab === 'instructions' ? '#00f2fe' : '#94a3b8',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <BookOpen size={13} /> Guide
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className="btn"
            style={{
              padding: '5px 12px',
              fontSize: '0.75rem',
              backgroundColor: activeTab === 'architecture' ? '#141b2d' : 'transparent',
              color: activeTab === 'architecture' ? '#00f2fe' : '#94a3b8',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <Layers size={13} /> Topology
          </button>
          <button
            onClick={() => setActiveTab('editor')}
            className="btn"
            style={{
              padding: '5px 12px',
              fontSize: '0.75rem',
              backgroundColor: activeTab === 'editor' ? '#141b2d' : 'transparent',
              color: activeTab === 'editor' ? '#00f2fe' : '#94a3b8',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <Cpu size={13} /> Editor
          </button>
          <button
            onClick={() => setActiveTab('telemetry')}
            className="btn"
            style={{
              padding: '5px 12px',
              fontSize: '0.75rem',
              backgroundColor: activeTab === 'telemetry' ? '#141b2d' : 'transparent',
              color: activeTab === 'telemetry' ? '#00f2fe' : '#94a3b8',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <Activity size={13} /> Telemetry
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className="btn"
            style={{
              padding: '5px 12px',
              fontSize: '0.75rem',
              backgroundColor: activeTab === 'resources' ? '#141b2d' : 'transparent',
              color: activeTab === 'resources' ? '#00f2fe' : '#94a3b8',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <FileCode size={13} /> Resources
          </button>
        </div>
      </div>

      {/* Main Multi-Panel Workspace */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: isTerminalFullscreen ? '0 1fr' : isEditorFullscreen ? '1fr 0' : '1.1fr 1.3fr', overflow: 'hidden' }}>
        {/* Left Column: Context / Instructions / Editor / Resources */}
        {!isTerminalFullscreen && (
          <div
            style={{
              borderRight: '1px solid rgba(255,255,255,0.08)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto',
              padding: 20,
              gap: 16,
            }}
          >
            {activeTab === 'instructions' && (
              <>
                <div className="glass-panel" style={{ padding: 18 }}>
                  <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase' }}>
                    Objectives & SRE Workflow
                  </div>
                  <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                    {lab.objectives.map((obj, i) => (
                      <li key={i}>{obj}</li>
                    ))}
                  </ul>
                </div>

                {lab.what_why && (
                  <div className="glass-panel" style={{ padding: 18 }}>
                    <div style={{ fontSize: '0.8rem', color: '#3b82f6', fontWeight: 600, textTransform: 'uppercase' }}>
                      What & Why It Matters
                    </div>
                    <div style={{ marginTop: 6, fontSize: '0.825rem', color: '#94a3b8', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                      {lab.what_why}
                    </div>
                  </div>
                )}

                {/* Troubleshooting Workflow Steps */}
                {lab.troubleshooting_workflow && lab.troubleshooting_workflow.length > 0 && (
                  <div className="glass-panel" style={{ padding: 18 }}>
                    <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 600, textTransform: 'uppercase' }}>
                      Recommended Diagnostic Steps
                    </div>
                    <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {lab.troubleshooting_workflow.map((st: any, idx) => (
                        <div
                          key={idx}
                          style={{
                            fontSize: '0.8rem',
                            color: '#f1f5f9',
                            padding: '6px 10px',
                            backgroundColor: '#0d121d',
                            borderRadius: 4,
                            fontFamily: 'monospace',
                          }}
                        >
                          {typeof st === 'string' ? st : JSON.stringify(st)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {activeTab === 'architecture' && <TopologyViewer topology={lab.topology} />}

            {activeTab === 'editor' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 450 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                    {lab.initial_state?.files?.[0]?.path || 'config.yaml'}
                  </span>
                  <button
                    onClick={() => setIsEditorFullscreen(!isEditorFullscreen)}
                    className="btn btn-secondary"
                    style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                  >
                    {isEditorFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
                  </button>
                </div>
                <div style={{ flex: 1 }}>
                  <CodeEditor
                    filename={lab.initial_state?.files?.[0]?.path || 'config.yaml'}
                    initialContent={editorContent}
                    onSave={(newVal) => setEditorContent(newVal)}
                  />
                </div>
              </div>
            )}

            {activeTab === 'telemetry' && <TelemetryViewer />}

            {activeTab === 'resources' && (
              <div className="glass-panel" style={{ padding: 18 }}>
                <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase', marginBottom: 12 }}>
                  Environment Resources & Security Constraints
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: '0.8rem', color: '#94a3b8' }}>
                  <div style={{ padding: 10, backgroundColor: '#0d121d', borderRadius: 6 }}>
                    <div style={{ color: '#64748b', fontSize: '0.7rem' }}>CONTAINER RUNTIME</div>
                    <div style={{ color: '#f8fafc', fontWeight: 600, marginTop: 4 }}>Rootless Podman / Cgroups v2</div>
                  </div>
                  <div style={{ padding: 10, backgroundColor: '#0d121d', borderRadius: 6 }}>
                    <div style={{ color: '#64748b', fontSize: '0.7rem' }}>MEMORY / CPU QUOTA</div>
                    <div style={{ color: '#f8fafc', fontWeight: 600, marginTop: 4 }}>512 MB / 1.0 Core</div>
                  </div>
                  <div style={{ padding: 10, backgroundColor: '#0d121d', borderRadius: 6 }}>
                    <div style={{ color: '#64748b', fontSize: '0.7rem' }}>CAPABILITIES DROPPED</div>
                    <div style={{ color: '#ef4444', fontWeight: 600, marginTop: 4 }}>ALL (Full Isolation)</div>
                  </div>
                  <div style={{ padding: 10, backgroundColor: '#0d121d', borderRadius: 6 }}>
                    <div style={{ color: '#64748b', fontSize: '0.7rem' }}>CLEANUP TTL</div>
                    <div style={{ color: '#10b981', fontWeight: 600, marginTop: 4 }}>30 Minutes Sweeper</div>
                  </div>
                </div>

                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: 8 }}>
                    Staged Failure Manifests
                  </div>
                  {lab.initial_state?.files?.map((f, idx) => (
                    <div key={idx} style={{ padding: '8px 12px', backgroundColor: '#0d121d', borderRadius: 6, marginBottom: 6, fontFamily: 'monospace', fontSize: '0.8rem', color: '#cbd5e1' }}>
                      {f.path} ({(f as any).permissions || '0644'})
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Layered Hints Assistant */}
            <LayeredHintsDialog hints={lab.tasks?.[0]?.hints || []} onAskAdvisor={handleAskAdvisor} />
          </div>
        )}

        {/* Right Column: Terminal & Validation Panel */}
        {!isEditorFullscreen && (
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 16, gap: 14 }}>
            {/* Interactive Shell Terminal */}
            <div style={{ flex: 1, minHeight: 300, display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 6 }}>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
                  INTERACTIVE SRE PTY SHELL ({session.session_id})
                </span>
                <button
                  onClick={() => setIsTerminalFullscreen(!isTerminalFullscreen)}
                  className="btn btn-secondary"
                  style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                  title={isTerminalFullscreen ? 'Exit Fullscreen' : 'Fullscreen Terminal'}
                >
                  {isTerminalFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
                </button>
              </div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <TerminalView
                  sessionId={session.session_id}
                  isContainer={session.is_container}
                  onCommandRun={(cmd) => console.log('Command executed:', cmd)}
                />
              </div>
            </div>

            {/* Validation Engine Panel */}
            <div style={{ flexShrink: 0 }}>
              <ValidationPanel
                report={validationReport}
                onValidate={handleRunValidation}
                isValidating={isValidating}
              />
            </div>

            {/* Zero Residue Status Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 12px', backgroundColor: '#0a0e17', borderRadius: 4, border: '1px solid rgba(255,255,255,0.05)', fontSize: '0.7rem', color: '#64748b' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#10b981' }}>
                <ShieldCheck size={13} /> Zero-Residue Lifecycle Active
              </span>
              <span>Session ID: {session.session_id}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
