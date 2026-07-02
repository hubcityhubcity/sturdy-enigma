'use client';

import { FormEvent, useState } from 'react';
import { createLinkSource, createProject, generateCandidates } from '../../lib/api';

export function NewProjectForm() {
  const [name, setName] = useState('');
  const [sourceType, setSourceType] = useState<'link' | 'upload'>('link');
  const [url, setUrl] = useState('');
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [status, setStatus] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setStatus('Creating project...');

    try {
      if (!rightsConfirmed) {
        throw new Error('Confirm permission before processing the source.');
      }

      const project = await createProject({
        name: name || 'Untitled BPC Project',
        source_type: sourceType,
        rights_confirmed: rightsConfirmed,
      });

      setProjectId(project.project_id);

      if (sourceType === 'link') {
        if (!url) throw new Error('Paste a video link first.');
        setStatus('Queuing link source...');
        const sourceJob = await createLinkSource(project.project_id, {
          url,
          rights_confirmed: rightsConfirmed,
        });
        setJobId(sourceJob.job_id);
      }

      setStatus('Generating mock candidate clips...');
      await generateCandidates(project.project_id);
      setStatus('Ready for Producer Mode.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Something went wrong.');
      setStatus('');
    }
  }

  return (
    <section className="card" style={{ marginTop: 24 }}>
      <h2>Project details</h2>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Project name
          <input
            className="input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Example: Earn Your Leisure episode clips"
          />
        </label>

        <label>
          Source type
          <select
            className="select"
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value as 'link' | 'upload')}
          >
            <option value="link">Paste a link</option>
            <option value="upload">Upload a file</option>
          </select>
        </label>

        {sourceType === 'link' ? (
          <label>
            Video link
            <input
              className="input"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://example.com/video.mp4"
            />
          </label>
        ) : (
          <label>
            Upload file
            <input className="input" type="file" disabled />
            <p>Upload wiring comes next. Link workflow is connected first.</p>
          </label>
        )}

        <label>
          <input
            type="checkbox"
            checked={rightsConfirmed}
            onChange={(event) => setRightsConfirmed(event.target.checked)}
          />{' '}
          I confirm I have permission to process this source.
        </label>

        <div className="button-row">
          <button className="button" type="submit">Create project</button>
          {projectId && (
            <a className="button secondary" href={`/producer-mode?projectId=${projectId}`}>
              Open Producer Mode
            </a>
          )}
        </div>
      </form>

      {status && <p><strong>Status:</strong> {status}</p>}
      {projectId && <p><strong>Project ID:</strong> {projectId}</p>}
      {jobId && <p><strong>Job ID:</strong> {jobId}</p>}
      {error && <p style={{ color: '#ff8a8a' }}><strong>Error:</strong> {error}</p>}
    </section>
  );
}
