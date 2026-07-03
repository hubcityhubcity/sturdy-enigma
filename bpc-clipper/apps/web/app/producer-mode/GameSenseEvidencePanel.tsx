'use client';

import { useEffect, useState } from 'react';
import { GameSenseSummary, getGameSenseSummary } from '../../lib/api';

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

function titleCase(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function GameSenseEvidencePanel({ projectId, refreshToken }: { projectId?: string; refreshToken: number }) {
  const [summary, setSummary] = useState<GameSenseSummary | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!projectId) { setSummary(null); return; }
    let cancelled = false;
    async function load() {
      setIsLoading(true); setError('');
      try {
        const next = await getGameSenseSummary(projectId);
        if (!cancelled) setSummary(next);
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : 'Unable to load GameSense evidence.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [projectId, refreshToken]);

  if (!projectId) return null;
  return (
    <section className="card" style={{ marginTop: 18 }}>
      <h2>Why Titan picked these moments</h2>
      {isLoading && <p>Loading evidence timeline...</p>}
      {error && <p style={{ color: '#ff8a8a' }}><strong>Evidence note:</strong> {error}</p>}
      {summary && <>
        <p><strong>Total signals:</strong> {summary.total_events}</p>
        <div className="button-row" style={{ marginTop: 8 }}>
          {Object.entries(summary.modality_counts).map(([modality, count]) => <span className="badge" key={modality}>{titleCase(modality)}: {count}</span>)}
        </div>
        {summary.strongest_events.length > 0 ? <div style={{ marginTop: 14 }}>
          <h3>Strongest evidence</h3>
          {summary.strongest_events.map((event, index) => <p key={`${event.event_type}-${event.start_seconds}-${index}`} style={{ margin: '7px 0' }}>
            <strong>{formatTime(event.start_seconds)}–{formatTime(event.end_seconds)}</strong> · {titleCase(event.event_type)} · {titleCase(event.modality)} · intensity {event.intensity} · confidence {Math.round(event.confidence * 100)}%
          </p>)}
        </div> : <p style={{ marginTop: 12, opacity: 0.82 }}>Run Analyze Stream, import chat, or add gameplay events to build the evidence timeline.</p>}
      </>}
    </section>
  );
}
