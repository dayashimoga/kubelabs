import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OnboardingModal, GOALS } from '../pages/OnboardingModal';

describe('OnboardingModal Component', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders null when isOpen is false', () => {
    const { container } = render(
      <OnboardingModal isOpen={false} onClose={vi.fn()} onSelectGoal={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders all 5 learning goals when isOpen is true', () => {
    render(<OnboardingModal isOpen={true} onClose={vi.fn()} onSelectGoal={vi.fn()} />);
    expect(screen.getByText('Welcome to KubeLabs')).toBeInTheDocument();
    expect(screen.getByText('Learn DevOps from Scratch')).toBeInTheDocument();
    expect(screen.getByText('Master Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('Become an SRE')).toBeInTheDocument();
    expect(screen.getByText('Production Troubleshooting')).toBeInTheDocument();
    expect(screen.getByText('DevOps & SRE Interview Prep')).toBeInTheDocument();
  });

  it('allows selecting a goal and advancing to step 2 roadmap preview', () => {
    const onSelectGoal = vi.fn();
    const onClose = vi.fn();

    render(
      <OnboardingModal
        isOpen={true}
        onClose={onClose}
        onSelectGoal={onSelectGoal}
        currentGoalId="devops-scratch"
      />
    );

    // Select "Master Kubernetes"
    const k8sOption = screen.getByText('Master Kubernetes');
    fireEvent.click(k8sOption);

    // Click Continue to Learning Path
    const continueBtn = screen.getByText(/Continue to Learning Path/i);
    fireEvent.click(continueBtn);

    // Step 2 should be active
    expect(screen.getByText(/Recommended Learning Roadmap: Master Kubernetes/i)).toBeInTheDocument();
    expect(screen.getByText('Kubernetes Pod CrashLoop & Liveness Probes')).toBeInTheDocument();

    // Back to goals button works
    const backBtn = screen.getByText('Back to Goals');
    fireEvent.click(backBtn);
    expect(screen.getByText('Select your primary learning goal to customize your curriculum')).toBeInTheDocument();
  });

  it('handles Skip Customization in step 1', () => {
    const onSelectGoal = vi.fn();
    const onClose = vi.fn();

    render(
      <OnboardingModal
        isOpen={true}
        onClose={onClose}
        onSelectGoal={onSelectGoal}
        currentGoalId="become-sre"
      />
    );

    const skipBtn = screen.getByText('Skip Customization');
    fireEvent.click(skipBtn);

    expect(onSelectGoal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'become-sre' }),
      false
    );
    expect(onClose).toHaveBeenCalled();
    expect(localStorage.getItem('kubelabs_goal')).toBe('become-sre');
  });

  it('handles Save & Explore Dashboard in step 2', () => {
    const onSelectGoal = vi.fn();
    const onClose = vi.fn();

    render(
      <OnboardingModal
        isOpen={true}
        onClose={onClose}
        onSelectGoal={onSelectGoal}
        currentGoalId="devops-scratch"
      />
    );

    fireEvent.click(screen.getByText(/Continue to Learning Path/i));
    const saveBtn = screen.getByText('Save & Explore Dashboard');
    fireEvent.click(saveBtn);

    expect(onSelectGoal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'devops-scratch' }),
      false
    );
    expect(onClose).toHaveBeenCalled();
  });

  it('handles Start First Lesson in step 2', () => {
    const onSelectGoal = vi.fn();
    const onClose = vi.fn();

    render(
      <OnboardingModal
        isOpen={true}
        onClose={onClose}
        onSelectGoal={onSelectGoal}
        currentGoalId="production-troubleshooting"
      />
    );

    fireEvent.click(screen.getByText(/Continue to Learning Path/i));
    const startLabBtn = screen.getByText(/Start First Lesson/i);
    fireEvent.click(startLabBtn);

    expect(onSelectGoal).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'production-troubleshooting',
        firstLabId: 'k8s-service-zero-endpoints',
      }),
      true
    );
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<OnboardingModal isOpen={true} onClose={onClose} onSelectGoal={vi.fn()} />);
    const closeBtn = screen.getByRole('button', { name: /Close/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });
});
