import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ProgressTracker } from '../pages/ProgressTracker';

describe('ProgressTracker Component', () => {
  it('renders overall learner metrics and track progress table', () => {
    render(<ProgressTracker />);

    expect(screen.getByText('Learner Progress & Certification')).toBeInTheDocument();
    expect(screen.getByText('Curriculum Progress')).toBeInTheDocument();
    expect(screen.getByText('Average SRE Score')).toBeInTheDocument();
    expect(screen.getByText('Domain Competency Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Linux Systems')).toBeInTheDocument();
    expect(screen.getByText('Kubernetes Deep-Dive')).toBeInTheDocument();
  });

  it('opens and closes the Certified Credential modal and allows credential export', () => {
    // Mock window.alert
    const alertMock = vi.fn();
    window.alert = alertMock;

    render(<ProgressTracker />);

    const viewCredBtn = screen.getByText('View Certified Credential');
    fireEvent.click(viewCredBtn);

    expect(screen.getByText(/Certificate of Production Engineering Excellence/i)).toBeInTheDocument();
    expect(screen.getByText(/Certified Kubernetes & Site Reliability Engineer/i)).toBeInTheDocument();

    // Export credential
    const exportBtn = screen.getByText(/Download Credential Record/i);
    fireEvent.click(exportBtn);
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining('KL-2026-SRE-8842'));

    // Modal closes after export
    expect(screen.queryByText(/Certificate of Production Engineering Excellence/i)).not.toBeInTheDocument();
  });
});
