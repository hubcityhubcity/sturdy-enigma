'use client';

import { useEffect, useMemo, useState } from 'react';
import { Candidate, GameSenseEvidence, GameSenseSummary, Source, generateGameSenseCandidates, getGameSenseSummary, listSourceCandidates, listSources } from '../../lib/api';

function sourceLabel(source: Source) {
  return source.title || source.original_filename || source.original_url || `Source ${source.source_id.slice(0, 8)}`;
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

function titleCase(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function evidenceStrings(event: GameSenseEvidence, key: string): string[] {
  const value = event.evidence?.[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function evidenceNumber(event: GameSenseEvidence, key: string): number | null {
  const value = event.evidence?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function SourceCandidateBrowser({ projectId }: { projectId?: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [summary, setSummary] = useState<GameSenseSummary | null>(null);
  const [status, setStatus] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [isReranking, setIsReranking] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    async function loadSources() {
      try {
        const result = await listSources(projectId);
        if (cancelled) return;
        setSources(result.sources);
        const newest = result.sources[result.sources.length - 1];
        setSourceId(newest?.source_id || '');
      } catch (caught) {
        if (!cancelled) setStatus(caught instanceof Error ? caught.message : 'Unable to load project sources.');
      }
    }
    loadSources();
    return () => { cancelled = true; };
  }, [projectId]);

  useEffect(() => {
    function onEvidenceUpdated(event: Event) {
      const detail = (event as CustomEvent<{ sourceId?: string }>).detail;
      if (!detail?.sourceId || detail.sourceId === sourceId) setRefreshToken((value) => value + 1);
    }
    window.addEventListener('gamesense-evidence-updated', onEvidenceUpdated);
    return () => window.removeEventListener('gamesense-evidence-updated', onEvidenceUpdated);
  }, [sourceId]);

  useEffect(() => {
    if (!projectId || !sourceId) { setCandidates([]); setSummary(null); return; }
    let cancelled = false;
    async function loadSourceReview() {
      setStatus('Loading saved clips and evidence for this source...');
      try {
        const [candidateResult, evidenceResult] = await Promise.all([
          listSourceCandidates(projectId, sourceId),
          getGameSenseSummary(projectId, sourceId),
        ]);
        if (cancelled) return;
        setCandidates(candidateResult.candidates);
        setSummary(evidenceResult);
        setStatus(candidateResult.candidates.length ? `${candidateResult.candidates.length} saved clip candidate(s).` : 'No saved clips for this source yet.');
      } catch (caught) {
        if (!cancelled) setStatus(caught instanceof Error ? caught.message : 'Unable to load saved clips.');
      }
    }
    loadSourceReview();
    return () => { cancelled = true; };
  }, [projectId, sourceId, refreshToken]);

  const ranked = useMemo(() => [...candidates].sort((a, b) => b.score - a.score), [candidates]);
  const strongestChat = useMemo(() => {
    if (!summary) return null;
    return summary.strongest_by_modality?.chat || summary.strongest_events.find((event) => event.modality === 'chat') || null;
  }, [summary]);
  const hasRankableEvidence = Boolean(summary && summary.total_events > 0);
  const chatTerms = strongestChat ? evidenceStrings(strongestChat, 'top_terms') : [];
  const chatSamples = strongestChat ? evidenceStrings(strongestChat, 'sample_messages') : [];
  const chatHypeScore = strongestChat ? evidenceNumber(strongestChat, 'hype_score') : null;

  async function rerankSourceEvidence() {
    if (!projectId || !sourceId) return;
    if (!hasRankableEvidence) {
      setStatus('No GameSense evidence exists for this source yet. Analyze the stream, import chat, or add gameplay evidence first.');
      return;
    }
    setIsReranking(true);
    setStatus('Titan GameSense is ranking this source’s current evidence...');
    try {
      const result = await generateGameSenseCandidates(projectId, sourceId, true);
      window.dispatchEvent(new CustomEvent('gamesense-evidence-updated', { detail: { sourceId } }));
      setStatus(result.generated_count ? `Titan generated ${result.generated_count} refreshed GameSense clip candidate(s).` : 'Titan found no clip candidates above the current GameSense threshold.');
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : 'Unable to rerank GameSense evidence for this source.');
    } finally {
      setIsReranking(false);
    }
  }

  if (!projectId) return null;

  return <section className="card" style={{ marginTop: 18 }}>
    <h2>Saved clips by source</h2>
    <p style={{ opacity: 0.8 }}>Browse previous candidates and the evidence Titan used for this specific source.</p>
    <label style={{ display: 'grid', gap: 6, marginTop: 10 }}>
      <strong>Source</strong>
      <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} disabled={!sources.length || isReranking}>
        <option value="">Select a source</option>
        {sources.map((source) => <option key={source.source_id} value={source.source_id}>{sourceLabel(source)}</option>)}
      </select>
    </label>
    <div className="button-row" style={{ marginTop: 10 }}>
      <button className="button secondary" type="button" onClick={() => setRefreshToken((value) => value + 1)} disabled={!sourceId || isReranking}>Refresh Review</button>
      <button className="button" type="button" onClick={rerankSourceEvidence} disabled={!sourceId || !hasRankableEvidence || isReranking}>{isReranking ? 'Ranking Evidence...' : 'Rank Evidence Into Clips'}</button>
    </div>
    {!isReranking && sourceId && summary?.total_events === 0 && <p style={{ marginTop: 10, opacity: 0.8 }}>No GameSense evidence yet. Run stream analysis, import chat, or add manual gameplay evidence before ranking clips.</p>}
    {status && <p style={{ marginTop: 10 }}>{status}</p>}
    {summary && <div style={{ marginTop: 12 }}>
      <div className="button-row">
        {Object.entries(summary.modality_counts).filter(([, count]) => count > 0).map(([modality, count]) => <span className="badge" key={modality}>{titleCase(modality)}: {count}</span>)}
      </div>
      {summary.strongest_events.length > 0 && <p style={{ marginTop: 10, opacity: 0.85 }}>
        <strong>Top signal:</strong> {formatTime(summary.strongest_events[0].start_seconds)}–{formatTime(summary.strongest_events[0].end_seconds)} · {titleCase(summary.strongest_events[0].event_type)} · intensity {summary.strongest_events[0].intensity}
      </p>}
      {strongestChat && <div className="card" style={{ marginTop: 10, marginBottom: 0 }}>
        <strong>What chat reacted to</strong>
        <p style={{ margin: '6px 0 0' }}>{formatTime(strongestChat.start_seconds)}–{formatTime(strongestChat.end_seconds)} · intensity {strongestChat.intensity}{chatHypeScore !== null ? ` · hype score ${chatHypeScore}` : ''}</p>
        {chatTerms.length > 0 && <div className="button-row" style={{ marginTop: 8 }}>{chatTerms.map((term) => <span className="badge" key={term}>{titleCase(term)}</span>)}</div>}
        {chatSamples.length > 0 && <div style={{ marginTop: 8 }}>{chatSamples.slice(0, 3).map((sample, index) => <p key={`${sample}-${index}`} style={{ margin: '4px 0', opacity: 0.82 }}>“{sample}”</p>)}</div>}
      </div>}
    </div>}
    {ranked.length > 0 && <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
      {ranked.map((candidate) => <div key={candidate.candidate_id} className="card" style={{ margin: 0 }}>
        <strong>{candidate.score} · {candidate.title}</strong>
        <p style={{ margin: '6px 0 0' }}>{formatTime(candidate.start_seconds)}–{formatTime(candidate.end_seconds)} · {candidate.category.replaceAll('_', ' ')}</p>
      </div>)}
    </div>}
  </section>;
}
