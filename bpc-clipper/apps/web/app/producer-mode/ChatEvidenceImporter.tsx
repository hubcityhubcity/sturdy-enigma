'use client';

import { useEffect, useState } from 'react';
import { ChatMessageInput, Source, detectGameSenseChat, generateGameSenseCandidates, listSources } from '../../lib/api';

const example = `[
  { "seconds": 120.2, "author": "viewer1", "text": "NO WAY" },
  { "seconds": 120.8, "author": "viewer2", "text": "SOMEBODY CLIP THAT" },
  { "seconds": 121.1, "author": "viewer3", "text": "W" }
]`;

function sourceLabel(source: Source) {
  return source.title || source.original_filename || source.original_url || `Source ${source.source_id.slice(0, 8)}`;
}

function normalizeMessages(value: unknown): ChatMessageInput[] {
  if (!Array.isArray(value) || !value.length) throw new Error('Paste a JSON array with at least one chat message.');
  return value.map((item, index) => {
    if (!item || typeof item !== 'object') throw new Error(`Chat row ${index + 1} must be an object.`);
    const row = item as Record<string, unknown>;
    if (typeof row.seconds !== 'number' || !Number.isFinite(row.seconds) || row.seconds < 0) throw new Error(`Chat row ${index + 1} needs a non-negative numeric seconds value.`);
    if (typeof row.text !== 'string') throw new Error(`Chat row ${index + 1} needs text.`);
    if (row.author !== undefined && row.author !== null && typeof row.author !== 'string') throw new Error(`Chat row ${index + 1} author must be text when provided.`);
    return { seconds: row.seconds, text: row.text, author: typeof row.author === 'string' ? row.author : null };
  });
}

function notifyEvidenceUpdated(sourceId: string) {
  window.dispatchEvent(new CustomEvent('gamesense-evidence-updated', { detail: { sourceId } }));
}

export function ChatEvidenceImporter({ projectId }: { projectId?: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceId, setSourceId] = useState('');
  const [rawJson, setRawJson] = useState(example);
  const [status, setStatus] = useState('');
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    async function loadSources() {
      try {
        const result = await listSources(projectId);
        if (cancelled) return;
        setSources(result.sources);
        setSourceId(result.sources[result.sources.length - 1]?.source_id || '');
      } catch (caught) {
        if (!cancelled) setStatus(caught instanceof Error ? caught.message : 'Unable to load project sources.');
      }
    }
    loadSources();
    return () => { cancelled = true; };
  }, [projectId]);

  async function importChatEvidence() {
    if (!sourceId) { setStatus('Select a source first.'); return; }
    setIsImporting(true); setStatus('');
    try {
      const messages = normalizeMessages(JSON.parse(rawJson));
      const result = await detectGameSenseChat(sourceId, messages, true);
      notifyEvidenceUpdated(sourceId);
      setStatus(result.created_count ? `Imported chat evidence and found ${result.created_count} chat spike(s).` : 'Chat was imported, but no burst was strong enough to become a spike.');
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : 'Unable to import chat evidence.');
    } finally {
      setIsImporting(false);
    }
  }

  async function importAndGenerateClips() {
    if (!projectId || !sourceId) { setStatus('Select a source first.'); return; }
    setIsImporting(true); setStatus('Analyzing chat and ranking GameSense clips...');
    try {
      const messages = normalizeMessages(JSON.parse(rawJson));
      const chatResult = await detectGameSenseChat(sourceId, messages, true);
      const clipResult = await generateGameSenseCandidates(projectId, sourceId, true);
      notifyEvidenceUpdated(sourceId);
      setStatus(`Chat analysis found ${chatResult.created_count} spike(s) and generated ${clipResult.generated_count} GameSense clip candidate(s).`);
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : 'Unable to analyze chat and generate clips.');
    } finally {
      setIsImporting(false);
    }
  }

  if (!projectId) return null;
  return <section className="card" style={{ marginTop: 18 }}>
    <h2>Import chat evidence</h2>
    <p style={{ opacity: 0.8 }}>Paste normalized timestamped chat messages. Direct Twitch or YouTube chat connection is not included yet.</p>
    <label style={{ display: 'grid', gap: 6, marginTop: 10 }}>
      <strong>Source</strong>
      <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} disabled={!sources.length || isImporting}>
        <option value="">Select a source</option>
        {sources.map((source) => <option key={source.source_id} value={source.source_id}>{sourceLabel(source)}</option>)}
      </select>
    </label>
    <label style={{ display: 'grid', gap: 6, marginTop: 12 }}>
      <strong>Chat JSON</strong>
      <textarea value={rawJson} onChange={(event) => setRawJson(event.target.value)} rows={9} spellCheck={false} style={{ width: '100%', fontFamily: 'monospace' }} disabled={isImporting} />
    </label>
    <div className="button-row" style={{ marginTop: 10 }}>
      <button className="button secondary" type="button" onClick={() => setRawJson(example)} disabled={isImporting}>Load Example</button>
      <button className="button secondary" type="button" onClick={importChatEvidence} disabled={!sourceId || isImporting}>{isImporting ? 'Working...' : 'Analyze Chat Burst'}</button>
      <button className="button" type="button" onClick={importAndGenerateClips} disabled={!sourceId || isImporting}>{isImporting ? 'Working...' : 'Analyze Chat + Find Clips'}</button>
    </div>
    {status && <p style={{ marginTop: 10 }}>{status}</p>}
  </section>;
}
