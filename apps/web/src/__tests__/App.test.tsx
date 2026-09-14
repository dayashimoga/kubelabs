import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../App';

// Global fetch mock
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/v1/dashboard')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              user: {
                username: 'sre-lead',
                role: 'Senior SRE',
                troubleshooting_rating: 'Principal',
                overall_mastery: 84,
                labs_completed: 42,
                incidents_resolved: 18,
              },
              radar: [],
              weak_areas: [],
              recent_activity: [],
              recommended_next: {
                id: 'checkout-latency-spike',
                title: 'Checkout Latency Spike',
                reason: 'Service latency breached 99th percentile SLO',
              },
            }),
        });
      }
      if (url.includes('/api/v1/labs/tracks')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ tracks: ['Linux', 'Docker', 'Kubernetes'] }),
        });
      }
      if (url.includes('/api/v1/labs/linux-inode-exhaustion/session')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ session_id: 'test-session-123', status: 'ready', expires_at: Date.now() + 3600000 }),
        });
      }
      if (url.endsWith('/api/v1/labs')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve([
              {
                id: 'linux-inode-exhaustion',
                title: 'Linux Inode Exhaustion',
                track: 'Linux',
                difficulty: 'beginner',
                estimated_minutes: 20,
                objectives: ['Identify 100% inode saturation'],
              },
            ]),
        });
      }
      if (url.includes('/api/v1/labs/')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              id: 'linux-inode-exhaustion',
              title: 'Linux Inode Exhaustion',
              track: 'Linux',
              difficulty: 'beginner',
              estimated_minutes: 20,
              objectives: ['Identify 100% inode saturation'],
              instructions_md: '# Instructions\nFix inode leak',
              initial_state: { files: [{ path: '/tmp/test.sh', content: '#!/bin/bash' }] },
            }),
        });
      }
      if (url.includes('/api/v1/incidents')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve([
              {
                id: 'checkout-latency-spike',
                title: 'Checkout Latency Spike',
                severity: 'SEV-1',
                environment: 'production',
                time_limit_minutes: 30,
              },
            ]),
        });
      }
      if (url.includes('/api/v1/assessments')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ questions: [] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders sidebar navigation links and brand title', async () => {
    render(<App />);
    expect(screen.getByText('SRE TROUBLESHOOTING')).toBeInTheDocument();
    expect(screen.getByText('Learn Curriculum')).toBeInTheDocument();
    expect(screen.getByText('Skill & Dependency Map')).toBeInTheDocument();
    expect(screen.getByText('Hands-on Labs')).toBeInTheDocument();
    expect(screen.getByText('Troubleshooting Library')).toBeInTheDocument();
    expect(screen.getByText('Incident War Room')).toBeInTheDocument();
    expect(screen.getByText('Assessments & Quizzes')).toBeInTheDocument();
    expect(screen.getByText('Progress & Certificates')).toBeInTheDocument();
  });

  it('opens onboarding modal on initial visit when no goal is saved', () => {
    render(<App />);
    expect(screen.getByText('Welcome to KubeLabs')).toBeInTheDocument();
    expect(screen.getByText('Learn DevOps from Scratch')).toBeInTheDocument();
  });

  it('navigates between views when navigation buttons are clicked', async () => {
    localStorage.setItem('kubelabs_goal', 'devops-scratch');
    render(<App />);

    // Click Learn Curriculum
    const learnBtn = screen.getByText('Learn Curriculum');
    fireEvent.click(learnBtn);
    await waitFor(() => {
      expect(screen.getByText('SRE & DevOps Curriculum Guides')).toBeInTheDocument();
    });

    // Click Skill Graph
    const skillsBtn = screen.getByText('Skill & Dependency Map');
    fireEvent.click(skillsBtn);
    await waitFor(() => {
      expect(screen.getByText('Production SRE Competency & Dependency Map')).toBeInTheDocument();
    });

    // Click Hands-On Labs
    const labsBtn = screen.getByText('Hands-on Labs');
    fireEvent.click(labsBtn);
    await waitFor(() => {
      expect(screen.getByText('Explore Hands-on Real-World Labs')).toBeInTheDocument();
    });

    // Click Troubleshooting Index
    const troubleBtn = screen.getByText('Troubleshooting Library');
    fireEvent.click(troubleBtn);
    await waitFor(() => {
      expect(screen.getByText('Production Troubleshooting Library')).toBeInTheDocument();
    });

    // Click Incident War Room
    const incidentBtn = screen.getByText('Incident War Room');
    fireEvent.click(incidentBtn);
    await waitFor(() => {
      expect(screen.getByText(/LIVE SEV-1 \/ SEV-2 INCIDENT WAR ROOM/i)).toBeInTheDocument();
    });

    // Click Knowledge Assessments
    const assessBtn = screen.getByText('Assessments & Quizzes');
    fireEvent.click(assessBtn);
    await waitFor(() => {
      expect(screen.getByText(/Hands-on Engineering Assessment/i)).toBeInTheDocument();
    });

    // Click Certification Progress
    const progressBtn = screen.getByText('Progress & Certificates');
    fireEvent.click(progressBtn);
    await waitFor(() => {
      expect(screen.getByText('Learner Progress & Certification')).toBeInTheDocument();
    });

    // Click Dashboard
    const dashBtn = screen.getByText('Dashboard');
    fireEvent.click(dashBtn);
    await waitFor(() => {
      expect(screen.getByText(/Site Reliability Engineering Console/i)).toBeInTheDocument();
    });
  });

  it('allows clicking Active Goal badge to open OnboardingModal', () => {
    localStorage.setItem('kubelabs_goal', 'master-k8s');
    render(<App />);
    const goalBadge = screen.getByText(/Goal: Master Kubernetes/i);
    expect(goalBadge).toBeInTheDocument();
    fireEvent.click(goalBadge);
    expect(screen.getByText('Welcome to KubeLabs')).toBeInTheDocument();
  });

  it('switches to workspace view when launching a lab from catalog', async () => {
    localStorage.setItem('kubelabs_goal', 'devops-scratch');
    render(<App />);

    // Click Hands-on Labs
    fireEvent.click(screen.getByText('Hands-on Labs'));

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion')).toBeInTheDocument();
    });

    const startBtn = screen.getByText(/Start Lab/i);
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(screen.getByRole('region', { name: /SRE Lab Workspace/i })).toBeInTheDocument();
    });
  });

  it('switches to workspace view when choosing Start First Lesson in onboarding modal', async () => {
    render(<App />);

    // Onboarding modal is open
    expect(screen.getByText('Welcome to KubeLabs')).toBeInTheDocument();

    // Advance to step 2
    fireEvent.click(screen.getByText(/Continue to Learning Path/i));

    // Click Start First Lesson
    const startFirstBtn = screen.getByText(/Start First Lesson/i);
    fireEvent.click(startFirstBtn);

    await waitFor(() => {
      expect(screen.getByRole('region', { name: /SRE Lab Workspace/i })).toBeInTheDocument();
    });
  });

  it('switches to incident simulator when launching incident scenario from dashboard', async () => {
    localStorage.setItem('kubelabs_goal', 'devops-scratch');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Checkout Latency Spike')).toBeInTheDocument();
    });

    const launchScenarioBtn = screen.getByRole('button', { name: /Launch Scenario/i });
    fireEvent.click(launchScenarioBtn);

    await waitFor(() => {
      expect(screen.getByText(/LIVE SEV-1 \/ SEV-2 INCIDENT WAR ROOM/i)).toBeInTheDocument();
    });
  });
});
