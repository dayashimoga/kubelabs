import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { IncidentSimulator } from '../pages/IncidentSimulator';

const mockIncidents = [
  {
    id: 'checkout-latency-spike',
    title: 'Checkout Latency Spike & Queue Saturation',
    severity: 'SEV-1',
    summary: 'P99 checkout latency spike causing cascading HTTP 504 timeouts',
    impact: 'Cart checkout drop-off rate spiked 42%',
    affected_services: ['gateway', 'order-svc', 'postgres'],
  },
  {
    id: 'dns-lookup-blackhole',
    title: 'CoreDNS Lookup Blackhole',
    severity: 'SEV-2',
    summary: 'DNS timeouts in payment cluster',
    impact: 'Intermittent resolution failures',
    affected_services: ['coredns'],
  },
];

const mockIncidentDetail = {
  id: 'checkout-latency-spike',
  title: 'Checkout Latency Spike & Queue Saturation',
  severity: 'SEV-1',
  summary: 'P99 checkout latency spike causing cascading HTTP 504 timeouts',
  impact: 'Cart checkout drop-off rate spiked 42%',
  affected_services: ['gateway', 'order-svc', 'postgres'],
  initial_symptoms: [
    'P99 checkout latency > 3500ms',
    'HTTP 504 Gateway Timeouts on POST /v2/checkout',
  ],
  hypotheses: [
    {
      id: 'h1',
      statement: 'Postgres connection pool exhaustion in order-svc',
      plausible: true,
      evidence_required: 'Run pool metric check',
    },
  ],
  topology: {
    nodes: [{ id: 'gateway', label: 'Edge Gateway', type: 'gateway', status: 'healthy' }],
    edges: [],
  },
  alerts: [],
  diagnostic_commands: [],
};

describe('IncidentSimulator Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/api/v1/incidents')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockIncidents),
        });
      }
      if (url.includes('/start')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ session_id: 'inc-session-999', status: 'active' }),
        });
      }
      if (url.includes('/hypothesis')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              supported: true,
            }),
        });
      }
      if (url.includes('/mitigate')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              mitigated: true,
              feedback: 'Database connection pool increased to 400. Latency dropping.',
            }),
        });
      }
      if (url.includes('/resolve')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              resolved: true,
              score: {
                total_score: 92,
                detection_score: 95,
                investigation_score: 90,
                root_cause_score: 92,
                fix_score: 90,
                verification_score: 95,
                prevention_score: 90,
                feedback: ['Connection pool saturation resolved.'],
              },
              post_mortem: '# Blameless Post-Mortem\nRoot cause: Under-provisioned DB pool.',
            }),
        });
      }
      if (url.includes('/api/v1/incidents/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockIncidentDetail),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders incident simulator and loads active incident details', async () => {
    render(<IncidentSimulator />);

    await waitFor(() => {
      expect(screen.getByText(/LIVE SEV-1 \/ SEV-2 INCIDENT WAR ROOM/i)).toBeInTheDocument();
      expect(screen.getByText(/P99 checkout latency > 3500ms/i)).toBeInTheDocument();
    });
  });

  it('tests hypotheses and applies mitigations', async () => {
    render(<IncidentSimulator />);

    await waitFor(() => {
      expect(screen.getByText(/Postgres connection pool exhaustion in order-svc/i)).toBeInTheDocument();
    });

    // Test hypothesis
    const testHypoBtn = screen.getByText('Test Hypothesis');
    fireEvent.click(testHypoBtn);

    await waitFor(() => {
      expect(screen.getByText(/Supported by telemetry!/i)).toBeInTheDocument();
    });

    // Enter mitigation command
    const cmdInput = screen.getByPlaceholderText(/e\.g\. kubectl rollout restart/i);
    fireEvent.change(cmdInput, { target: { value: 'kubectl scale deployment order-svc --replicas=5' } });

    const applyBtn = screen.getByText('Apply Fix');
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(screen.getByText(/Database connection pool increased to 400/i)).toBeInTheDocument();
    });
  });

  it('resolves incident and opens post-mortem modal', async () => {
    render(<IncidentSimulator />);

    await waitFor(() => {
      expect(screen.getByText('Verify Incident Resolution & Generate Scorecard')).toBeInTheDocument();
    });

    // Resolve incident
    const resolveBtn = screen.getByText('Verify Incident Resolution & Generate Scorecard');
    fireEvent.click(resolveBtn);

    await waitFor(() => {
      expect(screen.getByText(/SRE Post-Mortem Score: 92 \/ 100/i)).toBeInTheDocument();
    });

    // Open post-mortem modal
    const viewPostMortemBtn = screen.getByText(/View Full SRE Post-Mortem/i);
    fireEvent.click(viewPostMortemBtn);

    expect(screen.getByText(/SRE Post-Mortem Report/i)).toBeInTheDocument();
    expect(screen.getByText(/Root cause: Under-provisioned DB pool/i)).toBeInTheDocument();

    // Close modal
    const closeBtn = screen.getByText('✕');
    fireEvent.click(closeBtn);
    expect(screen.queryByText(/SRE Post-Mortem Report/i)).not.toBeInTheDocument();
  });
});
