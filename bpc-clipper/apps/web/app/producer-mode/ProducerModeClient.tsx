'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Candidate,
  ExportRecord,
  createEditTimeline,
  createExport,
  generateCandidates,
  listCandidates,
  renderExport,
} from '../../lib/api';

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

type CandidateWorkflowState = {
  status: string;
  exportRecord?: ExportRecord;
  error?: string;
};

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
  const [workflowByCandidate, setWorkflowByCandidate] = useState<Record<string, CandidateWorkflowState>>({});

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

  async function approveAndRender(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') {
      setWorkflowByCandidate((current) => ({
        ...current,
        [candidate.candidate_id]: { status: 'Create a real project first to approve and render.' },
      }));
      return;
    }

    setWorkflowByCandidate((current) => ({
      ...current,
      [candidate.candidate_id]: { status: 'Approving candidate...' },
    }));

    try {
      const edit = await createEditTimeline(candidate.candidate_id, {
        hook_text: candidate.excerpt,
        caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial',
        crop_mode: 'speaker_focus',
      });

      setWorkflowByCandidate((current) => ({
        ...current,
        [candidate.candidate_id]: { status: 'Creating vertical export...' },
      }));

      const queuedExport = await createExport(edit.edit_id, {
        format: 'vertical_1080x1920',
        include_burned_captions: true,
        include_srt: true,
        include_vtt: true,
        include_metadata: true,
      });

      setWorkflowByCandidate((current) => ({
        ...current,
        [candidate.candidate_id]: { status: 'Rendering vertical clip...', exportRecord: queuedExport },
      }));

      const renderedExport = await renderExport(queuedExport.export_id);
      setWorkflowByCandidate((current) => ({
        ...current,
        [candidate.candidate_id]: { status: `Render finished: ${renderedExport.status}`, exportRecord: renderedExport },
      }));
    } catch (caught) {
      setWorkflowByCandidate((current) => ({
        ...current,
        [candidate.candidate_id]: {
          status: 'Workflow failed.',
          error: caught instanceof Error ? caught.message : 'Unable to approve and render candidate.',
        },
      }));
    }
  }

  return (
    <>
      <section className="card" style={{ marginTop: 24 }}>
        <h2>Candidate status</h2>
        <p>{status}</p>
        {projectId && <p><strong>Project ID:</strong> {projectId}</p>}
        {error && <p style={{ color: '#ff8a8a' }}><strong>API note:</strong> {error}</p>}
      </section>

      <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
        {sortedCandidates.map((candidate) => {
          const workflow = workflowByCandidate[candidate.candidate_id];
          return (
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
                {workflow && (
                  <div className="card" style={{ marginTop: 12 }}>
                    <p><strong>Workflow:</strong> {workflow.status}</p>
                    {workflow.exportRecord && (
                      <>
                        <p><strong>Export ID:</strong> {workflow.exportRecord.export_id}</p>
                        <p><strong>Video path:</strong> {workflow.exportRecord.video_path || 'Not ready yet'}</p>
                        <p><strong>SRT:</strong> {workflow.exportRecord.srt_path || 'Not generated'}</p>
                        <p><strong>VTT:</strong> {workflow.exportRecord.vtt_path || 'Not generated'}</p>
                      </>
                    )}
                    {workflow.error && <p style={{ color: '#ff8a8a' }}><strong>Error:</strong> {workflow.error}</p>}
                  </div>
                )}
              </div>
              <div className="button-row">
                <button className="button" type="button" onClick={() => approveAndRender(candidate)}>
                  Approve + Render
                </button>
                <button className="button secondary" type="button" onClick={() => approveAndRender(candidate)}>
                  Quick Export
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}
