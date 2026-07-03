'use client';

import { FormEvent, useMemo, useState } from 'react';
import { createLinkSource, createProject, createUploadSource, generateCandidates, Source } from '../../lib/api';
import { WorkflowSteps } from './WorkflowSteps';

export function NewProjectForm() {
  const [name, setName] = useState('');
  const [sourceType, setSourceType] = useState<'link' | 'upload'>('link');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [status, setStatus] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [source, setSource] = useState<Source | null>(null);
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const canSubmit = Boolean(rightsConfirmed && !isCreating && (sourceType === 'link' ? url.trim() : file));
  const sourceReady = source?.validation_status === 'valid';
  const steps = useMemo(() => [
    { label: 'Create project', detail: projectId ? 'Project created. Your workspace is ready.' : 'Name the project and choose your source.', state: projectId ? 'complete' : 'active' },
    { label: 'Add and validate source', detail: source ? (sourceReady ? 'Source validated and ready to analyze.' : source.validation_message || 'Source needs attention before rendering.') : 'Upload a file or provide a direct media URL.', state: source ? (sourceReady ? 'complete' : 'active') : projectId ? 'active' : 'upcoming' },
    { label: 'Review ranked clips', detail: sourceReady ? 'Open Producer Mode to analyze, rank, and choose the strongest moments.' : 'Titan will rank clips after the source is available.', state: sourceReady ? 'active' : 'upcoming' },
    { label: 'Render export package', detail: 'Approve the best clip, then render MP4, captions, and metadata.', state: 'upcoming' },
  ] as const, [projectId, source, sourceReady]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setError('');
    setSource(null);
    setIsCreating(true);
    setStatus('Creating your project...');

    try {
      const project = await createProject({
        name: name.trim() || 'Untitled Titan Clipper Project',
        source_type: sourceType,
        rights_confirmed: rightsConfirmed,
      });
      setProjectId(project.project_id);

      let sourceJob;
      if (sourceType === 'link') {
        setStatus('Importing and validating your media link...');
        sourceJob = await createLinkSource(project.project_id, { url: url.trim(), rights_confirmed: true });
      } else {
        setStatus('Uploading and validating your media...');
        sourceJob = await createUploadSource(project.project_id, { file: file as File, rights_confirmed: true });
      }
      setSource(sourceJob.source);

      if (sourceJob.source.validation_status === 'valid') {
        setStatus('Your source is ready. Creating an initial ranked clip list...');
        await generateCandidates(project.project_id);
        setStatus('Your first clip list is ready. Open Producer Mode to review it.');
      } else {
        setStatus('Project created. This source needs attention before Titan can analyze or render it.');
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Something went wrong while creating this project.');
      setStatus('');
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <section className="card" style={{ marginTop: 24 }}>
      <h2>Create your first clip project</h2>
      <p style={{ opacity: 0.82 }}>Titan only processes media you have permission to use. Direct media URLs and local uploads are supported.</p>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Project name
          <input className="input" value={name} onChange={(event) => setName(event.target.value)} placeholder="Example: Hub City interview clips" disabled={isCreating} />
        </label>

        <label>
          Source type
          <select className="select" value={sourceType} onChange={(event) => setSourceType(event.target.value as 'link' | 'upload')} disabled={isCreating}>
            <option value="link">Paste a direct media link</option>
            <option value="upload">Upload a video or audio file</option>
          </select>
        </label>

        {sourceType === 'link' ? (
          <label>
            Direct media URL
            <input className="input" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/video.mp4" inputMode="url" disabled={isCreating} />
            <span style={{ opacity: 0.72 }}>Use a direct downloadable media file, not a general webpage link.</span>
          </label>
        ) : (
          <label>
            Upload source file
            <input className="input" type="file" accept="video/*,audio/*" onChange={(event) => setFile(event.target.files?.[0] || null)} disabled={isCreating} />
            {file && <span style={{ opacity: 0.72 }}>{file.name}</span>}
          </label>
        )}

        <label>
          <input type="checkbox" checked={rightsConfirmed} onChange={(event) => setRightsConfirmed(event.target.checked)} disabled={isCreating} />{' '}
          I confirm I have permission to process and repurpose this source.
        </label>

        <div className="button-row">
          <button className="button" type="submit" disabled={!canSubmit}>{isCreating ? 'Building your project...' : 'Create project and find clips'}</button>
          {projectId && sourceReady && <a className="button secondary" href={`/producer-mode?projectId=${projectId}`}>Review ranked clips</a>}
        </div>
      </form>

      {status && <div className="card" style={{ marginTop: 16, marginBottom: 0 }}><strong>Project progress</strong><p style={{ marginBottom: 0 }}>{status}</p></div>}
      {source && <div className="card" style={{ marginTop: 16, marginBottom: 0 }}>
        <h3>Source check</h3>
        <p><strong>{source.validation_status === 'valid' ? 'Ready to analyze' : 'Needs attention'}</strong>{source.validation_message ? ` — ${source.validation_message}` : ''}</p>
        {source.duration_seconds && <p><strong>Length:</strong> {Math.round(source.duration_seconds)} seconds</p>}
        {source.width && source.height && <p><strong>Frame:</strong> {source.width} × {source.height}</p>}
      </div>}
      {error && <p style={{ color: '#ff8a8a', marginTop: 16 }}><strong>Could not create project:</strong> {error}</p>}
      <WorkflowSteps steps={steps} />
    </section>
  );
}
