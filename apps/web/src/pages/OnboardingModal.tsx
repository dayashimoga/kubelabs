import React, { useState } from 'react';
import { Target, Compass, Sparkles, ChevronRight, CheckCircle, ArrowRight, X } from 'lucide-react';

export interface LearningGoal {
  id: string;
  title: string;
  badge: string;
  description: string;
  estimatedHours: string;
  recommendedTracks: string[];
  firstLabId: string;
  firstLabTitle: string;
}

export const GOALS: LearningGoal[] = [
  {
    id: 'devops-scratch',
    title: 'Learn DevOps from Scratch',
    badge: 'Foundational',
    description: 'Master core systems engineering from Linux, Bash, and Git up to Docker containers and Kubernetes orchestrators.',
    estimatedHours: '35h',
    recommendedTracks: ['Linux', 'Bash', 'Git', 'Docker', 'Kubernetes', 'CI/CD'],
    firstLabId: 'linux-inode-exhaustion',
    firstLabTitle: 'Linux Inode Exhaustion & Root Cause',
  },
  {
    id: 'master-k8s',
    title: 'Master Kubernetes',
    badge: 'Specialist',
    description: 'Deep-dive into control planes, Pod lifecycle, Services, Ingress, CNI, storage, RBAC, and cluster-level operations.',
    estimatedHours: '40h',
    recommendedTracks: ['Kubernetes', 'Helm', 'Kustomize', 'Argo CD', 'Istio'],
    firstLabId: 'k8s-pod-crashloop-probe',
    firstLabTitle: 'Kubernetes Pod CrashLoop & Liveness Probes',
  },
  {
    id: 'become-sre',
    title: 'Become an SRE',
    badge: 'Reliability',
    description: 'Focus on SLI/SLO metrics, distributed tracing, alerting, cascading latency spikes, War Room triage, and blameless post-mortems.',
    estimatedHours: '30h',
    recommendedTracks: ['Prometheus', 'Grafana', 'OpenTelemetry', 'SRE Resilience', 'DevSecOps'],
    firstLabId: 'checkout-latency-spike',
    firstLabTitle: 'Cascading Latency Spike & Queue Saturation',
  },
  {
    id: 'production-troubleshooting',
    title: 'Production Troubleshooting',
    badge: 'Break/Fix',
    description: 'Hands-on practice tackling real-world failures: CrashLoopBackOff, 503 HTTP storms, OOMKilled evictions, and DNS outages.',
    estimatedHours: '25h',
    recommendedTracks: ['Linux', 'Docker', 'Kubernetes', 'Networking', 'Istio'],
    firstLabId: 'k8s-service-zero-endpoints',
    firstLabTitle: 'Kubernetes Service Zero Endpoints Mismatch',
  },
  {
    id: 'interview-prep',
    title: 'DevOps & SRE Interview Prep',
    badge: 'Career',
    description: 'Master systems design architectures, 13-part pedagogical internals, live diagnostic command challenges, and technical quizzes.',
    estimatedHours: '20h',
    recommendedTracks: ['All 24 Tracks', 'System Architecture', 'Assessments', 'Post-Mortems'],
    firstLabId: 'docker-pid1-signals',
    firstLabTitle: 'Docker PID 1 Signal Trapping & Zombie Reaping',
  },
];

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectGoal: (goal: LearningGoal, startLab?: boolean) => void;
  currentGoalId?: string;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  onSelectGoal,
  currentGoalId = 'devops-scratch',
}) => {
  const [selectedGoalId, setSelectedGoalId] = useState<string>(currentGoalId);
  const [step, setStep] = useState<1 | 2>(1);

  if (!isOpen) return null;

  const selectedGoal = GOALS.find((g) => g.id === selectedGoalId) || GOALS[0];

  const handleConfirm = (startLab: boolean) => {
    localStorage.setItem('kubelabs_goal', selectedGoal.id);
    onSelectGoal(selectedGoal, startLab);
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(7, 9, 14, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: 20,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 780,
          backgroundColor: '#0d121d',
          border: '1px solid var(--border-accent)',
          borderRadius: 12,
          boxShadow: '0 25px 50px -12px rgba(0, 242, 254, 0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '24px 28px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(180deg, rgba(0, 242, 254, 0.05) 0%, transparent 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#07090e',
              }}
            >
              <Target size={22} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#f8fafc', fontWeight: 800 }}>
                Welcome to KubeLabs
              </h2>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 2 }}>
                {step === 1 ? 'Select your primary learning goal to customize your curriculum' : 'Your Personalized SRE Curriculum Path'}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '6px 8px', borderRadius: 6 }}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px 28px', maxHeight: '65vh', overflowY: 'auto' }}>
          {step === 1 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {GOALS.map((goal) => {
                const isSelected = goal.id === selectedGoalId;
                return (
                  <div
                    key={goal.id}
                    onClick={() => setSelectedGoalId(goal.id)}
                    style={{
                      padding: '16px 20px',
                      borderRadius: 8,
                      border: isSelected ? '1px solid #00f2fe' : '1px solid var(--border-subtle)',
                      backgroundColor: isSelected ? 'rgba(0, 242, 254, 0.06)' : '#07090e',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease-in-out',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 16,
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: isSelected ? '#00f2fe' : '#f1f5f9' }}>
                          {goal.title}
                        </span>
                        <span className="badge badge-beginner" style={{ fontSize: '0.65rem' }}>
                          {goal.badge}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>• {goal.estimatedHours}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.4 }}>
                        {goal.description}
                      </p>
                    </div>
                    <div>
                      {isSelected ? (
                        <CheckCircle size={20} color="#00f2fe" />
                      ) : (
                        <div style={{ width: 20, height: 20, borderRadius: '50%', border: '1px solid #334155' }} />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div>
              <div
                style={{
                  padding: '20px',
                  backgroundColor: 'rgba(0, 242, 254, 0.05)',
                  border: '1px solid var(--border-accent)',
                  borderRadius: 8,
                  marginBottom: 20,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Sparkles size={18} color="#00f2fe" />
                  <h3 style={{ margin: 0, fontSize: '1rem', color: '#f8fafc' }}>
                    Recommended Learning Roadmap: {selectedGoal.title}
                  </h3>
                </div>
                <p style={{ margin: '0 0 16px 0', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                  We have structured an end-to-end learning track sequenced from core fundamentals to advanced failure modes.
                </p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                  {selectedGoal.recommendedTracks.map((track, idx) => (
                    <div
                      key={track}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        backgroundColor: '#141b2d',
                        border: '1px solid rgba(255,255,255,0.08)',
                        fontSize: '0.775rem',
                        color: '#cbd5e1',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <span style={{ color: '#00f2fe', fontWeight: 700 }}>{idx + 1}.</span> {track}
                    </div>
                  ))}
                </div>

                <div
                  style={{
                    padding: '14px 18px',
                    borderRadius: 8,
                    backgroundColor: '#07090e',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase' }}>
                      Recommended First Hands-On Lesson
                    </div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#f8fafc', marginTop: 2 }}>
                      {selectedGoal.firstLabTitle}
                    </div>
                  </div>
                  <span className="badge badge-beginner">Ready to Launch</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '18px 28px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: '#07090e',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          {step === 1 ? (
            <>
              <button
                onClick={() => handleConfirm(false)}
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem' }}
              >
                Skip Customization
              </button>
              <button
                onClick={() => setStep(2)}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                Continue to Learning Path <ChevronRight size={16} />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setStep(1)}
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem' }}
              >
                Back to Goals
              </button>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={() => handleConfirm(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem' }}
                >
                  Save & Explore Dashboard
                </button>
                <button
                  onClick={() => handleConfirm(true)}
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  Start First Lesson <ArrowRight size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
