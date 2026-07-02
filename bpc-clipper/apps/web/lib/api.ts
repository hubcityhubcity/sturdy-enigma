export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export type Project = {
  project_id: string;
  name: string;
  source_type: 'upload' | 'link' | 'unknown';
  rights_confirmed: boolean;
  status: string;
};

export type Source = {
  source_id: string;
  project_id: string;
  source_type: 'upload' | 'link';
  original_filename?: string | null;
  original_url?: string | null;
  title?: string | null;
  storage_path?: string | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  video_codec?: string | null;
  audio_codec?: string | null;
  validation_status: string;
  validation_message?: string | null;
  rights_confirmed: boolean;
};

export type Candidate = {
  candidate_id: string;
  project_id: string;
  start_seconds: number;
  end_seconds: number;
  title: string;
  excerpt: string;
  score: number;
  category: string;
  explanation: string;
  risk_flags: string[];
};

export async function createProject(input: {
  name: string;
  source_type: 'upload' | 'link' | 'unknown';
  rights_confirmed: boolean;
}): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!response.ok) throw new Error('Failed to create project');
  return response.json();
}

export async function createLinkSource(projectId: string, input: {
  url: string;
  rights_confirmed: boolean;
}): Promise<{ project_id: string; source: Source; job_id: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sources/link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!response.ok) throw new Error('Failed to create link source');
  return response.json();
}

export async function createUploadSource(projectId: string, input: {
  file: File;
  rights_confirmed: boolean;
}): Promise<{ project_id: string; source: Source; job_id: string; status: string }> {
  const body = new FormData();
  body.append('file', input.file);
  body.append('rights_confirmed', String(input.rights_confirmed));

  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sources/upload`, {
    method: 'POST',
    body,
  });

  if (!response.ok) throw new Error('Failed to upload source');
  return response.json();
}

export async function generateCandidates(projectId: string): Promise<{ project_id: string; candidates: Candidate[] }> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/candidates/generate`, {
    method: 'POST',
  });

  if (!response.ok) throw new Error('Failed to generate candidates');
  return response.json();
}

export async function listCandidates(projectId: string): Promise<{ project_id: string; candidates: Candidate[] }> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/candidates`, {
    cache: 'no-store',
  });

  if (!response.ok) throw new Error('Failed to list candidates');
  return response.json();
}
