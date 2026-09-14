import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CodeEditor } from '../components/Editor/CodeEditor';
import { TerminalView } from '../components/Terminal/TerminalView';
import { ValidationPanel } from '../components/Validation/ValidationPanel';
import { LayeredHintsDialog } from '../components/Hints/LayeredHintsDialog';
import { TopologyViewer } from '../components/Topology/TopologyViewer';
import { TelemetryViewer } from '../components/Telemetry/TelemetryViewer';
import { ValidationReport, TopologyData } from '../types';

describe('CodeEditor Component', () => {
  it('renders filename, initial content, and handles editing and saving', () => {
    const onSave = vi.fn();
    render(
      <CodeEditor
        filename="deployment.yaml"
        initialContent="replicas: 1"
        onSave={onSave}
      />
    );

    expect(screen.getByText('deployment.yaml')).toBeInTheDocument();
    const textarea = screen.getByTestId('monaco-textarea');
    expect(textarea).toHaveValue('replicas: 1');

    // Edit content
    fireEvent.change(textarea, { target: { value: 'replicas: 3' } });
    expect(screen.getByText(/Unsaved/i)).toBeInTheDocument();

    // Click save
    const saveBtn = screen.getByText('Save File');
    fireEvent.click(saveBtn);
    expect(onSave).toHaveBeenCalledWith('replicas: 3');
    expect(screen.queryByText(/Unsaved/i)).not.toBeInTheDocument();
  });
});

