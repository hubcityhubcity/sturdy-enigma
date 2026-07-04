'use client';

import { useEffect, useMemo, useState } from 'react';
import { ChatMessageInput, Source, detectGameSenseChat, generateGameSenseCandidates, listSources } from '../../lib/api';

const example = `[
  { "seconds": 120.2, "author": "viewer1", "text": "NO WAY" },
  { "seconds": 120.8, "author": "viewer2", "text": "SOMEBODY CLIP THAT" },
  { "seconds": 121.1, "author": "viewer3", "text": "W" }
]`;

type ChatPreview = {
  messages: ChatMessageInput[];
  firstSeconds: number;
  lastSeconds: number;
  uniqueAuthors: number;
  outOfOrderCount: number;
};

function sourceLabel(source: Source) {
  return source.title || source.original_filename || source.original_url || `Source ${source.source_id.slice(0, 8)}`;
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
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

function buildPreview(rawJson: string): ChatPreview {
  const messages = normalizeMessages(JSON.parse(rawJson));
  let outOfOrderCount = 0;
  for (let index = 1; index < messages.length; index += 1) {
    if (messages[index].seconds < messages[index - 1].seconds) outOfOrderCount += 1;
  }
  const sortedSeconds = messages.map((message) => message.seconds).sort((first, second) => first - second);
  return {
    messages,
    firstSeconds: sortedSeconds[0],
    lastSeconds: sortedSeconds[sortedSeconds.length - 1],
    uniqueAuthors: new Set(messages.map((message) => message.author).filter(Boolean)).size,
    outOfOrderCount,
  };
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
  const preview = useMemo(() => {
    try { return { value: buildPreview(rawJson), error: '' }; }
    catch (caught) { return { value: null, error: caught instanceof Error ? caught.message : 'Invalid chat JSON.' }; }
  }, [rawJson]);

  useEffect(() => {
    const activeProjectId = projectId;
    if (!activeProjectId) return;
    let cancelled = false;
    async function loadSources() {
      try {
        const result = await listSources(activeProjectId);
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
    const chatPreview = preview.value;
    if (!chatPreview) { setStatus(preview.error); return; }
    setIsImporting(true); setStatus('');
    try {
      const result = await detectGameSenseChat(sourceId, chatPreview.messages, true);
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
    const chatPreview = preview.value;
    if (!chatPreview) { setStatus(preview.error); return; }
    setIsImporting(true); setStatus('Analyzing chat and ranking GameSense clips...');
    try {
      const chatResult = await detectGameSenseChat(sourceId, chatPreview.messages, true);
      const clipResult = await generateGameSenseCandidates(projectId, sourceId, true);
      notifyEvidenceUpdated(sourceId);
      setStatus(clipResult.generated_count ? `Chat analysis found ${chatResult.created_count} spike(s) and generated ${clipResult.generated_count} GameSense clip candidate(s).` : clipResult.message || `Chat analysis found ${chatResult.created_count} spike(s), but no GameSense clip candidate met the current threshold.`);
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
    {preview.value ? <div className="card" style={{ marginTop: 10 }}>
      <strong>Import preview</strong>
      <p style={{ margin: '6px 0 0' }}>{preview.value.messages.length} messages · {formatTime(preview.value.firstSeconds)}–{formatTime(preview.value.lastSeconds)} · {preview.value.uniqueAuthors} named author(s)</p>
      {preview.value.outOfOrderCount > 0 && <p style={{ margin: '6px 0 0', color: '#ffcd75' }}>Timestamp order warning: {preview.value.outOfOrderCount} row(s) are out of order. Titan will still analyze the timestamps, but sorted exports are cleaner.</p>}
    </div> : <p style={{ marginTop: 10, color: '#ff8a8a' }}><strong>Preview error:</strong> {preview.error}</p>}
    <div className="button-row" style={{ marginTop: 10 }}>
      <button className="button secondary" type="button" onClick={() => setRawJson(example)} disabled={isImporting}>Load Example</button>
      <button className="button secondary" type="button" onClick={importChatEvidence} disabled={!sourceId || isImporting || !preview.value}>{isImporting ? 'Working...' : 'Analyze Chat Burst'}</button>
      <button className="button" type="button" onClick={importAndGenerateClips} disabled={!sourceId || isImporting || !preview.value}>{isImporting ? 'Working...' : 'Analyze Chat + Find Clips'}</button>
    </div>
    {status && <p style={{ marginTop: 10 }}>{status}</p>}
  </section>;
}
