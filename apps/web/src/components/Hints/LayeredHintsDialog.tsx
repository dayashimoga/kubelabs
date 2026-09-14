import React, { useState } from 'react';
import { HelpCircle, ChevronRight, Lock, Unlock, AlertCircle, MessageSquare } from 'lucide-react';
import { Hint } from '../../types';

interface LayeredHintsDialogProps {
  hints: Hint[];
  onAskAdvisor: (question: string) => Promise<any>;
}

export const LayeredHintsDialog: React.FC<LayeredHintsDialogProps> = ({ hints, onAskAdvisor }) => {
  const [unlockedTier, setUnlockedTier] = useState<number>(0);
  const [advisorAnswer, setAdvisorAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const tiers = [
    { tier: 1, name: 'Conceptual Direction', penalty: 5 },
    { tier: 2, name: 'Area to Inspect', penalty: 10 },
    { tier: 3, name: 'Diagnostic Command', penalty: 15 },
    { tier: 4, name: 'Strong Clue', penalty: 20 },
    { tier: 5, name: 'Full Solution & Explanation', penalty: 35 },
  ];

  const questions = [
    'What should I inspect next?',
    'Why did this fail?',
    'Which command should I run?',
    'Explain this output',
    'Show another possible root cause',
    'Show the correct solution',
  ];

  const handleAsk = async (q: string) => {
    setLoading(true);
    try {
      const res = await onAskAdvisor(q);
      setAdvisorAnswer(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        padding: 16,
        backgroundColor: '#0d121d',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <HelpCircle size={16} color="#00f2fe" />
        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9' }}>
          Step-by-Step Diagnostic Assistant
        </span>
      </div>

      {/* Quick SRE Questions */}
      <div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 8 }}>Ask Guided SRE Questions:</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {questions.map((q, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => handleAsk(q)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '4px 10px' }}
            >
              <MessageSquare size={12} color="#3b82f6" /> {q}
            </button>
          ))}
        </div>
      </div>

      {/* Advisor Response */}
      {advisorAnswer && (
        <div
          className="glass-panel"
          style={{
            padding: 14,
            borderLeft: '4px solid #00f2fe',
            backgroundColor: 'rgba(0, 242, 254, 0.05)',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#00f2fe', marginBottom: 4 }}>
            Advisor [{advisorAnswer.category}]:
          </div>
          <div style={{ fontSize: '0.825rem', color: '#f1f5f9', whiteSpace: 'pre-wrap' }}>
            {advisorAnswer.guidance}
          </div>
        </div>
      )}

      {/* 5-Tier Layered Hint Disclosure */}
      <div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 8 }}>Progressive Layered Hints:</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {tiers.map((t) => {
            const isUnlocked = unlockedTier >= t.tier;
            const hintObj = hints.find((h) => h.tier === t.tier);
            return (
              <div
                key={t.tier}
                style={{
                  padding: 12,
                  borderRadius: 6,
                  backgroundColor: isUnlocked ? '#141b2d' : '#07090e',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {isUnlocked ? <Unlock size={14} color="#10b981" /> : <Lock size={14} color="#64748b" />}
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isUnlocked ? '#f1f5f9' : '#94a3b8' }}>
                      Level {t.tier}: {t.name}
                    </span>
                  </div>
                  {!isUnlocked && (
                    <button
                      onClick={() => setUnlockedTier(t.tier)}
                      className="btn btn-secondary"
                      style={{ padding: '2px 8px', fontSize: '0.7rem' }}
                    >
                      Reveal (-{t.penalty} pts)
                    </button>
                  )}
                </div>

                {isUnlocked && hintObj && (
                  <div
                    style={{
                      marginTop: 8,
                      fontSize: '0.8rem',
                      color: '#cbd5e1',
                      whiteSpace: 'pre-wrap',
                      backgroundColor: '#07090e',
                      padding: 8,
                      borderRadius: 4,
                      fontFamily: t.tier === 3 ? 'monospace' : 'inherit',
                    }}
                  >
                    {hintObj.content}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
