import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TroubleshootingLibrary } from '../pages/TroubleshootingLibrary';

describe('TroubleshootingLibrary Component', () => {
  it('renders title, stats, and search controls', () => {
    render(<TroubleshootingLibrary onSelectLab={vi.fn()} />);
    expect(screen.getByText('Production Troubleshooting Library')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search symptoms \(e\.g\. CrashLoopBackOff/i)).toBeInTheDocument();
    expect(screen.getByText('CrashLoopBackOff')).toBeInTheDocument();
  });

  it('filters issues by search input term', () => {
    render(<TroubleshootingLibrary onSelectLab={vi.fn()} />);
    const searchInput = screen.getByPlaceholderText(/Search symptoms \(e\.g\. CrashLoopBackOff/i);

    fireEvent.change(searchInput, { target: { value: 'ENOSPC' } });
    expect(screen.getByText(/No space left on device error despite 85GB free disk blocks/i)).toBeInTheDocument();
    expect(screen.queryByText(/Pod status CrashLoopBackOff/i)).not.toBeInTheDocument();
  });

  it('filters issues by quick symptom tags', () => {
    render(<TroubleshootingLibrary onSelectLab={vi.fn()} />);
    const oomTag = screen.getByRole('button', { name: 'OOMKilled' });
    fireEvent.click(oomTag);

    expect(screen.getByText(/OOMKilled Pod Termination \(Exit Code 137\)/i)).toBeInTheDocument();
  });

  it('filters issues by technology and level', () => {
    render(<TroubleshootingLibrary onSelectLab={vi.fn()} />);

    // Filter by tech: Docker
    const techSelect = screen.getByDisplayValue('All Technologies');
    fireEvent.change(techSelect, { target: { value: 'Docker' } });

    expect(screen.getByText(/Container takes exactly 10s to stop and loses in-flight transactions/i)).toBeInTheDocument();
    expect(screen.queryByText(/Pod status CrashLoopBackOff/i)).not.toBeInTheDocument();

    // Filter by level: Beginner
    const levelSelect = screen.getByDisplayValue('All Tiers');
    fireEvent.change(levelSelect, { target: { value: 'Beginner' } });

    // No beginner docker labs in this subset
    expect(screen.getByText(/Showing 0 production failure scenarios/i)).toBeInTheDocument();
  });

  it('calls onSelectLab when Reproduce & Troubleshoot is clicked', () => {
    const onSelectLab = vi.fn();
    render(<TroubleshootingLibrary onSelectLab={onSelectLab} />);

    const launchBtns = screen.getAllByText(/Reproduce & Troubleshoot/i);
    fireEvent.click(launchBtns[0]);

    expect(onSelectLab).toHaveBeenCalledWith('k8s-pod-crashloop-probe');
  });
});
