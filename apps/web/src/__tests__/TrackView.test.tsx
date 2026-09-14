import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TrackView } from '../pages/TrackView';

const mockTracks = ['Linux', 'Kubernetes', 'Docker'];

const mockLabs = [
  {
    id: 'linux-inode-exhaustion',
    title: 'Linux Inode Exhaustion',
    track: 'Linux',
    difficulty: 'beginner',
    estimated_minutes: 20,
    validation_status: 'Automated',
    objectives: ['Diagnose inode leak with df -i'],
  },
  {
    id: 'k8s-pod-crashloop',
    title: 'Kubernetes Pod CrashLoop',
    track: 'Kubernetes',
    difficulty: 'intermediate',
    estimated_minutes: 25,
    validation_status: 'Automated',
    objectives: ['Fix liveness probe port mismatch'],
  },
];

describe('TrackView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/tracks')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ tracks: mockTracks }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockLabs),
      });
    });
  });

  it('renders track filter buttons and lab cards', async () => {
    render(<TrackView onSelectLab={vi.fn()} />);

    expect(screen.getByText('Explore Hands-on Real-World Labs')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion')).toBeInTheDocument();
      expect(screen.getByText('Kubernetes Pod CrashLoop')).toBeInTheDocument();
    });
  });

  it('filters labs by track selection', async () => {
    render(<TrackView onSelectLab={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion')).toBeInTheDocument();
    });

    const k8sFilterBtn = screen.getByRole('button', { name: 'Kubernetes' });
    fireEvent.click(k8sFilterBtn);

    expect(screen.getByText('Kubernetes Pod CrashLoop')).toBeInTheDocument();
    expect(screen.queryByText('Linux Inode Exhaustion')).not.toBeInTheDocument();

    // Reset to all
    const allBtn = screen.getByText(/All Tracks/i);
    fireEvent.click(allBtn);
    expect(screen.getByText('Linux Inode Exhaustion')).toBeInTheDocument();
  });

  it('calls onSelectLab when Start Lab is clicked', async () => {
    const onSelectLab = vi.fn();
    render(<TrackView onSelectLab={onSelectLab} />);

    await waitFor(() => {
      expect(screen.getByText('Linux Inode Exhaustion')).toBeInTheDocument();
    });

    const startBtns = screen.getAllByText(/Start Lab/i);
    fireEvent.click(startBtns[0]);

    expect(onSelectLab).toHaveBeenCalledWith('linux-inode-exhaustion');
  });
});
