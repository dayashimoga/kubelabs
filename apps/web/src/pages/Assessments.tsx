import React, { useState, useEffect } from 'react';
import { getApiBase } from '../config';
import { Award, CheckCircle2, XCircle, BookOpen, ChevronRight, HelpCircle } from 'lucide-react';

interface QuestionItem {
  id: string;
  track: string;
  type: string;
  difficulty: string;
  prompt: string;
  snippet?: string;
  options?: string[];
}

export const Assessments: React.FC = () => {
  const [track, setTrack] = useState<string>('all');
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [id: string]: any }>({});
  const [result, setResult] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${getApiBase()}/api/v1/assessments/${track}`)
      .then((res) => res.json())
      .then((data) => {
        setQuestions(data.questions || []);
        setSelectedAnswers({});
        setResult(null);
      });
  }, [track]);

  const handleSelectOption = (qId: string, optIdx: number, isMulti: boolean) => {
    if (isMulti) {
      const curr = selectedAnswers[qId] || [];
      const updated = curr.includes(optIdx) ? curr.filter((x: number) => x !== optIdx) : [...curr, optIdx];
      setSelectedAnswers({ ...selectedAnswers, [qId]: updated.sort() });
    } else {
      setSelectedAnswers({ ...selectedAnswers, [qId]: optIdx });
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/assessments/${track}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: selectedAnswers }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: '28px 36px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div
        className="glass-panel"
        style={{
          padding: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ fontSize: '0.8rem', color: '#00f2fe', fontWeight: 600, textTransform: 'uppercase' }}>
            Production Knowledge & Diagnosis Assessment
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4 }}>
            Hands-on Engineering Assessment
          </h1>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 4 }}>
            Evaluates log analysis, YAML fixing, command prediction, architecture, and troubleshooting.
          </div>
        </div>

        <select
          value={track}
          onChange={(e) => setTrack(e.target.value)}
          style={{
            padding: '8px 16px',
            borderRadius: 6,
            backgroundColor: '#141b2d',
            color: '#f1f5f9',
            border: '1px solid rgba(255,255,255,0.15)',
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          <option value="all">All Tracks</option>
          <option value="linux">Linux Internals</option>
          <option value="kubernetes">Kubernetes</option>
          <option value="networking">Networking & TCP</option>
          <option value="yaml-json">YAML & Schema</option>
          <option value="sre">SRE & Incident Response</option>
        </select>
      </div>

      {/* Questions List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {questions.map((q, idx) => {
          const isMulti = q.type === 'multi_select';
          const userAns = selectedAnswers[q.id];
          const itemResult = result?.details?.find((d: any) => d.question_id === q.id);

          return (
            <div key={q.id} className="glass-panel" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#00f2fe', textTransform: 'uppercase' }}>
                  Question {idx + 1} • {q.type.replace('_', ' ')} • {q.track}
                </span>
                <span className="badge badge-intermediate">{q.difficulty}</span>
              </div>

              <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9', marginBottom: 12 }}>
                {q.prompt}
              </div>

              {q.snippet && (
                <pre
                  style={{
                    backgroundColor: '#07090e',
                    padding: 12,
                    borderRadius: 6,
                    border: '1px solid rgba(255,255,255,0.06)',
                    fontSize: '0.8rem',
                    fontFamily: 'monospace',
                    color: '#cbd5e1',
                    marginBottom: 14,
                    overflowX: 'auto',
                  }}
                >
                  {q.snippet}
                </pre>
              )}

              {/* Options */}
              {q.options && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {q.options.map((opt, optIdx) => {
                    const isSelected = isMulti
                      ? Array.isArray(userAns) && userAns.includes(optIdx)
                      : userAns === optIdx;

                    return (
                      <div
                        key={optIdx}
                        onClick={() => !result && handleSelectOption(q.id, optIdx, isMulti)}
                        style={{
                          padding: '10px 14px',
                          borderRadius: 6,
                          backgroundColor: isSelected ? 'rgba(0, 242, 254, 0.1)' : '#0d121d',
                          border: `1px solid ${isSelected ? '#00f2fe' : 'rgba(255,255,255,0.06)'}`,
                          cursor: result ? 'default' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 10,
                          fontSize: '0.85rem',
                          color: isSelected ? '#f1f5f9' : '#94a3b8',
                        }}
                      >
                        <span
                          style={{
                            width: 18,
                            height: 18,
                            borderRadius: isMulti ? 4 : 9,
                            border: `2px solid ${isSelected ? '#00f2fe' : '#64748b'}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.7rem',
                            color: '#00f2fe',
                          }}
                        >
                          {isSelected && '✓'}
                        </span>
                        <span>{opt}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Feedback after grading */}
              {itemResult && (
                <div
                  style={{
                    marginTop: 14,
                    padding: 12,
                    borderRadius: 6,
                    backgroundColor: itemResult.is_correct ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                    border: `1px solid ${itemResult.is_correct ? '#10b981' : '#f43f5e'}`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: '0.85rem' }}>
                    {itemResult.is_correct ? (
                      <>
                        <CheckCircle2 size={16} color="#10b981" />
                        <span style={{ color: '#10b981' }}>Correct!</span>
                      </>
                    ) : (
                      <>
                        <XCircle size={16} color="#f43f5e" />
                        <span style={{ color: '#f43f5e' }}>Incorrect</span>
                      </>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 4 }}>
                    <strong>Explanation:</strong> {itemResult.explanation}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Submit button & Result Scorecard */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
        {!result ? (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="btn btn-primary"
            style={{ padding: '10px 24px', fontSize: '0.9rem' }}
          >
            {submitting ? 'Grading Answers...' : 'Submit & Grade Assessment'}
          </button>
        ) : (
          <div
            className="glass-panel"
            style={{
              padding: '16px 24px',
              borderLeft: `4px solid ${result.passed ? '#10b981' : '#f43f5e'}`,
              display: 'flex',
              alignItems: 'center',
              gap: 20,
            }}
          >
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Assessment Score</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: result.passed ? '#10b981' : '#f43f5e' }}>
                {result.score} / {result.total_questions} ({result.percentage}%)
              </div>
            </div>
            <button
              onClick={() => setResult(null)}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem' }}
            >
              Retry Assessment
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
