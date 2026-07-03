'use client';

import { useEffect, useMemo, useState } from 'react';
import { Candidate, GameSenseSummary, Source, getGameSenseSummary, listSourceCandidates, listSources } from '../../lib/api';

function sourceLabel(source: Source) {
  return source.title || source.original_filename || source.original_url || `Source ${source.source_id.slice(0, 8)}`;
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

function titleCase(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function SourceCandidateBrowser({ projectId }: { projectId?: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [summary, setSummary] = useState<GameSenseSummary | null>(null);
  const [status, setStatus] = useState('');

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
  }, [projectId, sourceId]);

  const ranked = useMemo(() => [...candidates].sort((a, b) => b.score - a.score), [candidates]);
  if (!projectId) return null;

  return <section className="card" style={{ marginTop: 18 }}>
    <h2>Saved clips by source</h2>
    <p style={{ opacity: 0.8 }}>Browse previous candidates and the evidence Titan used for this specific source.</p>
    <label style={{ display: 'grid', gap: 6, marginTop: 10 }}>
      <strong>Source</strong>
      <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} disabled={!sources.length}>
        <option value="">Select a source</option>
        {sources.map((source) => <option key={source.source_id} value={source.source_id}>{sourceLabel(source)}</option>)}
      </select>
    </label>
    {status && <p style={{ marginTop: 10 }}>{status}</p>}
    {summary && <div style={{ marginTop: 12 }}>
      <div className="button-row">
        {Object.entries(summary.modality_counts).filter(([, count]) => count > 0).map(([modality, count]) => <span className="badge" key={modality}>{titleCase(modality)}: {count}</span>)}
      </div>
      {summary.strongest_events.length > 0 && <p style={{ marginTop: 10, opacity: 0.85 }}>
        <strong>Top signal:</strong> {formatTime(summary.strongest_events[0].start_seconds)}–{formatTime(summary.strongest_events[0].end_seconds)} · {titleCase(summary.strongest_events[0].event_type)} · intensity {summary.strongest_events[0].intensity}
      </p>}
    </div>}
    {ranked.length > 0 && <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
      {ranked.map((candidate) => <div key={candidate.candidate_id} className="card" style={{ margin: 0 }}>
        <strong>{candidate.score} · {candidate.title}</strong>
        <p style={{ margin: '6px 0 0' }}>{formatTime(candidate.start_seconds)}–{formatTime(candidate.end_seconds)} · {candidate.category.replaceAll('_', ' ')}</p>
      </div>)}
    </div>}
  </section>;
}
