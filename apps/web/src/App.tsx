import React, { useState } from 'react';
import { Dashboard } from './pages/Dashboard';
import { TrackView } from './pages/TrackView';
import { LabWorkspace } from './pages/LabWorkspace';
import { IncidentSimulator } from './pages/IncidentSimulator';
import { Assessments } from './pages/Assessments';
import {
  LayoutDashboard,
  Terminal,
  Flame,
  Award,
  BookOpen,
  Cpu,
  Layers,
  CheckCircle2,
  Activity,
} from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'labs' | 'workspace' | 'incidents' | 'assessments'>('dashboard');
  const [selectedLabId, setSelectedLabId] = useState<string>('linux-inode-exhaustion');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('checkout-latency-spike');

  const handleLaunchLab = (labId: string) => {
    setSelectedLabId(labId);
    setCurrentView('workspace');
  };

  const handleLaunchIncident = (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setCurrentView('incidents');
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        {/* Brand Header */}
        <div
          style={{
            height: 60,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '0 20px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 6,
              background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              color: '#07090e',
              fontSize: '1rem',
            }}
          >
            ☸
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.05rem', color: '#f1f5f9', letterSpacing: '-0.02em' }}>
              Kube<span style={{ color: '#00f2fe' }}>Labs</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: '#64748b', fontWeight: 600 }}>SRE TROUBLESHOOTING</div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
          <button
            onClick={() => setCurrentView('dashboard')}
            className="btn"
            style={{
              justifyContent: 'flex-start',
              backgroundColor: currentView === 'dashboard' ? '#141b2d' : 'transparent',
              color: currentView === 'dashboard' ? '#00f2fe' : '#94a3b8',
              border: currentView === 'dashboard' ? '1px solid var(--border-accent)' : 'none',
              padding: '10px 14px',
            }}
          >
            <LayoutDashboard size={16} /> Dashboard
          </button>

          <button
            onClick={() => setCurrentView('labs')}
            className="btn"
            style={{
              justifyContent: 'flex-start',
              backgroundColor: currentView === 'labs' || currentView === 'workspace' ? '#141b2d' : 'transparent',
              color: currentView === 'labs' || currentView === 'workspace' ? '#00f2fe' : '#94a3b8',
              border: currentView === 'labs' || currentView === 'workspace' ? '1px solid var(--border-accent)' : 'none',
              padding: '10px 14px',
            }}
          >
            <Terminal size={16} /> Hands-on Labs
          </button>

          <button
            onClick={() => setCurrentView('incidents')}
            className="btn"
            style={{
              justifyContent: 'flex-start',
              backgroundColor: currentView === 'incidents' ? '#141b2d' : 'transparent',
              color: currentView === 'incidents' ? '#f43f5e' : '#94a3b8',
              border: currentView === 'incidents' ? '1px solid rgba(244, 63, 94, 0.3)' : 'none',
              padding: '10px 14px',
            }}
          >
            <Flame size={16} color={currentView === 'incidents' ? '#f43f5e' : '#94a3b8'} /> Incident Simulator
          </button>

          <button
            onClick={() => setCurrentView('assessments')}
            className="btn"
            style={{
              justifyContent: 'flex-start',
              backgroundColor: currentView === 'assessments' ? '#141b2d' : 'transparent',
              color: currentView === 'assessments' ? '#00f2fe' : '#94a3b8',
              border: currentView === 'assessments' ? '1px solid var(--border-accent)' : 'none',
              padding: '10px 14px',
            }}
          >
            <Award size={16} /> Assessments & Quizzes
          </button>
        </nav>

        {/* Runtime Footer */}
        <div
          style={{
            padding: '14px 16px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.725rem',
            color: '#64748b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>Podman 5.8 Engine Active</span>
          </div>
          <div style={{ marginTop: 4 }}>WSL2 Kernel: Linux amd64</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="badge badge-beginner">Sandbox Ready</span>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>TTL: 30m Auto-Clean</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: '#94a3b8' }}>
              <Activity size={14} color="#10b981" />
              <span>Telemetry: 0% drops</span>
            </div>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                backgroundColor: '#141b2d',
                border: '1px solid rgba(0, 242, 254, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                color: '#00f2fe',
                fontSize: '0.8rem',
              }}
            >
              SE
            </div>
          </div>
        </header>

        {/* Router View Rendering */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {currentView === 'dashboard' && (
            <Dashboard
              onSelectLab={handleLaunchLab}
              onSelectIncident={handleLaunchIncident}
              onNavigate={(v) => setCurrentView(v as any)}
            />
          )}

          {currentView === 'labs' && <TrackView onSelectLab={handleLaunchLab} />}

          {currentView === 'workspace' && (
            <LabWorkspace labId={selectedLabId} onBack={() => setCurrentView('labs')} />
          )}

          {currentView === 'incidents' && <IncidentSimulator initialIncidentId={selectedIncidentId} />}

          {currentView === 'assessments' && <Assessments />}
        </div>
      </main>
    </div>
  );
};
