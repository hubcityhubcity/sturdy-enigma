'use client';

import { useEffect, useMemo, useState } from 'react';
import { Candidate, generateCandidates, listCandidates } from '../../lib/api';

const fallbackCandidates: Candidate[] = [
  {
    candidate_id: 'fallback-1',
    project_id: 'demo',
    start_seconds: 120,
    end_seconds: 164,
    title: 'Strong opening debate moment',
    excerpt: 'This clip starts with immediate tension, gives enough context, and lands with a clear payoff.',
    score: 88,
    category: 'debate_heat',
    explanation: 'Strong hook, clear contrast, clean payoff, low context risk.',
    risk_flags: [],
  },
  {
    candidate_id: 'fallback-2',
    project_id: 'demo',
    start_seconds: 442,
    end_seconds: 489,
    title: 'Story mode clip',
    excerpt: 'A clear story arc with setup, emotion, and a practical takeaway.',
    score: 81,
    category: 'story_mode',
    explanation: 'Good narrative structure and emotional clarity.',
    risk_flags: [],
  },
];

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remainingSeconds = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remainingSeconds}`;
}

function formatCategory(category: string) {
  return category.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function ProducerModeClient({ projectId }: { projectId?: string }) {
  const [candidates, setCandidates] = useState<Candidate[]>(fallbackCandidates);
  const [status, setStatus] = useState(projectId ? 'Loading project candidates...' : 'Showing demo candidates.');
  const [error, setError] = useState('');

  const sortedCandidates = useMemo(
    () => [...candidates].sort((a, b) => b.score - a.score),
    [candidates]
  );

  useEffect(() => {
    async function loadCandidates() {
      if (!projectId) return;

      try {
        const existing = await listCandidates(projectId);
        if (existing.candidates.length > 0) {
          setCandidates(existing.candidates);
          setStatus('Loaded project candidates.');
          return;
        }

        const generated = await generateCandidates(projectId);
        setCandidates(generated.candidates);
        setStatus('Generated fresh mock candidates.');
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Unable to load candidates.');
        setStatus('Showing demo candidates because the API did not respond.');
      }
    }

    loadCandidates();
  }, [projectId]);

  return (
    <>
      <section className="card" style={{ marginTop: 24 }}>
        <h2>Candidate status</h2>
        <p>{status}</p>
        {projectId && <p><strong>Project ID:</strong> {projectId}</p>}
        {error && <p style={{ color: '#ff8a8a' }}><strong>API note:</strong> {error}</p>}
      </section>

      <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
        {sortedCandidates.map((candidate) => (
          <article className="card candidate" key={candidate.candidate_id}>
            <div>
              <div className="score">{candidate.score}</div>
              <div className="badge">{formatCategory(candidate.category)}</div>
            </div>
            <div>
              <h2>{candidate.title}</h2>
              <p>
                <strong>Source time:</strong> {formatTime(candidate.start_seconds)} - {formatTime(candidate.end_seconds)}
              </p>
              <p>{candidate.excerpt}</p>
              <p><strong>Why it ranked:</strong> {candidate.explanation}</p>
              {candidate.risk_flags.length > 0 && (
                <p><strong>Risk flags:</strong> {candidate.risk_flags.join(', ')}</p>
              )}
            </div>
            <div className="button-row">
              <a className="button" href="#">Approve</a>
              <a className="button secondary" href="#">Edit</a>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
