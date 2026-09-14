import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LabWorkspace } from '../pages/LabWorkspace';

const mockLabData = {
  id: 'linux-inode-exhaustion',
  title: 'Linux Inode Exhaustion & Root Cause',
  track: 'Linux',
  difficulty: 'beginner',
  estimated_minutes: 20,
  objectives: ['Diagnose zero free inodes with df -i', 'Locate spam queue files'],
  instructions_md: '# Instructions\nRun df -i and identify the issue.',
  tasks: [
    {
      id: 'task-1',
      order: 1,
      title: 'Fix Inodes',
      description: 'Remediate inode exhaustion',
      hints: [],
    },
  ],
  hints: [
    { tier: 1, content: 'Check disk space with df.' },
    { tier: 2, content: 'Check inode space with df -i.' },
  ],
  topology: {
    nodes: [{ id: 'app', label: 'App Worker', type: 'pod', status: 'healthy' }],
    edges: [],
  },
  initial_state: {
    files: [{ path: '/etc/app.conf', content: 'debug=true\n' }],
  },
};

describe('LabWorkspace Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially and loads lab details and sandbox session', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-456',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    expect(screen.getByText(/Diagnose zero free inodes with df -i/i)).toBeInTheDocument();
  });

  it('displays provisioning failure and allows retry in simulation mode', async () => {
    let callCount = 0;
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        callCount++;
        if (callCount === 1) {
          return Promise.resolve({
            ok: false,
            status: 503,
            json: () => Promise.resolve({ detail: 'Podman rootless daemon timeout' }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-sim-123',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Runtime Provisioning Failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Podman rootless daemon timeout/i)).toBeInTheDocument();
    });

    // Click Launch in Simulation Mode
    const simBtn = screen.getByText(/Launch in Simulation Mode/i);
    fireEvent.click(simBtn);

    await waitFor(() => {
      expect(screen.queryByText(/Runtime Provisioning Failed/i)).not.toBeInTheDocument();
    });
  });

  it('switches between tab views: instructions, architecture, editor, telemetry, resources', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-789',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    // Switch to Topology tab
    fireEvent.click(screen.getByText('Topology'));
    expect(screen.getByText(/Service Mesh & Infrastructure Topology/i)).toBeInTheDocument();

    // Switch to Editor tab
    fireEvent.click(screen.getByText('Editor'));
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();

    // Edit content and save
    const editorTextarea = screen.getByTestId('monaco-textarea');
    fireEvent.change(editorTextarea, { target: { value: 'apiVersion: v1\nkind: Pod\nmetadata:\n  name: patched-app\n' } });
    const saveBtn = screen.getByText(/Save File/i);
    fireEvent.click(saveBtn);

    // Fullscreen editor toggle
    const fsEditorBtn = screen.getByTitle('Fullscreen Editor');
    fireEvent.click(fsEditorBtn);
    const exitFsEditorBtn = screen.getByTitle('Exit Fullscreen');
    expect(exitFsEditorBtn).toBeInTheDocument();
    fireEvent.click(exitFsEditorBtn);

    // Switch to Telemetry tab
    fireEvent.click(screen.getByText('Telemetry'));
    expect(screen.getByText('Live Metrics')).toBeInTheDocument();

    // Switch to Resources tab
    fireEvent.click(screen.getByText('Resources'));
    expect(screen.getByText(/Environment Resources & Security Constraints/i)).toBeInTheDocument();

    // Back to Instructions tab
    fireEvent.click(screen.getByText('Instructions'));
    expect(screen.getByText(/Diagnose zero free inodes with df -i/i)).toBeInTheDocument();

    // Fullscreen terminal toggle
    const fsTermBtn = screen.getByTitle('Fullscreen Terminal');
    fireEvent.click(fsTermBtn);
    const exitFsTermBtn = screen.getByTitle('Exit Fullscreen');
    expect(exitFsTermBtn).toBeInTheDocument();
    fireEvent.click(exitFsTermBtn);

    // Reconnect session
    const reconnectBtn = screen.getByTitle('Reconnect or re-sync active session');
    fireEvent.click(reconnectBtn);
  });

  it('interacts with Layered Hints and SRE advisor assistant', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-adv-1',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      if (url.endsWith('/advisor')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              category: 'diagnostic',
              guidance: 'Inspect /var/spool/postfix with df -i and identify stranded queue files.',
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    // Ask advisor question
    const askBtn = screen.getByText('What should I inspect next?');
    fireEvent.click(askBtn);

    await waitFor(() => {
      expect(screen.getByText(/Advisor \[diagnostic\]:/i)).toBeInTheDocument();
      expect(screen.getByText(/Inspect \/var\/spool\/postfix with df -i/i)).toBeInTheDocument();
    });
  });

  it('executes state validation and updates score report', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-101',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      if (url.endsWith('/validate')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              overall_status: 'PASS',
              total_score: 100,
              max_possible_score: 100,
              percentage: 100,
              summary: 'All root causes remediated successfully.',
              items: [
                {
                  description: 'Inode saturation below 80%',
                  passed: true,
                  score_awarded: 50,
                  max_score: 50,
                  feedback: 'Inode usage is healthy at 34%',
                },
              ],
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    // Click Run State Validation button
    const valBtn = screen.getByText('Run State Validation');
    fireEvent.click(valBtn);

    await waitFor(() => {
      expect(screen.getByText(/STATUS: PASS/i)).toBeInTheDocument();
      expect(screen.getByText(/All root causes remediated successfully/i)).toBeInTheDocument();
    });
  });

  it('resets sandbox session when Reset Sandbox Environment is clicked', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/reset')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ reset: true, message: 'Clean sandbox environment restored' }),
        });
      }
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              session_id: 'session-reset-test',
              status: 'ready',
              expires_at: Date.now() + 3600000,
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    render(<LabWorkspace labId="linux-inode-exhaustion" onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    const resetBtn = screen.getByTitle('Reset sandbox to initial failure state');
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText(/Sandbox environment reset to initial failure state/i)).toBeInTheDocument();
    });
  });

  it('handles resizable divider dragging and back navigation', async () => {
    const onBack = vi.fn();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/session')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ session_id: 's-drag', status: 'ready' }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabData),
      });
    });

    const { container } = render(<LabWorkspace labId="linux-inode-exhaustion" onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion & Root Cause')).toBeInTheDocument();
    });

    // Test back button
    const backBtn = screen.getByLabelText('Back to labs catalog');
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalled();

    // Test drag divider
    const divider = container.querySelector('div[style*="cursor: col-resize"]');
    if (divider) {
      fireEvent.mouseDown(divider);
      fireEvent.mouseMove(window, { clientX: 600 });
      fireEvent.mouseUp(window);
    }
  });
});
