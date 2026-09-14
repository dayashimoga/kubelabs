import React, { useState, useEffect } from 'react';
import { Activity, Terminal as LogIcon, GitCommit, AlertTriangle } from 'lucide-react';

interface TelemetryViewerProps {
  isPerturbed?: boolean;
}

export const TelemetryViewer: React.FC<TelemetryViewerProps> = ({ isPerturbed = false }) => {
  const [tab, setTab] = useState<'metrics' | 'logs' | 'traces'>('metrics');
  const [metrics, setMetrics] = useState<any>({
    requests_per_second: 1420.5,
    error_rate_5xx_percent: isPerturbed ? 18.4 : 0.05,
    latency_p50_ms: isPerturbed ? 95.0 : 14.2,
    latency_p95_ms: isPerturbed ? 850.0 : 48.0,
    latency_p99_ms: isPerturbed ? 3850.0 : 120.0,
    cpu_utilization_percent: isPerturbed ? 89.2 : 38.0,
  });

  const [logs, setLogs] = useState<any[]>([
    { timestamp: '10:14:02', level: 'INFO', service: 'gateway', msg: 'POST /v2/checkout HTTP/2 200' },
    { timestamp: '10:14:05', level: 'WARN', service: 'order-svc', msg: 'Connection pool saturation warning: active=195/200' },
    { timestamp: '10:14:08', level: 'ERROR', service: 'order-svc', msg: 'java.sql.SQLTransientConnectionException: HikariPool-1 timeout after 30000ms' },
    { timestamp: '10:14:10', level: 'ERROR', service: 'gateway', msg: 'upstream connect error or disconnect/reset before headers (504 Gateway Timeout)' },
  ]);

  const traces = [
    { span: 'POST /api/v2/checkout', service: 'edge-gateway', dur: '5012ms', status: 'ERROR', code: 504 },
    { span: 'OrderController.createOrder', service: 'order-svc', dur: '5008ms', status: 'ERROR', code: 'Timeout' },
    { span: 'InventoryClient.reserveSKU', service: 'inventory-svc', dur: '5000ms', status: 'ERROR', code: 'SocketTimeout' },
    { span: 'SELECT * FROM inventory FOR UPDATE', service: 'postgres', dur: '4995ms', status: 'ERROR', code: 'LockWait' },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time metric jitter
      setMetrics((prev: any) => ({
        ...prev,
        requests_per_second: (prev.requests_per_second + (Math.random() * 20 - 10)).toFixed(1),
        error_rate_5xx_percent: isPerturbed
          ? (18.0 + Math.random() * 4).toFixed(2)
          : (0.02 + Math.random() * 0.04).toFixed(3),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, [isPerturbed]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#07090e',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.08)',
        overflow: 'hidden',
      }}
    >
      {/* Tab Switcher */}
      <div
        style={{
          display: 'flex',
          backgroundColor: '#0d121d',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <button
          onClick={() => setTab('metrics')}
          style={{
            padding: '8px 16px',
            border: 'none',
            background: tab === 'metrics' ? '#141b2d' : 'transparent',
            color: tab === 'metrics' ? '#00f2fe' : '#94a3b8',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            borderBottom: tab === 'metrics' ? '2px solid #00f2fe' : 'none',
          }}
        >
          <Activity size={14} /> Live Metrics
        </button>
        <button
          onClick={() => setTab('logs')}
          style={{
            padding: '8px 16px',
            border: 'none',
            background: tab === 'logs' ? '#141b2d' : 'transparent',
            color: tab === 'logs' ? '#00f2fe' : '#94a3b8',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            borderBottom: tab === 'logs' ? '2px solid #00f2fe' : 'none',
          }}
        >
          <LogIcon size={14} /> Log Stream
        </button>
        <button
          onClick={() => setTab('traces')}
          style={{
            padding: '8px 16px',
            border: 'none',
            background: tab === 'traces' ? '#141b2d' : 'transparent',
            color: tab === 'traces' ? '#00f2fe' : '#94a3b8',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            borderBottom: tab === 'traces' ? '2px solid #00f2fe' : 'none',
          }}
        >
          <GitCommit size={14} /> OTel Traces
        </button>
      </div>

      <div style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
        {tab === 'metrics' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            <div className="glass-panel" style={{ padding: 12 }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Throughput (RPS)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#00f2fe', marginTop: 4 }}>
                {metrics.requests_per_second}
              </div>
            </div>
            <div className="glass-panel" style={{ padding: 12 }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>5xx Error Rate</div>
              <div
                style={{
                  fontSize: '1.25rem',
                  fontWeight: 700,
                  color: parseFloat(metrics.error_rate_5xx_percent) > 1.0 ? '#f43f5e' : '#10b981',
                  marginTop: 4,
                }}
              >
                {metrics.error_rate_5xx_percent}%
              </div>
            </div>
            <div className="glass-panel" style={{ padding: 12 }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Latency P50 / P99</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9', marginTop: 4 }}>
                {metrics.latency_p50_ms}ms /{' '}
                <span style={{ color: parseFloat(metrics.latency_p99_ms) > 1000 ? '#f43f5e' : '#f59e0b' }}>
                  {metrics.latency_p99_ms}ms
                </span>
              </div>
            </div>
            <div className="glass-panel" style={{ padding: 12 }}>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>CPU Utilization</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9', marginTop: 4 }}>
                {metrics.cpu_utilization_percent}%
              </div>
            </div>
          </div>
        )}

        {tab === 'logs' && (
          <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {logs.map((l, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: 8,
                  padding: '4px 8px',
                  borderRadius: 4,
                  backgroundColor: l.level === 'ERROR' ? 'rgba(244, 63, 94, 0.1)' : 'transparent',
                }}
              >
                <span style={{ color: '#64748b' }}>{l.timestamp}</span>
                <span
                  style={{
                    color: l.level === 'ERROR' ? '#f43f5e' : l.level === 'WARN' ? '#f59e0b' : '#3b82f6',
                    fontWeight: 600,
                  }}
                >
                  [{l.level}]
                </span>
                <span style={{ color: '#00f2fe' }}>{l.service}:</span>
                <span style={{ color: '#f1f5f9' }}>{l.msg}</span>
              </div>
            ))}
          </div>
        )}

        {tab === 'traces' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>
              Trace ID: <span style={{ fontFamily: 'monospace', color: '#00f2fe' }}>4bf92f3577b34da6a3ce929d0e0e4736</span>
            </div>
            {traces.map((t, idx) => (
              <div
                key={idx}
                className="glass-panel"
                style={{
                  padding: '8px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginLeft: idx * 16,
                  borderLeft: '3px solid #f43f5e',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9' }}>{t.span}</div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>service: {t.service}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="badge badge-production">{t.dur}</span>
                  <span style={{ fontSize: '0.75rem', color: '#f43f5e', fontWeight: 600 }}>{t.code}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
