'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Candidate, ExportRecord, RenderJob, ScoreBreakdown, ScoreSignal,
  absoluteApiUrl, analyzeGameSenseStream, createEditTimeline, createExport,
  detectGameSenseAudio, detectGameSenseVisual, generateCandidates,
  generateGameSenseCandidates, getExport, getRenderJob, listCandidates,
  listSources, queueRenderExport, renderExport, rescoreCandidates,
} from '../../lib/api';
import { GameSenseEvidencePanel } from './GameSenseEvidencePanel';

const fallbackCandidates: Candidate[] = [{
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
}];

const scoreOrder: Array<keyof ScoreBreakdown> = ['hook', 'curiosity', 'emotion', 'debate', 'story', 'retention'];
const scoreLabels: Record<string, string> = { hook: 'Hook', curiosity: 'Curiosity', emotion: 'Emotion', debate: 'Debate', story: 'Story', retention: 'Retention', overall: 'Overall' };
type CandidateWorkflowState = { status: string; exportRecord?: ExportRecord; renderJob?: RenderJob; error?: string };

function formatTime(seconds: number) { return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`; }
function formatCategory(category: string) { return category.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function sleep(milliseconds: number) { return new Promise((resolve) => setTimeout(resolve, milliseconds)); }
function scoreTone(score: number) { return score >= 85 ? 'Elite' : score >= 70 ? 'Strong' : score >= 55 ? 'Useful' : 'Low'; }

function ScoreSignalRow({ signal }: { signal: ScoreSignal }) {
  return <div style={{ display: 'grid', gridTemplateColumns: '90px 52px 70px 1fr', gap: 10, alignItems: 'center', marginTop: 8 }}><strong>{scoreLabels[signal.name] || formatCategory(signal.name)}</strong><span>{signal.score}</span><span className="badge">{scoreTone(signal.score)}</span><span style={{ opacity: 0.85 }}>{signal.explanation}</span></div>;
}

function ScoreBreakdownPanel({ breakdown }: { breakdown?: ScoreBreakdown }) {
  const signals = scoreOrder.map((key) => breakdown?.[key]).filter(Boolean) as ScoreSignal[];
  const evidence = breakdown?.engine === 'gamesense_v1' ? breakdown.evidence || [] : [];
  if (evidence.length) return <div className="card" style={{ marginTop: 12 }}><h3>Titan GameSense</h3>{breakdown?.overall && <p><strong>Moment score:</strong> {breakdown.overall.score} — {breakdown.overall.explanation}</p>}<p><strong>Aligned evidence:</strong> {evidence.length} signal(s)</p>{evidence.map((signal, index) => <p key={`${signal.event_type}-${index}`} style={{ margin: '6px 0', opacity: 0.9 }}>{formatCategory(signal.event_type)} · {formatCategory(signal.modality)} · intensity {signal.intensity}</p>)}</div>;
  if (!signals.length) return <p><strong>Titan Brain:</strong> Score breakdown not available yet.</p>;
  return <div className="card" style={{ marginTop: 12 }}><h3>Titan Brain</h3>{breakdown?.overall && <p><strong>Overall:</strong> {breakdown.overall.score} — {breakdown.overall.explanation}</p>}{signals.map((signal) => <ScoreSignalRow key={signal.name} signal={signal} />)}</div>;
}

function ExportLinks({ exportRecord }: { exportRecord: ExportRecord }) {
  const links = [{ label: 'Open MP4', url: absoluteApiUrl(exportRecord.download_urls?.video), primary: true }, { label: 'SRT', url: absoluteApiUrl(exportRecord.download_urls?.srt) }, { label: 'VTT', url: absoluteApiUrl(exportRecord.download_urls?.vtt) }, { label: 'Metadata', url: absoluteApiUrl(exportRecord.download_urls?.metadata) }];
  return <div className="button-row" style={{ marginTop: 10 }}>{links.filter((item) => item.url).map((item) => <a key={item.label} className={item.primary ? 'button' : 'button secondary'} href={item.url || undefined} target="_blank" rel="noreferrer">{item.label}</a>)}</div>;
}

export function ProducerModeClient({ projectId }: { projectId?: string }) {
  const [candidates, setCandidates] = useState<Candidate[]>(fallbackCandidates);
  const [status, setStatus] = useState(projectId ? 'Loading project candidates...' : 'Showing demo candidates.');
  const [error, setError] = useState('');
  const [workflowByCandidate, setWorkflowByCandidate] = useState<Record<string, CandidateWorkflowState>>({});
  const [isRescoring, setIsRescoring] = useState(false);
  const [isGeneratingGameSense, setIsGeneratingGameSense] = useState(false);
  const [isAnalyzingStream, setIsAnalyzingStream] = useState(false);
  const [isScanningAudio, setIsScanningAudio] = useState(false);
  const [isScanningVisual, setIsScanningVisual] = useState(false);
  const [evidenceRefreshToken, setEvidenceRefreshToken] = useState(0);
  const [activeEvidenceSourceId, setActiveEvidenceSourceId] = useState<string | null>(null);
  const sortedCandidates = useMemo(() => [...candidates].sort((a, b) => b.score - a.score), [candidates]);
  const refreshEvidence = () => setEvidenceRefreshToken((value) => value + 1);

  useEffect(() => {
    async function loadCandidates() {
      if (!projectId) return;
      try {
        const existing = await listCandidates(projectId);
        if (existing.candidates.length) { setCandidates(existing.candidates); setStatus('Loaded project candidates.'); return; }
        const generated = await generateCandidates(projectId);
        setCandidates(generated.candidates); setStatus('Generated fresh transcript candidates.');
      } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to load candidates.'); setStatus('Showing demo candidates because the API did not respond.'); }
    }
    setActiveEvidenceSourceId(null);
    loadCandidates();
  }, [projectId]);

  function updateWorkflow(candidateId: string, next: CandidateWorkflowState) { setWorkflowByCandidate((current) => ({ ...current, [candidateId]: next })); }
  async function withNewestSource(action: (sourceId: string) => Promise<void>, missingMessage: string) {
    if (!projectId) { setStatus('Create a real gaming project first.'); return; }
    const sources = await listSources(projectId);
    const source = sources.sources[sources.sources.length - 1];
    if (!source) throw new Error(missingMessage);
    setActiveEvidenceSourceId(source.source_id);
    await action(source.source_id);
  }

  async function rescoreProject() {
    if (!projectId) return setStatus('Create a real project first to rescore candidates.');
    setIsRescoring(true); setError(''); setStatus('Rescoring candidates with Titan Brain...');
    try { const result = await rescoreCandidates(projectId); setCandidates(result.candidates); setStatus(`Titan Brain rescored ${result.updated_count} candidate(s).`); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to rescore candidates.'); setStatus('Candidate rescore failed.'); }
    finally { setIsRescoring(false); }
  }

  async function analyzeStream() {
    if (!projectId) return setStatus('Create a real gaming project first to analyze a stream.');
    setIsAnalyzingStream(true); setError(''); setStatus('Titan GameSense is analyzing stream audio and visual action...');
    try {
      await withNewestSource(async (sourceId) => {
        const analysis = await analyzeGameSenseStream(sourceId, true, 0.30);
        refreshEvidence();
        setStatus('Titan found evidence. Ranking the strongest GameSense moments...');
        const generated = await generateGameSenseCandidates(projectId, sourceId, true);
        setCandidates(generated.candidates);
        const { audio_spike_count, visual_scene_change_count } = analysis.summary;
        setStatus(`Titan analyzed the stream and ranked ${generated.generated_count} clip candidate(s) from ${audio_spike_count} audio reaction spike(s) and ${visual_scene_change_count} visual action signal(s).`);
      }, 'No source exists for this project yet.');
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Unable to analyze this stream.';
      setError(message); setStatus(message.includes('source_media_not_available') ? 'Stream analysis requires an uploaded or successfully imported local media source.' : 'GameSense stream analysis failed.');
    } finally { setIsAnalyzingStream(false); }
  }

  async function scanAudioForReactions() {
    if (!projectId) return setStatus('Create a real gaming project first to scan audio.');
    setIsScanningAudio(true); setError(''); setStatus('Titan GameSense is scanning stream audio for reaction spikes...');
    try { await withNewestSource(async (sourceId) => { const result = await detectGameSenseAudio(sourceId, true); refreshEvidence(); setStatus(result.created_count ? `Titan found ${result.created_count} audio reaction spike(s). Generate GameSense clips to fuse them into moments.` : 'Titan found no strong audio spikes in this source. Add visual, chat, or gameplay evidence for more context.'); }, 'No source exists for this project yet.'); }
    catch (caught) { const message = caught instanceof Error ? caught.message : 'Unable to scan stream audio.'; setError(message); setStatus(message.includes('source_media_not_available') ? 'Audio scanning requires an uploaded or successfully imported local media source.' : 'GameSense audio scan failed.'); }
    finally { setIsScanningAudio(false); }
  }

  async function scanVisualForAction() {
    if (!projectId) return setStatus('Create a real gaming project first to scan visuals.');
    setIsScanningVisual(true); setError(''); setStatus('Titan GameSense is scanning for sharp visual action changes...');
    try { await withNewestSource(async (sourceId) => { const result = await detectGameSenseVisual(sourceId, true); refreshEvidence(); setStatus(result.created_count ? `Titan found ${result.created_count} visual scene-change signal(s). Generate GameSense clips to fuse them with audio, chat, or gameplay evidence.` : 'Titan found no sharp visual changes at the current threshold. Audio, chat, and gameplay evidence can still produce clips.'); }, 'No source exists for this project yet.'); }
    catch (caught) { const message = caught instanceof Error ? caught.message : 'Unable to scan stream visuals.'; setError(message); setStatus(message.includes('source_media_not_available') ? 'Visual scanning requires an uploaded or successfully imported local media source.' : 'GameSense visual scan failed.'); }
    finally { setIsScanningVisual(false); }
  }

  async function generateGameSense() {
    if (!projectId) return setStatus('Create a real gaming project first to generate GameSense clips.');
    setIsGeneratingGameSense(true); setError(''); setStatus('Titan GameSense is fusing gameplay, audio, visual, chat, and reaction evidence...');
    try { const result = await generateGameSenseCandidates(projectId, activeEvidenceSourceId, true); if (!result.candidates.length) throw new Error('No strong gaming moments met the GameSense threshold.'); setCandidates(result.candidates); refreshEvidence(); setStatus(`Titan GameSense generated ${result.generated_count} gaming candidate(s).`); }
    catch (caught) { const message = caught instanceof Error ? caught.message : 'Unable to generate GameSense clips.'; setError(message); setStatus(message.includes('gamesense_events_not_found') ? 'No GameSense evidence exists yet. Analyze the stream, import chat, or add gameplay events first.' : 'GameSense generation failed.'); }
    finally { setIsGeneratingGameSense(false); }
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
    try { const edit = await createEditTimeline(candidate.candidate_id, { hook_text: candidate.excerpt, caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial', crop_mode: 'speaker_focus' }); const exportRecord = await createExport(edit.edit_id, { format: 'vertical_1080x1920', include_burned_captions: true, include_srt: true, include_vtt: true, include_metadata: true }); updateWorkflow(candidate.candidate_id, { status: 'Queueing render job...', exportRecord }); const renderJob = await queueRenderExport(exportRecord.export_id); const result = await pollRenderJob(candidate.candidate_id, renderJob, exportRecord.export_id); updateWorkflow(candidate.candidate_id, { status: result.job.status === 'complete' ? 'Render complete.' : 'Render failed.', exportRecord: result.exportRecord, renderJob: result.job, error: result.job.error || undefined }); }
    catch (caught) { updateWorkflow(candidate.candidate_id, { status: 'Queued render workflow failed.', error: caught instanceof Error ? caught.message : 'Unable to approve and queue render candidate.' }); }
  }

  async function approveAndRenderNow(candidate: Candidate) {
    if (!projectId || candidate.project_id === 'demo') return updateWorkflow(candidate.candidate_id, { status: 'Create a real project first to approve and render.' });
    updateWorkflow(candidate.candidate_id, { status: 'Approving candidate for immediate render...' });
    try { const edit = await createEditTimeline(candidate.candidate_id, { hook_text: candidate.excerpt, caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial', crop_mode: 'speaker_focus' }); const exportRecord = await createExport(edit.edit_id, { format: 'vertical_1080x1920', include_burned_captions: true, include_srt: true, include_vtt: true, include_metadata: true }); updateWorkflow(candidate.candidate_id, { status: 'Rendering immediately...', exportRecord }); const renderedExport = await renderExport(exportRecord.export_id); updateWorkflow(candidate.candidate_id, { status: `Immediate render finished: ${renderedExport.status}`, exportRecord: renderedExport }); }
    catch (caught) { updateWorkflow(candidate.candidate_id, { status: 'Immediate render failed.', error: caught instanceof Error ? caught.message : 'Unable to render immediately.' }); }
  }

  return <>
    <section className="card" style={{ marginTop: 24 }}>
      <h2>Candidate status</h2><p>{status}</p>{projectId && <p><strong>Project ID:</strong> {projectId}</p>}{error && <p style={{ color: '#ff8a8a' }}><strong>API note:</strong> {error}</p>}
      <div className="button-row" style={{ marginTop: 12 }}>
        <button className="button" type="button" onClick={analyzeStream} disabled={isAnalyzingStream || !projectId}>{isAnalyzingStream ? 'Analyzing + Ranking...' : 'Analyze Stream + Find Clips'}</button>
        <button className="button secondary" type="button" onClick={generateGameSense} disabled={isGeneratingGameSense || !projectId}>{isGeneratingGameSense ? 'Finding Gaming Moments...' : 'Generate GameSense Clips'}</button>
        <button className="button secondary" type="button" onClick={rescoreProject} disabled={isRescoring || !projectId}>{isRescoring ? 'Rescoring...' : 'Rescore with Titan Brain'}</button>
      </div>
      <details style={{ marginTop: 12 }}><summary style={{ cursor: 'pointer' }}>Advanced detection controls</summary><div className="button-row" style={{ marginTop: 10 }}><button className="button secondary" type="button" onClick={scanAudioForReactions} disabled={isScanningAudio || !projectId}>{isScanningAudio ? 'Scanning Stream Audio...' : 'Scan Audio for Reactions'}</button><button className="button secondary" type="button" onClick={scanVisualForAction} disabled={isScanningVisual || !projectId}>{isScanningVisual ? 'Scanning Stream Visuals...' : 'Scan Visual Action'}</button></div></details>
      <p style={{ marginTop: 10, opacity: 0.8 }}>Gaming workflow: analyze local stream evidence, rank the strongest GameSense moments, then review and render. Visual changes are signals—not automatic kill labels.</p>
    </section>
    <GameSenseEvidencePanel projectId={projectId} sourceId={activeEvidenceSourceId} refreshToken={evidenceRefreshToken} />
    <section style={{ display: 'grid', gap: 18, marginTop: 24 }}>
      {sortedCandidates.map((candidate) => {
        const workflow = workflowByCandidate[candidate.candidate_id];
        return <article className="card candidate" key={candidate.candidate_id}><div><div className="score">{candidate.score}</div><div className="badge">{formatCategory(candidate.category)}</div></div><div><h2>{candidate.title}</h2><p><strong>Source time:</strong> {formatTime(candidate.start_seconds)} - {formatTime(candidate.end_seconds)}</p><p>{candidate.excerpt}</p><p><strong>Why it ranked:</strong> {candidate.explanation}</p><ScoreBreakdownPanel breakdown={candidate.score_breakdown} />{candidate.risk_flags.length > 0 && <p><strong>Risk flags:</strong> {candidate.risk_flags.join(', ')}</p>}{workflow && <div className="card" style={{ marginTop: 12 }}><p><strong>Workflow:</strong> {workflow.status}</p>{workflow.renderJob && <p><strong>Render Job:</strong> {workflow.renderJob.status} / {workflow.renderJob.progress}%</p>}{workflow.exportRecord && <><p><strong>Export Status:</strong> {workflow.exportRecord.status}</p><ExportLinks exportRecord={workflow.exportRecord} /></>}{workflow.error && <p style={{ color: '#ff8a8a' }}><strong>Error:</strong> {workflow.error}</p>}</div>}</div><div className="button-row"><button className="button" type="button" onClick={() => approveAndQueueRender(candidate)}>Approve + Queue Render</button><button className="button secondary" type="button" onClick={() => approveAndRenderNow(candidate)}>Render Now</button></div></article>;
      })}
    </section>
  </>;
}
