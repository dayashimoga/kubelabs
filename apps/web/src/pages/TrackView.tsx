import React, { useState, useEffect } from 'react';
import { LabSummary } from '../types';
import { Terminal, Shield, Cpu, BookOpen, Layers, ArrowRight, CheckCircle2 } from 'lucide-react';

interface TrackViewProps {
  onSelectLab: (labId: string) => void;
}

export const TrackView: React.FC<TrackViewProps> = ({ onSelectLab }) => {
  const [labs, setLabs] = useState<LabSummary[]>([]);
  const [tracks, setTracks] = useState<string[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<string>('all');

  useEffect(() => {
    fetch('/api/v1/labs/tracks')
      .then((res) => res.json())
      .then((data) => setTracks(data.tracks || []));

    fetch('/api/v1/labs')
      .then((res) => res.json())
      .then((data) => setLabs(data || []));
  }, []);

  const labList = Array.isArray(labs) ? labs : [];
  const filteredLabs = selectedTrack === 'all' ? labList : labList.filter((l) => l.track === selectedTrack);

  return (
    <div style={{ padding: '28px 36px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div
        className="glass-panel"
        style={{
          padding: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase' }}>
            Hands-on DevOps & SRE Catalog
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4 }}>
            Explore Hands-on Real-World Labs
          </h1>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 4 }}>
            Learn → Practice → Break → Troubleshoot → Fix → Validate → Explain → Master
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setSelectedTrack('all')}
            className={`btn ${selectedTrack === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
          >
            All Tracks ({labs.length})
          </button>
          {tracks.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTrack(t)}
              className={`btn ${selectedTrack === t ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Labs Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 18 }}>
        {filteredLabs.map((lab) => (
          <div
            key={lab.id}
            className="glass-panel glass-panel-hover"
            style={{
              padding: 20,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: 180,
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span className="badge badge-intermediate" style={{ fontSize: '0.65rem' }}>
                  {lab.track}
                </span>
                <span
                  className={
                    lab.difficulty === 'beginner'
                      ? 'badge badge-beginner'
                      : lab.difficulty === 'production'
                      ? 'badge badge-production'
                      : 'badge badge-intermediate'
                  }
                  style={{ fontSize: '0.65rem' }}
                >
                  {lab.difficulty}
                </span>
              </div>

              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>
                {lab.title}
              </div>

              {lab.objectives && lab.objectives.length > 0 && (
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.4 }}>
                  • {lab.objectives[0]}
                </div>
              )}
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: 16,
                paddingTop: 12,
                borderTop: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Est. {lab.estimated_minutes} mins |{' '}
                <span style={{ color: '#10b981', fontWeight: 600 }}>{lab.validation_status}</span>
              </div>
              <button
                onClick={() => onSelectLab(lab.id)}
                className="btn btn-primary"
                style={{ padding: '4px 12px', fontSize: '0.75rem' }}
              >
                Start Lab <ArrowRight size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
