import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CurriculumBrowser } from '../pages/CurriculumBrowser';

describe('CurriculumBrowser Component', () => {
  it('renders track selector tabs and curriculum header', () => {
    render(<CurriculumBrowser onSelectLab={vi.fn()} />);
    expect(screen.getByText('SRE & DevOps Curriculum Guides')).toBeInTheDocument();
    expect(screen.getByText('Kubernetes Deep-Dive')).toBeInTheDocument();
    expect(screen.getByText('Linux Systems & Kernel Diagnostics')).toBeInTheDocument();
    expect(screen.getByText('Docker & OCI Container Engine')).toBeInTheDocument();
  });

  it('switches active track when track button is clicked', () => {
    render(<CurriculumBrowser onSelectLab={vi.fn()} />);
    const linuxBtn = screen.getByText('Linux Systems & Kernel Diagnostics');
    fireEvent.click(linuxBtn);

    expect(screen.getAllByText('Filesystem VFS & Inode Saturation').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Process Lifecycle, Signals & Zombie Reaping')).toBeInTheDocument();
  });

  it('filters topics by search query', () => {
    render(<CurriculumBrowser onSelectLab={vi.fn()} />);
    const searchInput = screen.getByPlaceholderText(/Search topics\.\.\./i);
    fireEvent.change(searchInput, { target: { value: 'EndpointSlices' } });

    expect(screen.getByText('Services, EndpointSlices & CNI Routing')).toBeInTheDocument();
  });

  it('shows detailed topic breakdown and subtabs when a topic is selected', () => {
    render(<CurriculumBrowser onSelectLab={vi.fn()} />);
    const topicItem = screen.getByText('Pod Lifecycle & Probe Troubleshooting');
    fireEvent.click(topicItem);

    expect(screen.getByText('Concept Overview')).toBeInTheDocument();
    expect(screen.getByText(/Architectural Internals/i)).toBeInTheDocument();

    // Switch to Commands tab
    const commandsTab = screen.getByText('Essential Diagnostic Commands');
    fireEvent.click(commandsTab);
    expect(screen.getByText('Diagnostic Command Arsenal')).toBeInTheDocument();

    // Switch to Interview tab
    const interviewTab = screen.getByText('Interview Challenge & Security');
    fireEvent.click(interviewTab);
    expect(screen.getByText('Principal SRE / Staff Interview Scenario')).toBeInTheDocument();
    expect(screen.getByText(/DevSecOps & Production Safeguards/i)).toBeInTheDocument();
  });

  it('triggers onSelectLab when Launch Interactive Lab is clicked', () => {
    const onSelectLab = vi.fn();
    render(<CurriculumBrowser onSelectLab={onSelectLab} />);

    const topicItem = screen.getByText('Pod Lifecycle & Probe Troubleshooting');
    fireEvent.click(topicItem);

    const launchLabBtn = screen.getByText(/Launch Interactive Lab/i);
    fireEvent.click(launchLabBtn);

    expect(onSelectLab).toHaveBeenCalledWith('k8s-pod-crashloop-probe');
  });
});
