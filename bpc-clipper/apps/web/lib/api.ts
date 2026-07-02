export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export type Project = {
  project_id: string;
  name: string;
  source_type: 'upload' | 'link' | 'unknown';
  rights_confirmed: boolean;
  status: string;
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
}): Promise<{ project_id: string; job_id: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sources/link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (!response.ok) throw new Error('Failed to create link source');
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