describe('TerminalView Component', () => {
  it('renders terminal container, connects websocket, and handles fullscreen toggle', () => {
    const onCommandRun = vi.fn();
    const { unmount } = render(
      <TerminalView
        sessionId="test-session-term"
        isContainer={true}
        onCommandRun={onCommandRun}
      />
    );

    expect(screen.getByText('Podman Container Shell')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();

    const ws = (window as any).__lastWebSocketInstance;
    const term = (window as any).__lastTerminalInstance;

    // Test WebSocket callbacks
    if (ws?.onopen) ws.onopen();
    if (ws?.onmessage) ws.onmessage({ data: 'system status normal\r\n' });
    if (ws?.onerror) ws.onerror();

    // Test onData with WebSocket OPEN
    ws.readyState = 1; // WebSocket.OPEN
    term._onDataCallback('whoami');
    expect(ws.send).toHaveBeenCalledWith('whoami');

    // Test onData with fallback emulator (WebSocket CLOSED)
    ws.readyState = 3; // WebSocket.CLOSED

    // Test typing and backspace
    term._onDataCallback('a');
    term._onDataCallback('\x7f'); // backspace
    term._onDataCallback('\x08'); // backspace on empty buffer

    // Test commands
    term._onDataCallback('c');
    term._onDataCallback('l');
    term._onDataCallback('e');
    term._onDataCallback('a');
    term._onDataCallback('r');
    term._onDataCallback('\r');

    term._onDataCallback('d');
    term._onDataCallback('f');
    term._onDataCallback(' ');
    term._onDataCallback('-');
    term._onDataCallback('h');
    term._onDataCallback('\r');

    term._onDataCallback('d');
    term._onDataCallback('f');
    term._onDataCallback(' ');
    term._onDataCallback('-');
    term._onDataCallback('i');
    term._onDataCallback('\r');

    term._onDataCallback('k');
    term._onDataCallback('u');
    term._onDataCallback('b');
    term._onDataCallback('e');
    term._onDataCallback('c');
    term._onDataCallback('t');
    term._onDataCallback('l');
    term._onDataCallback(' ');
    term._onDataCallback('g');
    term._onDataCallback('e');
    term._onDataCallback('t');
    term._onDataCallback(' ');
    term._onDataCallback('p');
    term._onDataCallback('o');
    term._onDataCallback('d');
    term._onDataCallback('s');
    term._onDataCallback('\r');

    term._onDataCallback('u');
    term._onDataCallback('n');
    term._onDataCallback('a');
    term._onDataCallback('m');
    term._onDataCallback('e');
    term._onDataCallback('\r');

    // Test empty enter
    term._onDataCallback('\r');

    // Toggle fullscreen
    const fsBtn = screen.getByTitle('Toggle Fullscreen');
    fireEvent.click(fsBtn);
    fireEvent.click(fsBtn);

    // Clear terminal
    const clearBtn = screen.getByTitle('Clear Terminal');
    fireEvent.click(clearBtn);

    // Trigger window resize
    fireEvent(window, new Event('resize'));

    unmount();
  });
});

describe('ValidationPanel Component', () => {
  it('renders validating state and report results with pass/partial/fail statuses', () => {
    const onValidate = vi.fn();

    // 1. Validating in progress
    const { rerender } = render(
      <ValidationPanel report={null} onValidate={onValidate} isValidating={true} />
    );
    expect(screen.getByText('Validating State...')).toBeDisabled();

    // 2. PASS report
    const passReport: ValidationReport = {
      overall_status: 'PASS',
      total_score: 100,
      max_possible_score: 100,
      percentage: 100,
      summary: 'Remediation confirmed healthy.',
      items: [
        {
          rule_id: 'rule-1',
          rule_type: 'http',
          description: 'Liveness probe healthy',
          passed: true,
          score_awarded: 100,
          max_score: 100,
          feedback: 'HTTP 200 returned.',
        },
      ],
    };

    rerender(<ValidationPanel report={passReport} onValidate={onValidate} isValidating={false} />);
    expect(screen.getByText('STATUS: PASS (100 / 100 pts)')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();

    // 3. PARTIAL report
    const partialReport: ValidationReport = {
      overall_status: 'PARTIAL',
      total_score: 50,
      max_possible_score: 100,
      percentage: 50,
      summary: 'One check failed.',
      items: [
        {
          rule_id: 'rule-1',
          rule_type: 'http',
          description: 'Liveness probe',
          passed: true,
          score_awarded: 50,
          max_score: 50,
          feedback: 'Passed',
        },
        {
          rule_id: 'rule-2',
          rule_type: 'tcp',
          description: 'Readiness probe',
          passed: false,
          score_awarded: 0,
          max_score: 50,
          feedback: 'Probe timed out',
        },
      ],
    };

    rerender(<ValidationPanel report={partialReport} onValidate={onValidate} isValidating={false} />);
    expect(screen.getByText('STATUS: PARTIAL (50 / 100 pts)')).toBeInTheDocument();

    // 4. FAIL report
    const failReport: ValidationReport = {
      overall_status: 'FAIL',
      total_score: 0,
      max_possible_score: 100,
      percentage: 0,
      summary: 'Pod still crashing.',
      items: [],
    };

    rerender(<ValidationPanel report={failReport} onValidate={onValidate} isValidating={false} />);
    expect(screen.getByText('STATUS: FAIL (0 / 100 pts)')).toBeInTheDocument();
  });
});

describe('LayeredHintsDialog Component', () => {
  it('handles guided SRE questions and progressive hint tier unlocking', async () => {
    const hints = [
      { tier: 1, title: 'Tier 1 Hint', penalty_points: 5, content: 'Conceptual clue: check inodes' },
      { tier: 2, title: 'Tier 2 Hint', penalty_points: 10, content: 'Inspect /var/spool' },
    ];
    const onAskAdvisor = vi.fn().mockResolvedValue({
      category: 'Diagnostic Reasoning',
      guidance: 'Inspect df -i output to see inode usage.',
    });

    render(<LayeredHintsDialog hints={hints} onAskAdvisor={onAskAdvisor} />);

    expect(screen.getByText('Step-by-Step Diagnostic Assistant')).toBeInTheDocument();

    // Ask SRE question
    const qBtn = screen.getByText('What should I inspect next?');
    fireEvent.click(qBtn);

    await waitFor(() => {
      expect(screen.getByText(/Advisor \[Diagnostic Reasoning\]:/i)).toBeInTheDocument();
      expect(screen.getByText(/Inspect df -i output/i)).toBeInTheDocument();
    });

    // Reveal Level 1 hint
    const revealBtn = screen.getByText('Reveal (-5 pts)');
    fireEvent.click(revealBtn);

    expect(screen.getByText('Conceptual clue: check inodes')).toBeInTheDocument();
  });
});

describe('TopologyViewer Component', () => {
  it('renders empty fallback and topology nodes with multiple statuses', () => {
    const { rerender } = render(<TopologyViewer />);
    expect(screen.getByText(/No architecture topology graph defined/i)).toBeInTheDocument();

    const topology: TopologyData = {
      nodes: [
        { id: 'gw', label: 'Ingress ALB', type: 'alb', status: 'healthy' },
        { id: 'api', label: 'API Pod', type: 'pod', status: 'degraded' },
        { id: 'db', label: 'PostgreSQL DB', type: 'database', status: 'failed' },
        { id: 'cache', label: 'Redis Cache', type: 'cache', status: 'slow' },
        { id: 'disk', label: 'NFS Volume', type: 'storage', status: 'healthy' },
      ],
      edges: [
        { source: 'gw', target: 'api', status: 'normal' },
        { source: 'api', target: 'db', status: 'broken', label: 'TCP RST' },
      ],
    };

    const onSelectNode = vi.fn();
    rerender(<TopologyViewer topology={topology} onSelectNode={onSelectNode} />);

    expect(screen.getByText('Ingress ALB')).toBeInTheDocument();
    expect(screen.getByText('API Pod')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL DB')).toBeInTheDocument();
    expect(screen.getByText('Redis Cache')).toBeInTheDocument();

    // Click a node
    fireEvent.click(screen.getByText('API Pod'));
    expect(onSelectNode).toHaveBeenCalledWith(expect.objectContaining({ id: 'api' }));

    // Edge check
    expect(screen.getByText(/gw ➔ api/i)).toBeInTheDocument();
    expect(screen.getByText(/api ➔ db \(TCP RST\)/i)).toBeInTheDocument();
  });
});

describe('TelemetryViewer Component', () => {
  it('switches between Metrics, Logs, and Traces tabs with live data', () => {
    render(<TelemetryViewer isPerturbed={true} />);

    // Live Metrics tab
    expect(screen.getByText('Throughput (RPS)')).toBeInTheDocument();
    expect(screen.getByText('5xx Error Rate')).toBeInTheDocument();

    // Switch to Log Stream
    const logsBtn = screen.getByText('Log Stream');
    fireEvent.click(logsBtn);
    expect(screen.getByText(/POST \/v2\/checkout HTTP\/2 200/i)).toBeInTheDocument();
    expect(screen.getByText(/HikariPool-1 timeout after 30000ms/i)).toBeInTheDocument();

    // Switch to OTel Traces
    const tracesBtn = screen.getByText('OTel Traces');
    fireEvent.click(tracesBtn);
    expect(screen.getByText('POST /api/v2/checkout')).toBeInTheDocument();
    expect(screen.getByText('OrderController.createOrder')).toBeInTheDocument();
  });
});
