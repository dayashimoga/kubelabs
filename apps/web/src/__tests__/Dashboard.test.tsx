import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Dashboard } from '../pages/Dashboard';

const mockDashboardData = {
  user: {
    username: 'sre-alice',
    role: 'Principal SRE',
    troubleshooting_rating: 'Elite (2450)',
    overall_mastery: 92,
    labs_completed: 64,
    incidents_resolved: 29,
  },
  radar: [{ technology: 'Kubernetes', mastery: 88, labs_count: 14 }],
  weak_areas: [{ topic: 'CoreDNS', track: 'Kubernetes', severity: 'High', recommendation: 'Practice DNS labs' }],
  recommended_next: {
    type: 'incident',
    id: 'checkout-latency-spike',
    title: 'Checkout Latency Spike',
    track: 'sre-resilience',
    reason: 'Strengthen SLO triage',
  },
  active_sessions: [],
  recent_activity: [
    {
      type: 'lab_completed',
      title: 'Linux Inode Exhaustion',
      timestamp: '10 mins ago',
      score: 100,
    },
  ],
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state and displays loaded dashboard data', async () => {
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDashboardData),
      })
    );

    render(
      <Dashboard
        onSelectLab={vi.fn()}
        onSelectIncident={vi.fn()}
        onNavigate={vi.fn()}
      />
    );

    expect(screen.getByText('Loading SRE Dashboard...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('sre-alice')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
      expect(screen.getByText('64')).toBeInTheDocument();
      expect(screen.getByText('29')).toBeInTheDocument();
    });
  });

  it('triggers onSelectLab, onSelectIncident, and onNavigate callbacks', async () => {
    const onSelectLab = vi.fn();
    const onSelectIncident = vi.fn();
    const onNavigate = vi.fn();

    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDashboardData),
      })
    );

    render(
      <Dashboard
        onSelectLab={onSelectLab}
        onSelectIncident={onSelectIncident}
        onNavigate={onNavigate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('sre-alice')).toBeInTheDocument();
    });

    // Test Recommended Launch Scenario
    const launchScenarioBtn = screen.getByText(/Launch Scenario/i);
    fireEvent.click(launchScenarioBtn);
    expect(onSelectIncident).toHaveBeenCalledWith('checkout-latency-spike');

    // Test Take Skill Diagnostic Quiz navigation
    const quizBtn = screen.getByText('Take Skill Diagnostic Quiz');
    fireEvent.click(quizBtn);
    expect(onNavigate).toHaveBeenCalledWith('assessments');
  });
});
