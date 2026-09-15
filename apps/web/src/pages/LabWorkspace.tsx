import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LabDetail, ValidationReport } from '../types';
import { getApiBase } from '../config';
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
  Clock,
  RefreshCw,
  AlertTriangle,
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

  // Resizable split-pane state
  const [leftWidthPercent, setLeftWidthPercent] = useState<number>(45);
  const [isDragging, setIsDragging] = useState(false);

  // Session countdown timer state
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [provisionError, setProvisionError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // 1. Fetch lab details
  useEffect(() => {
    fetch(`${getApiBase()}/api/v1/labs/${labId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Lab ${labId} not found`);
        return res.json();
      })
      .then((data) => {
        setLab(data);
        if (data.initial_state?.files?.[0]?.content) {
          setEditorContent(data.initial_state.files[0].content);
        }
      })
      .catch((err) => setProvisionError(err.message));
  }, [labId]);

  // 2. Start sandbox session
  const initSession = useCallback((forceSimulation: boolean = false) => {
    setProvisionError(null);
    setIsRetrying(true);
    fetch(`${getApiBase()}/api/v1/labs/${labId}/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_simulation: forceSimulation }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const errData = await res.json().catch(() => ({ detail: 'Unknown provisioning failure' }));
          throw new Error(errData.detail || `Server returned HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((s) => {
        setSession(s);
        setProvisionError(null);
      })
      .catch((err) => {
        console.error('Error starting lab session:', err);
        setProvisionError(err.message);
      })
      .finally(() => setIsRetrying(false));
  }, [labId]);

  useEffect(() => {
    initSession(false);
  }, [initSession]);

  // Live countdown timer ticking every second
  useEffect(() => {
    if (!session?.expires_at) return;

    const updateTimer = () => {
      const now = Date.now() / 1000;
      const rem = Math.max(0, Math.floor(session.expires_at - now));
      setTimeLeft(rem);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [session?.expires_at]);

  // Drag handlers for resizable panels
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const newPercent = (e.clientX / window.innerWidth) * 100;
      if (newPercent >= 25 && newPercent <= 75) {
        setLeftWidthPercent(newPercent);
      }
    };

    const handleMouseUp = () => {
      if (isDragging) setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleSaveFile = async (contentToSave: string, targetPath?: string) => {
    setEditorContent(contentToSave);
    if (!session) return;
    const filePath = targetPath || lab?.initial_state?.files?.[0]?.path || '/workspace/service.yaml';
    try {
      await fetch(`${getApiBase()}/api/v1/labs/session/${session.session_id}/file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: filePath, content: contentToSave }),
      });
    } catch (err) {
      console.error('Failed to sync saved file:', err);
    }
  };

  const handleRunValidation = async () => {
    if (!session || !lab?.tasks?.[0]) return;
    setIsValidating(true);
    try {
      const filePath = lab?.initial_state?.files?.[0]?.path || '/workspace/service.yaml';
      if (editorContent) {
        await fetch(`${getApiBase()}/api/v1/labs/session/${session.session_id}/file`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: filePath, content: editorContent }),
        }).catch((e) => console.warn('Could not sync file before validation', e));
      }

      const res = await fetch(`${getApiBase()}/api/v1/labs/session/${session.session_id}/validate`, {
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
      const res = await fetch(`${getApiBase()}/api/v1/labs/session/${session.session_id}/reset`, { method: 'POST' });
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
    const res = await fetch(`${getApiBase()}/api/v1/labs/session/${session.session_id}/advisor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: lab.tasks[0].id,
        question: question,
      }),
    });
    return res.json();
  };

  const formatCountdown = (seconds: number | null) => {
    if (seconds === null) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
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

  // Error screen when provisioning fails
  if (provisionError) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 40, gap: 20 }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
          <AlertTriangle size={32} />
        </div>
        <div style={{ textAlign: 'center', maxWidth: 600 }}>
          <h2 style={{ color: '#f8fafc', fontSize: '1.4rem', margin: '0 0 10px 0' }}>Runtime Provisioning Failed</h2>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6, margin: '0 0 20px 0', fontFamily: 'monospace', backgroundColor: '#0d121d', padding: 14, borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)' }}>
            {provisionError}
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <button onClick={() => initSession(false)} disabled={isRetrying} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <RefreshCw size={14} className={isRetrying ? 'animate-spin' : ''} />
              Retry Real Sandbox
            </button>
            <button onClick={() => initSession(true)} disabled={isRetrying} className="btn btn-secondary">
              Launch in Simulation Mode
            </button>
            <button onClick={onBack} className="btn btn-secondary">
              ← Return to Catalog
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Loading screen
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }} role="region" aria-label="SRE Lab Workspace">
      {/* Top Workspace Header */}
      <header
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
          <button onClick={onBack} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} aria-label="Back to labs catalog">
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

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Live TTL Countdown Timer */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 10px',
              borderRadius: 4,
              backgroundColor: timeLeft !== null && timeLeft < 300 ? 'rgba(239, 68, 68, 0.15)' : '#07090e',
              border: `1px solid ${timeLeft !== null && timeLeft < 300 ? '#ef4444' : 'rgba(255,255,255,0.1)'}`,
              color: timeLeft !== null && timeLeft < 300 ? '#ef4444' : '#cbd5e1',
              fontSize: '0.75rem',
              fontWeight: 600,
              fontFamily: 'monospace',
            }}
            title="Remaining session TTL before automatic cleanup"
          >
            <Clock size={12} /> {formatCountdown(timeLeft)}
          </div>

          {resetMessage && (
            <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }} aria-live="polite">
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
            <RotateCcw size={13} className={isResetting ? 'animate-spin' : ''} /> {isResetting ? 'Resetting...' : 'Reset'}
          </button>

          <button
            onClick={() => initSession(false)}
            className="btn btn-secondary"
            style={{ padding: '5px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
            title="Reconnect or re-sync active session"
          >
            <RefreshCw size={13} /> Reconnect
          </button>

          <div style={{ height: 20, width: 1, backgroundColor: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />

          {/* Session Health Dot */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#64748b' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }} />
            Active
          </div>
        </div>
      </header>

      {/* Main Workspace Body: Resizable Split-Pane */}
      <div
        style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: isTerminalFullscreen
            ? '0px 0px 1fr'
            : isEditorFullscreen
            ? '1fr 0px 0px'
            : `${leftWidthPercent}% 6px calc(${100 - leftWidthPercent}% - 6px)`,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Left Column: Instructions / Architecture / Editor / Telemetry */}
        {!isTerminalFullscreen && (
          <div style={{ display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: 16, gap: 14 }}>
            {/* Workspace Sub-Navigation Tabs */}
            <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: 8, flexShrink: 0 }}>
              <button
                onClick={() => setActiveTab('instructions')}
                className={`btn ${activeTab === 'instructions' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <BookOpen size={13} /> Instructions
              </button>
              <button
                onClick={() => setActiveTab('architecture')}
                className={`btn ${activeTab === 'architecture' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Layers size={13} /> Topology
              </button>
              <button
                onClick={() => setActiveTab('editor')}
                className={`btn ${activeTab === 'editor' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <FileCode size={13} /> Editor
              </button>
              <button
                onClick={() => setActiveTab('telemetry')}
                className={`btn ${activeTab === 'telemetry' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Activity size={13} /> Telemetry
              </button>
              <button
                onClick={() => setActiveTab('resources')}
                className={`btn ${activeTab === 'resources' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Cpu size={13} /> Resources
              </button>
            </div>

            {/* Tab: Instructions */}
            {activeTab === 'instructions' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="glass-panel" style={{ padding: 18 }}>
                  <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                    Lab Mission & Objectives
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                    {lab.objectives?.map((obj, i) => (
                      <li key={i}>{obj}</li>
                    ))}
                  </ul>
                </div>

                <div className="glass-panel" style={{ padding: 18 }}>
                  <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                    Architecture & Why It Matters
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                    {lab.what_why}
                  </div>
                </div>

                {lab.troubleshooting_workflow && (
                  <div className="glass-panel" style={{ padding: 18 }}>
                    <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                      Recommended Diagnostic Workflow
                    </div>
                    <ol style={{ margin: 0, paddingLeft: 18, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                      {lab.troubleshooting_workflow?.map((step, i) => (
                        <li key={i} style={{ marginBottom: 4 }}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Architecture Topology */}
            {activeTab === 'architecture' && (
              <div className="glass-panel" style={{ padding: 16, minHeight: 350 }}>
                <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase', marginBottom: 12 }}>
                  System Architecture & Dependency Topology
                </div>
                <TopologyViewer topology={lab.topology || session.topology} />
              </div>
            )}

            {/* Tab: Monaco Code Editor */}
            {activeTab === 'editor' && (
              <div style={{ flex: 1, minHeight: 400, display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 6 }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
                    MANIFEST EDITOR ({lab.initial_state?.files?.[0]?.path || 'config.yaml'})
                  </span>
                  <button
                    onClick={() => setIsEditorFullscreen(!isEditorFullscreen)}
                    className="btn btn-secondary"
                    style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                    title={isEditorFullscreen ? 'Exit Fullscreen' : 'Fullscreen Editor'}
                  >
                    {isEditorFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
                  </button>
                </div>
                <div style={{ flex: 1 }}>
                  <CodeEditor
                    filename={lab.initial_state?.files?.[0]?.path || 'config.yaml'}
                    initialContent={editorContent}
                    onSave={(newVal) => handleSaveFile(newVal, lab.initial_state?.files?.[0]?.path)}
                  />
                </div>
              </div>
            )}

            {/* Tab: Telemetry */}
            {activeTab === 'telemetry' && <TelemetryViewer />}

            {/* Tab: Resources & Security Constraints */}
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

        {/* Draggable Vertical Divider Handle */}
        {!isTerminalFullscreen && !isEditorFullscreen && (
          <div
            onMouseDown={handleMouseDown}
            style={{
              width: 6,
              backgroundColor: isDragging ? '#00f2fe' : 'rgba(255,255,255,0.06)',
              cursor: 'col-resize',
              transition: isDragging ? 'none' : 'background-color 0.2s',
              zIndex: 10,
            }}
            title="Drag to resize workspace panels"
          />
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
