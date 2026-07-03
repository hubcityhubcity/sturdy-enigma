'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Candidate,
  ExportRecord,
  RenderJob,
  ScoreBreakdown,
  ScoreSignal,
  absoluteApiUrl,
  createEditTimeline,
  createExport,
  generateCandidates,
  generateGameSenseCandidates,
  getExport,
  getRenderJob,
  listCandidates,
  queueRenderExport,
  renderExport,
  rescoreCandidates,
} from '../../lib/api';

const fallbackCandidates: Candidate[] = [
  {
    candidate_id: 'fallback-1', project_id: 'demo', start_seconds: 120, end_seconds: 164,
    title: 'Strong opening debate moment', excerpt: 'This clip starts with immediate tension, gives enough context, and lands with a clear payoff.',
    score: 88, category: 'debate_heat', explanation: 'Strong hook, clear contrast, clean payoff, low context risk.', risk_flags: [],
    score_breakdown: {
      hook: { name: 'hook', score: 92, explanation: 'Strong opening tension.' },
      curiosity: { name: 'curiosity', score: 86, explanation: 'Creates a clear open loop.' },
      emotion: { name: 'emotion', score: 78, explanation: 'Has urgency and intensity.' },
      debate: { name: 'debate', score: 91, explanation: 'Conflict signal is strong.' },
      story: { name: 'story', score: 61, explanation: 'Some narrative setup.' },
      retention: { name: 'retention', score: 84, explanation: 'Good short-form length and pace.' },
    },
  },
];

const scoreOrder: Array<keyof ScoreBreakdown> = ['hook', 'curiosity', 'emotion', 'debate', 'story', 'retention'];
const scoreLabels: Record<string, string> = { hook: 'Hook', curiosity: 'Curiosity', emotion: 'Emotion', debate: 'Debate', story: 'Story', retention: 'Retention', overall: 'Overall' };

type CandidateWorkflowState = { status: string; exportRecord?: ExportRecord; renderJob?: RenderJob; error?: string };

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

function formatCategory(category: string) {
  return category.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function scoreTone(score: number) {
  if (score >= 85) return 'Elite';
  if (score >= 70) return 'Strong';
  if (score >= 55) return 'Useful';
  return 'Low';
}

function ScoreSignalRow({ signal }: { signal: ScoreSignal }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '90px 52px 70px 1fr', gap: 10, alignItems: 'center', marginTop: 8 }}>
      <strong>{scoreLabels[signal.name] || formatCategory(signal.name)}</strong>
      <span>{signal.score}</span>
      <span className="badge">{scoreTone(signal.score)}</span>
      <span style={{ opacity: 0.85 }}>{signal.explanation}</span>
    </div>
  );
}

