'use client';

import { useEffect, useMemo, useState } from 'react';
import { Candidate, Source, listSourceCandidates, listSources } from '../../lib/api';

function sourceLabel(source: Source) {
  return source.title || source.original_filename || source.original_url || `Source ${source.source_id.slice(0, 8)}`;
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

export function SourceCandidateBrowser({ projectId }: { projectId?: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
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
    if (!projectId || !sourceId) { setCandidates([]); return; }
    let cancelled = false;
    async function loadCandidates() {
      setStatus('Loading saved clips for this source...');
      try {
        const result = await listSourceCandidates(projectId, sourceId);
        if (cancelled) return;
        setCandidates(result.candidates);
        setStatus(result.candidates.length ? `${result.candidates.length} saved clip candidate(s).` : 'No saved clips for this source yet.');
      } catch (caught) {
        if (!cancelled) setStatus(caught instanceof Error ? caught.message : 'Unable to load saved clips.');
      }
    }
    loadCandidates();
    return () => { cancelled = true; };
  }, [projectId, sourceId]);

  const ranked = useMemo(() => [...candidates].sort((a, b) => b.score - a.score), [candidates]);
  if (!projectId) return null;

  return <section className="card" style={{ marginTop: 18 }}>
    <h2>Saved clips by source</h2>
    <p style={{ opacity: 0.8 }}>Browse previously generated candidates without rerunning analysis.</p>
    <label style={{ display: 'grid', gap: 6, marginTop: 10 }}>
      <strong>Source</strong>
      <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} disabled={!sources.length}>
        <option value="">Select a source</option>
        {sources.map((source) => <option key={source.source_id} value={source.source_id}>{sourceLabel(source)}</option>)}
      </select>
    </label>
    {status && <p style={{ marginTop: 10 }}>{status}</p>}
    {ranked.length > 0 && <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
      {ranked.map((candidate) => <div key={candidate.candidate_id} className="card" style={{ margin: 0 }}>
        <strong>{candidate.score} · {candidate.title}</strong>
        <p style={{ margin: '6px 0 0' }}>{formatTime(candidate.start_seconds)}–{formatTime(candidate.end_seconds)} · {candidate.category.replaceAll('_', ' ')}</p>
      </div>)}
    </div>}
  </section>;
}
