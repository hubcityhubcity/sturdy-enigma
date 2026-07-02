'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Candidate,
  ExportRecord,
  RenderJob,
  absoluteApiUrl,
  createEditTimeline,
  createExport,
  generateCandidates,
  getExport,
  getRenderJob,
  listCandidates,
  queueRenderExport,
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
  renderJob?: RenderJob;
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

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function ExportLinks({ exportRecord }: { exportRecord: ExportRecord }) {
  const videoUrl = absoluteApiUrl(exportRecord.download_urls?.video);
  const srtUrl = absoluteApiUrl(exportRecord.download_urls?.srt);
  const vttUrl = absoluteApiUrl(exportRecord.download_urls?.vtt);
  const metadataUrl = absoluteApiUrl(exportRecord.download_urls?.metadata);

  return (
    <div className="button-row" style={{ marginTop: 10 }}>
      {videoUrl && <a className="button" href={videoUrl} target="_blank" rel="noreferrer">Open MP4</a>}
      {srtUrl && <a className="button secondary" href={srtUrl} target="_blank" rel="noreferrer">SRT</a>}
      {vttUrl && <a className="button secondary" href={vttUrl} target="_blank" rel="noreferrer">VTT</a>}
      {metadataUrl && <a className="button secondary" href={metadataUrl} target="_blank" rel="noreferrer">Metadata</a>}
    </div>
  );
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
        setStatus('Generated fresh candidates.');
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Unable to load candidates.');
        setStatus('Showing demo candidates because the API did not respond.');
      }
    }

    loadCandidates();
  }, [projectId]);

  function updateWorkflow(candidateId: string, next: CandidateWorkflowState) {
    setWorkflowByCandidate((current) => ({
      ...current,
      [candidateId]: next,
    }));
  }

  async function pollRenderJob(candidateId: string, job: RenderJob, exportId: string) {
    let currentJob = job;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      currentJob = await getRenderJob(job.job_id);
      const refreshedExport = await getExport(exportId);

      updateWorkflow(candidateId, {
        status: `Queued render: ${currentJob.status} (${currentJob.progress}%)`,
        exportRecord: refreshedExport,
        renderJob: currentJob,
      });

      if (currentJob.status === 'complete' || currentJob.status === 'failed') {
        return { job: currentJob, exportRecord: refreshedExport };
      }

      await sleep(2000);
    }

    throw new Error('Render job polling timed out. Worker may not be running.');
  }

  async function approveAndQueueRender(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') {
      updateWorkflow(candidate.candidate_id, { status: 'Create a real project first to approve and render.' });
      return;
    }

    updateWorkflow(candidate.candidate_id, { status: 'Approving candidate...' });

    try {
      const edit = await createEditTimeline(candidate.candidate_id, {
        hook_text: candidate.excerpt,
        caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial',
        crop_mode: 'speaker_focus',
      });

      updateWorkflow(candidate.candidate_id, { status: 'Creating vertical export...' });

      const exportRecord = await createExport(edit.edit_id, {
        format: 'vertical_1080x1920',
        include_burned_captions: true,
        include_srt: true,
        include_vtt: true,
        include_metadata: true,
      });

      updateWorkflow(candidate.candidate_id, {
        status: 'Queueing render job...',
        exportRecord,
      });

      const renderJob = await queueRenderExport(exportRecord.export_id);
      updateWorkflow(candidate.candidate_id, {
        status: `Queued render: ${renderJob.status} (${renderJob.progress}%)`,
        exportRecord,
        renderJob,
      });

      const result = await pollRenderJob(candidate.candidate_id, renderJob, exportRecord.export_id);
      updateWorkflow(candidate.candidate_id, {
        status: result.job.status === 'complete' ? 'Render complete.' : 'Render failed.',
        exportRecord: result.exportRecord,
        renderJob: result.job,
        error: result.job.error || undefined,
      });
    } catch (caught) {
      updateWorkflow(candidate.candidate_id, {
        status: 'Queued render workflow failed.',
        error: caught instanceof Error ? caught.message : 'Unable to approve and queue render candidate.',
      });
    }
  }

  async function approveAndRenderNow(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') {
      updateWorkflow(candidate.candidate_id, { status: 'Create a real project first to approve and render.' });
      return;
    }

    updateWorkflow(candidate.candidate_id, { status: 'Approving candidate for immediate render...' });

    try {
      const edit = await createEditTimeline(candidate.candidate_id, {
        hook_text: candidate.excerpt,
        caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial',
        crop_mode: 'speaker_focus',
      });
      const exportRecord = await createExport(edit.edit_id, {
        format: 'vertical_1080x1920',
        include_burned_captions: true,
        include_srt: true,
        include_vtt: true,
        include_metadata: true,
      });
      updateWorkflow(candidate.candidate_id, { status: 'Rendering immediately...', exportRecord });
      const renderedExport = await renderExport(exportRecord.export_id);
      updateWorkflow(candidate.candidate_id, {
        status: `Immediate render finished: ${renderedExport.status}`,
        exportRecord: renderedExport,
      });
    } catch (caught) {
      updateWorkflow(candidate.candidate_id, {
        status: 'Immediate render failed.',
        error: caught instanceof Error ? caught.message : 'Unable to render immediately.',
      });
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
                    {workflow.renderJob && (
                      <>
                        <p><strong>Render Job ID:</strong> {workflow.renderJob.job_id}</p>
                        <p><strong>Render Job:</strong> {workflow.renderJob.status} / {workflow.renderJob.progress}%</p>
                      </>
                    )}
                    {workflow.exportRecord && (
                      <>
                        <p><strong>Export ID:</strong> {workflow.exportRecord.export_id}</p>
                        <p><strong>Export Status:</strong> {workflow.exportRecord.status}</p>
                        <ExportLinks exportRecord={workflow.exportRecord} />
                      </>
                    )}
                    {workflow.error && <p style={{ color: '#ff8a8a' }}><strong>Error:</strong> {workflow.error}</p>}
                  </div>
                )}
              </div>
              <div className="button-row">
                <button className="button" type="button" onClick={() => approveAndQueueRender(candidate)}>
                  Approve + Queue Render
                </button>
                <button className="button secondary" type="button" onClick={() => approveAndRenderNow(candidate)}>
                  Render Now
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}
