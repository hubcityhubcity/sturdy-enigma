'use client';

import { FormEvent, useEffect, useState } from 'react';
import { createLinkSource, createProject, createUploadSource, ensureWorkspace, generateCandidates, getWorkspace, Source, WorkspaceSnapshot } from '../../lib/api';

function friendlyError(error: unknown): string {
  const message = error instanceof Error ? error.message : 'Something went wrong.';
  if (message.includes('source_minutes_limit_reached')) return 'Your workspace has reached its monthly source-minute limit. Review your plan before importing more media.';
  if (message.includes('exports_limit_reached')) return 'Your workspace has reached its monthly export limit. Review your plan before rendering another clip.';
  return message;
}

export function NewProjectForm() {
  const [name, setName] = useState('');
  const [sourceType, setSourceType] = useState<'link' | 'upload'>('link');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [status, setStatus] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [source, setSource] = useState<Source | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot | null>(null);
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    ensureWorkspace('My Titan Workspace').then(setWorkspace).catch((caught) => setError(friendlyError(caught)));
  }, []);

  async function refreshWorkspace() {
    try { setWorkspace(await getWorkspace()); } catch { /* The next workspace action will retry automatically. */ }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isCreating) return;
    setError('');
    setSource(null);
    setIsCreating(true);
    setStatus('Creating your project...');

    try {
      if (!rightsConfirmed) throw new Error('Confirm permission before processing the source.');
      if (sourceType === 'link' && !url.trim()) throw new Error('Paste a direct media link first.');
      if (sourceType === 'upload' && !file) throw new Error('Choose a media file first.');

      const project = await createProject({ name: name.trim() || 'Untitled Titan Clipper Project', source_type: sourceType, rights_confirmed: true });
      setProjectId(project.project_id);
      setStatus(sourceType === 'link' ? 'Importing and validating your media link...' : 'Uploading and validating your media...');
      const sourceJob = sourceType === 'link'
        ? await createLinkSource(project.project_id, { url: url.trim(), rights_confirmed: true })
        : await createUploadSource(project.project_id, { file: file as File, rights_confirmed: true });
      setSource(sourceJob.source);
      await refreshWorkspace();

      if (sourceJob.source.validation_status === 'valid') {
        setStatus('Source ready. Creating your first ranked clip list...');
        await generateCandidates(project.project_id);
        setStatus('Your first clip list is ready for Producer Mode.');
      } else {
        setStatus('Project created, but this source needs attention before Titan can analyze it.');
      }
    } catch (caught) {
      setError(friendlyError(caught));
      setStatus('');
    } finally {
      setIsCreating(false);
    }
  }

  return <section className="card" style={{ marginTop: 24 }}>
    <h2>Start a project</h2>
    {workspace && <div className="card" style={{ marginTop: 12, marginBottom: 0 }}>
      <strong>{workspace.workspace.name} · {workspace.workspace.plan_name}</strong>
      <p style={{ margin: '6px 0 0' }}>{workspace.usage.source_minutes_used} / {workspace.usage.source_minutes_limit} source minutes used this month · {workspace.usage.exports_used} / {workspace.usage.exports_limit} exports created</p>
    </div>}
    <form className="form" onSubmit={handleSubmit} style={{ marginTop: 18 }}>
      <label>Project name<input className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="Example: Hub City interview clips" disabled={isCreating} /></label>
      <label>Source type<select className="select" value={sourceType} onChange={(event) => setSourceType(event.target.value as 'link' | 'upload')} disabled={isCreating}><option value="link">Paste a direct media link</option><option value="upload">Upload a video or audio file</option></select></label>
      {sourceType === 'link' ? <label>Direct media URL<input className="input" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/video.mp4" inputMode="url" disabled={isCreating} /><span style={{ opacity: 0.72 }}>Use a direct downloadable media file, not a general webpage link.</span></label> : <label>Upload source file<input className="input" type="file" accept="video/*,audio/*" onChange={(event) => setFile(event.target.files?.[0] || null)} disabled={isCreating} />{file && <span style={{ opacity: 0.72 }}>{file.name}</span>}</label>}
      <label><input type="checkbox" checked={rightsConfirmed} onChange={(event) => setRightsConfirmed(event.target.checked)} disabled={isCreating} /> I confirm I have permission to process and repurpose this source.</label>
      <div className="button-row"><button className="button" type="submit" disabled={isCreating}>{isCreating ? 'Building your project...' : 'Create project and find clips'}</button>{projectId && source?.validation_status === 'valid' && <a className="button secondary" href={`/producer-mode?projectId=${projectId}`}>Review ranked clips</a>}</div>
    </form>
    {status && <p style={{ marginTop: 16 }}><strong>Project progress:</strong> {status}</p>}
    {source && <div className="card" style={{ marginTop: 16, marginBottom: 0 }}><h3>Source check</h3><p><strong>{source.validation_status === 'valid' ? 'Ready to analyze' : 'Needs attention'}</strong>{source.validation_message ? ` — ${source.validation_message}` : ''}</p>{source.duration_seconds && <p><strong>Length:</strong> {Math.round(source.duration_seconds)} seconds</p>}</div>}
    {error && <p style={{ color: '#ff8a8a', marginTop: 16 }}><strong>Could not continue:</strong> {error}</p>}
  </section>;
}
