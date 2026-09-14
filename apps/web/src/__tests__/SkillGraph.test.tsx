import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SkillGraph } from '../pages/SkillGraph';

describe('SkillGraph Component', () => {
  it('renders skill dependency graph and column headings', () => {
    render(<SkillGraph onSelectTrack={vi.fn()} />);

    expect(screen.getByText('Production SRE Competency & Dependency Map')).toBeInTheDocument();
    expect(screen.getByText('beginner')).toBeInTheDocument();
    expect(screen.getByText('intermediate')).toBeInTheDocument();
    expect(screen.getByText('advanced')).toBeInTheDocument();
    expect(screen.getByText('production')).toBeInTheDocument();
    expect(screen.getAllByText('Linux System Internals').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Container & Host Networking')).toBeInTheDocument();
  });

  it('selects a node, displays prerequisite details, and triggers onSelectTrack', () => {
    const onSelectTrack = vi.fn();
    render(<SkillGraph onSelectTrack={onSelectTrack} />);

    // Click Kubernetes Architecture node
    const k8sNode = screen.getByText('Kubernetes Architecture');
    fireEvent.click(k8sNode);

    // Verify descriptions in both card and drawer
    const descriptions = screen.getAllByText(/Control plane, kube-proxy, Endpoints, probes/i);
    expect(descriptions.length).toBeGreaterThanOrEqual(1);

    // Click explore button in drawer
    const exploreBtn = screen.getByText(/Explore KUBERNETES Labs/i);
    fireEvent.click(exploreBtn);
    expect(onSelectTrack).toHaveBeenCalledWith('kubernetes');
  });
});