function ScoreBreakdownPanel({ breakdown }: { breakdown?: ScoreBreakdown }) {
  const signals = scoreOrder.map((key) => breakdown?.[key]).filter(Boolean) as ScoreSignal[];
  const gameEvidence = breakdown?.engine === 'gamesense_v1' ? breakdown.evidence || [] : [];

  if (gameEvidence.length) {
    return (
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Titan GameSense</h3>
        {breakdown?.overall && <p><strong>Moment score:</strong> {breakdown.overall.score} — {breakdown.overall.explanation}</p>}
        <p><strong>Aligned evidence:</strong> {gameEvidence.length} signal(s)</p>
        {gameEvidence.map((signal, index) => (
          <p key={`${signal.event_type}-${index}`} style={{ margin: '6px 0', opacity: 0.9 }}>
            {formatCategory(signal.event_type)} · {formatCategory(signal.modality)} · intensity {signal.intensity}
          </p>
        ))}
      </div>
    );
  }

  if (!signals.length) return <p><strong>Titan Brain:</strong> Score breakdown not available yet. Rescore this project after running migrations.</p>;
  return (
    <div className="card" style={{ marginTop: 12 }}>
      <h3>Titan Brain</h3>
      {breakdown?.overall && <p><strong>Overall:</strong> {breakdown.overall.score} — {breakdown.overall.explanation}</p>}
      {signals.map((signal) => <ScoreSignalRow key={signal.name} signal={signal} />)}
    </div>
  );
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
  const [isRescoring, setIsRescoring] = useState(false);
  const [isGeneratingGameSense, setIsGeneratingGameSense] = useState(false);

  const sortedCandidates = useMemo(() => [...candidates].sort((a, b) => b.score - a.score), [candidates]);

  useEffect(() => {
    async function loadCandidates() {
      if (!projectId) return;
      try {
        const existing = await listCandidates(projectId);
        if (existing.candidates.length) {
          setCandidates(existing.candidates);
          setStatus('Loaded project candidates.');
          return;
        }
        const generated = await generateCandidates(projectId);
        setCandidates(generated.candidates);
        setStatus('Generated fresh transcript candidates.');
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Unable to load candidates.');
        setStatus('Showing demo candidates because the API did not respond.');
      }
    }
    loadCandidates();
  }, [projectId]);

  function updateWorkflow(candidateId: string, next: CandidateWorkflowState) {
    setWorkflowByCandidate((current) => ({ ...current, [candidateId]: next }));
  }

  async function rescoreProject() {
    if (!projectId) return setStatus('Create a real project first to rescore candidates.');
    setIsRescoring(true); setError(''); setStatus('Rescoring candidates with Titan Brain...');
    try {
      const result = await rescoreCandidates(projectId);
      setCandidates(result.candidates);
      setStatus(`Titan Brain rescored ${result.updated_count} candidate(s).`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to rescore candidates.');
      setStatus('Candidate rescore failed.');
    } finally {
      setIsRescoring(false);
    }
  }

  async function generateGameSense() {
    if (!projectId) return setStatus('Create a real gaming project first to generate GameSense clips.');
    setIsGeneratingGameSense(true); setError(''); setStatus('Titan GameSense is fusing gameplay, audio, chat, and reaction evidence...');
    try {
      const result = await generateGameSenseCandidates(projectId, undefined, true);
      if (!result.candidates.length) throw new Error('No strong gaming moments met the GameSense threshold.');
      setCandidates(result.candidates);
      setStatus(`Titan GameSense generated ${result.generated_count} gaming candidate(s).`);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Unable to generate GameSense clips.';
      setError(message);
      setStatus(message.includes('gamesense_events_not_found')
        ? 'No GameSense evidence exists yet. Import or detect gameplay, audio, chat, or facecam events first.'
        : 'GameSense generation failed.');
    } finally {
      setIsGeneratingGameSense(false);
    }
  }

  async function pollRenderJob(candidateId: string, job: RenderJob, exportId: string) {
    let currentJob = job;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      currentJob = await getRenderJob(job.job_id);
      const refreshedExport = await getExport(exportId);
      updateWorkflow(candidateId, { status: `Queued render: ${currentJob.status} (${currentJob.progress}%)`, exportRecord: refreshedExport, renderJob: currentJob });
      if (currentJob.status === 'complete' || currentJob.status === 'failed') return { job: currentJob, exportRecord: refreshedExport };
      await sleep(2000);
    }
    throw new Error('Render job polling timed out. Worker may not be running.');
  }

  async function approveAndQueueRender(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') return updateWorkflow(candidate.candidate_id, { status: 'Create a real project first to approve and render.' });
    updateWorkflow(candidate.candidate_id, { status: 'Approving candidate...' });
    try {
      const edit = await createEditTimeline(candidate.candidate_id, { hook_text: candidate.excerpt, caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial', crop_mode: 'speaker_focus' });
      const exportRecord = await createExport(edit.edit_id, { format: 'vertical_1080x1920', include_burned_captions: true, include_srt: true, include_vtt: true, include_metadata: true });
      updateWorkflow(candidate.candidate_id, { status: 'Queueing render job...', exportRecord });
      const renderJob = await queueRenderExport(exportRecord.export_id);
      const result = await pollRenderJob(candidate.candidate_id, renderJob, exportRecord.export_id);
      updateWorkflow(candidate.candidate_id, { status: result.job.status === 'complete' ? 'Render complete.' : 'Render failed.', exportRecord: result.exportRecord, renderJob: result.job, error: result.job.error || undefined });
    } catch (caught) {
      updateWorkflow(candidate.candidate_id, { status: 'Queued render workflow failed.', error: caught instanceof Error ? caught.message : 'Unable to approve and queue render candidate.' });
    }
  }

  async function approveAndRenderNow(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') return updateWorkflow(candidate.candidate_id, { status: 'Create a real project first to approve and render.' });
    updateWorkflow(candidate.candidate_id, { status: 'Approving candidate for immediate render...' });
    try {
      const edit = await createEditTimeline(candidate.candidate_id, { hook_text: candidate.excerpt, caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial', crop_mode: 'speaker_focus' });
      const exportRecord = await createExport(edit.edit_id, { format: 'vertical_1080x1920', include_burned_captions: true, include_srt: true, include_vtt: true, include_metadata: true });
      updateWorkflow(candidate.candidate_id, { status: 'Rendering immediately...', exportRecord });
      const renderedExport = await renderExport(exportRecord.export_id);
      updateWorkflow(candidate.candidate_id, { status: `Immediate render finished: ${renderedExport.status}`, exportRecord: renderedExport });
    } catch (caught) {
      updateWorkflow(candidate.candidate_id, { status: 'Immediate render failed.', error: caught instanceof Error ? caught.message : 'Unable to render immediately.' });
    }
  }

  return (
    <>
      <section className="card" style={{ marginTop: 24 }}>
        <h2>Candidate status</h2>
        <p>{status}</p>
        {projectId && <p><strong>Project ID:</strong> {projectId}</p>}
        {error && <p style={{ color: '#ff8a8a' }}><strong>API note:</strong> {error}</p>}
        <div className="button-row" style={{ marginTop: 12 }}>
          <button className="button secondary" type="button" onClick={rescoreProject} disabled={isRescoring || !projectId}>
            {isRescoring ? 'Rescoring...' : 'Rescore with Titan Brain'}
          </button>
          <button className="button" type="button" onClick={generateGameSense} disabled={isGeneratingGameSense || !projectId}>
            {isGeneratingGameSense ? 'Finding Gaming Moments...' : 'Generate GameSense Clips'}
          </button>
        </div>
        <p style={{ marginTop: 10, opacity: 0.8 }}>GameSense uses imported or detected gameplay, audio, chat, and facecam events. It does not invent stream moments from a transcript.</p>
      </section>

      <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
        {sortedCandidates.map((candidate) => {
          const workflow = workflowByCandidate[candidate.candidate_id];
          return (
            <article className="card candidate" key={candidate.candidate_id}>
              <div><div className="score">{candidate.score}</div><div className="badge">{formatCategory(candidate.category)}</div></div>
              <div>
                <h2>{candidate.title}</h2>
                <p><strong>Source time:</strong> {formatTime(candidate.start_seconds)} - {formatTime(candidate.end_seconds)}</p>
                <p>{candidate.excerpt}</p>
                <p><strong>Why it ranked:</strong> {candidate.explanation}</p>
                <ScoreBreakdownPanel breakdown={candidate.score_breakdown} />
                {candidate.risk_flags.length > 0 && <p><strong>Risk flags:</strong> {candidate.risk_flags.join(', ')}</p>}
                {workflow && (
                  <div className="card" style={{ marginTop: 12 }}>
                    <p><strong>Workflow:</strong> {workflow.status}</p>
                    {workflow.renderJob && <p><strong>Render Job:</strong> {workflow.renderJob.status} / {workflow.renderJob.progress}%</p>}
                    {workflow.exportRecord && <><p><strong>Export Status:</strong> {workflow.exportRecord.status}</p><ExportLinks exportRecord={workflow.exportRecord} /></>}
                    {workflow.error && <p style={{ color: '#ff8a8a' }}><strong>Error:</strong> {workflow.error}</p>}
                  </div>
                )}
              </div>
              <div className="button-row">
                <button className="button" type="button" onClick={() => approveAndQueueRender(candidate)}>Approve + Queue Render</button>
                <button className="button secondary" type="button" onClick={() => approveAndRenderNow(candidate)}>Render Now</button>
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}
