import React, { useState, useEffect } from 'react';
import { LabDetail, ValidationReport } from '../types';
import { TerminalView } from '../components/Terminal/TerminalView';
import { CodeEditor } from '../components/Editor/CodeEditor';
import { TopologyViewer } from '../components/Topology/TopologyViewer';
import { TelemetryViewer } from '../components/Telemetry/TelemetryViewer';
import { LayeredHintsDialog } from '../components/Hints/LayeredHintsDialog';
import { ValidationPanel } from '../components/Validation/ValidationPanel';
import { BookOpen, Terminal as TermIcon, ShieldAlert, Cpu, Layers, HelpCircle, Activity } from 'lucide-react';

interface LabWorkspaceProps {
  labId: string;
  onBack: () => void;
}

export const LabWorkspace: React.FC<LabWorkspaceProps> = ({ labId, onBack }) => {
  const [lab, setLab] = useState<LabDetail | null>(null);
  const [session, setSession] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'instructions' | 'architecture' | 'editor' | 'telemetry'>('instructions');
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [isValidating, setIsValidating] = useState(false);
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

  if (!lab || !session) {
    return (
      <div style={{ padding: 40, color: '#94a3b8' }}>
        Initializing isolated sandbox container environment for {labId}...
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
          <div>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f1f5f9' }}>{lab.title}</span>
            <span className="badge badge-intermediate" style={{ marginLeft: 10, fontSize: '0.65rem' }}>
              {lab.track}
            </span>
            <span className="badge badge-beginner" style={{ marginLeft: 6, fontSize: '0.65rem' }}>
              {lab.validation_status}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
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
            <BookOpen size={13} /> Instructions
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
            <Cpu size={13} /> Config Editor
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
        </div>
      </div>

      {/* Main Multi-Panel Workspace */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.2fr 1.3fr', overflow: 'hidden' }}>
        {/* Left Column: Context / Instructions / Editor */}
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
                  <div style={{ marginTop: 6, fontSize: '0.825rem', color: '#94a3b8', whiteSpace: 'pre-wrap' }}>
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
            <div style={{ height: '500px' }}>
              <CodeEditor
                filename={lab.initial_state?.files?.[0]?.path || 'config.yaml'}
                initialContent={editorContent}
                onSave={(newVal) => setEditorContent(newVal)}
              />
            </div>
          )}

          {activeTab === 'telemetry' && <TelemetryViewer />}

          {/* Layered Hints Assistant */}
          <LayeredHintsDialog hints={lab.tasks?.[0]?.hints || []} onAskAdvisor={handleAskAdvisor} />
        </div>

        {/* Right Column: Terminal & Validation Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 16, gap: 14 }}>
          {/* Interactive Shell Terminal */}
          <div style={{ flex: 1, minHeight: 300 }}>
            <TerminalView
              sessionId={session.session_id}
              isContainer={session.is_container}
              onCommandRun={(cmd) => console.log('Command executed:', cmd)}
            />
          </div>

          {/* Validation Engine Panel */}
          <div style={{ flexShrink: 0 }}>
            <ValidationPanel
              report={validationReport}
              onValidate={handleRunValidation}
              isValidating={isValidating}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
