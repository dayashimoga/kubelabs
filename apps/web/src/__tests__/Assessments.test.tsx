import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Assessments } from '../pages/Assessments';

const mockQuestions = [
  {
    id: 'q1',
    track: 'kubernetes',
    type: 'multiple-choice',
    difficulty: 'intermediate',
    prompt: 'What happens when a readiness probe fails on a Kubernetes Pod?',
    snippet: 'readinessProbe:\n  httpGet:\n    path: /ready\n    port: 8080',
    options: [
      'The kubelet restarts the container immediately',
      'The Pod is removed from Service EndpointSlices and stops receiving traffic',
      'The node enters NotReady status',
      'The Pod is evicted and rescheduled to another node',
    ],
  },
  {
    id: 'q2',
    track: 'linux',
    type: 'multiple-select',
    difficulty: 'advanced',
    prompt: 'Which commands can reveal inode saturation when df -h shows free space?',
    options: [
      'df -i',
      'stat -f /',
      'free -m',
      'cat /proc/uptime',
    ],
  },
];

describe('Assessments Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/submit')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              passed: true,
              score: 2,
              total_questions: 2,
              percentage: 100,
              details: [
                {
                  question_id: 'q1',
                  is_correct: true,
                  explanation: 'Readiness failures detach pods from EndpointSlices without restarting.',
                },
                {
                  question_id: 'q2',
                  is_correct: true,
                  explanation: 'df -i and stat -f show inode metrics.',
                },
              ],
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ questions: mockQuestions }),
      });
    });
  });

  it('loads assessment questions and handles single-choice and multi-choice selections', async () => {
    render(<Assessments />);

    await waitFor(() => {
      expect(screen.getByText(/What happens when a readiness probe fails/i)).toBeInTheDocument();
      expect(screen.getByText(/Which commands can reveal inode saturation/i)).toBeInTheDocument();
    });

    // Select single-choice option
    const opt1 = screen.getByText('The Pod is removed from Service EndpointSlices and stops receiving traffic');
    fireEvent.click(opt1);

    // Select multi-choice options (toggle)
    const dfiOpt = screen.getByText('df -i');
    fireEvent.click(dfiOpt);
    const statOpt = screen.getByText('stat -f /');
    fireEvent.click(statOpt);

    // Toggle again to test removal
    fireEvent.click(statOpt);
    fireEvent.click(statOpt);

    // Submit assessment
    const submitBtn = screen.getByText('Submit & Grade Assessment');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Assessment Score')).toBeInTheDocument();
      expect(screen.getByText(/2 \/ 2 \(100%\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Readiness failures detach pods from EndpointSlices/i)).toBeInTheDocument();
      expect(screen.getByText('Retry Assessment')).toBeInTheDocument();
    });

    // Test retry
    const retryBtn = screen.getByText('Retry Assessment');
    fireEvent.click(retryBtn);
    expect(screen.getByText('Submit & Grade Assessment')).toBeInTheDocument();
  });

  it('allows switching tracks to reload different question sets', async () => {
    render(<Assessments />);

    await waitFor(() => {
      expect(screen.getByText(/Hands-on Engineering Assessment/i)).toBeInTheDocument();
    });

    const trackSelect = screen.getByDisplayValue('All Tracks');
    fireEvent.change(trackSelect, { target: { value: 'kubernetes' } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/assessments/kubernetes');
    });
  });
});
