import React from 'react';
import { TopologyData, TopologyNode } from '../../types';
import { Server, Database, Cloud, ShieldAlert, Cpu, HardDrive } from 'lucide-react';

interface TopologyViewerProps {
  topology?: TopologyData;
  onSelectNode?: (node: TopologyNode) => void;
}

export const TopologyViewer: React.FC<TopologyViewerProps> = ({ topology, onSelectNode }) => {
  if (!topology || !topology.nodes || topology.nodes.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#64748b' }}>
        No architecture topology graph defined for this scenario.
      </div>
    );
  }

  const getNodeColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#10b981';
      case 'degraded':
      case 'slow':
        return '#f59e0b';
      case 'failed':
      case 'broken':
        return '#f43f5e';
      default:
        return '#3b82f6';
    }
  };

  const getNodeIcon = (type: string, color: string) => {
    switch (type.toLowerCase()) {
      case 'database':
      case 'cache':
        return <Database size={16} color={color} />;
      case 'alb':
      case 'gateway':
      case 'ingress':
        return <Cloud size={16} color={color} />;
      case 'pod':
        return <Cpu size={16} color={color} />;
      case 'storage':
        return <HardDrive size={16} color={color} />;
      default:
        return <Server size={16} color={color} />;
    }
  };

  return (
    <div
      style={{
        padding: 20,
        backgroundColor: '#0d121d',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.08)',
        overflowX: 'auto',
      }}
    >
      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', marginBottom: 16 }}>
        Service Mesh & Infrastructure Topology
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center' }}>
        {topology.nodes.map((node) => {
          const color = getNodeColor(node.status);
          return (
            <div
              key={node.id}
              onClick={() => onSelectNode && onSelectNode(node)}
              className="glass-panel glass-panel-hover"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                minWidth: 170,
                borderLeft: `4px solid ${color}`,
                cursor: 'pointer',
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 6,
                  backgroundColor: `${color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {getNodeIcon(node.type, color)}
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9' }}>{node.label}</div>
                <div style={{ fontSize: '0.7rem', color: color, textTransform: 'capitalize', fontWeight: 500 }}>
                  ● {node.status}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {topology.edges && topology.edges.length > 0 && (
        <div style={{ marginTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14 }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>Traffic Edges:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {topology.edges.map((e, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: '0.75rem',
                  padding: '3px 8px',
                  borderRadius: 4,
                  backgroundColor: '#141b2d',
                  color: e.status === 'broken' || e.status === 'dropped' ? '#f43f5e' : '#94a3b8',
                  fontFamily: 'monospace',
                }}
              >
                {e.source} ➔ {e.target} {e.label ? `(${e.label})` : ''}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
