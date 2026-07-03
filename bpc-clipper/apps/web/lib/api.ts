export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '');

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

export type ScoreSignal = {
  name: string;
  score: number;
  explanation: string;
};

export type GameSenseEvidence = {
  event_type: string;
  modality: string;
  start_seconds: number;
  end_seconds: number;
  intensity: number;
  confidence: number;
  evidence?: Record<string, unknown>;
};

export type GameSenseEvent = {
  event_id: string;
  project_id: string;
  source_id?: string | null;
  event_type: string;
  modality: string;
  start_seconds: number;
  end_seconds: number;
  intensity: number;
  confidence: number;
  evidence?: Record<string, unknown>;
};

export type ScoreBreakdown = {
  hook?: ScoreSignal;
  curiosity?: ScoreSignal;
  emotion?: ScoreSignal;
  debate?: ScoreSignal;
  story?: ScoreSignal;
  retention?: ScoreSignal;
  overall?: ScoreSignal;
  engine?: string;
  evidence_count?: number;
  evidence?: GameSenseEvidence[];
};

export type Candidate = {
  candidate_id: string;
  project_id: string;
  source_id?: string | null;
  start_seconds: number;
  end_seconds: number;
  title: string;
  excerpt: string;
  score: number;
  category: string;
  explanation: string;
  score_breakdown?: ScoreBreakdown;
  risk_flags: string[];
  status?: string;
};

export type EditTimeline = {
  edit_id: string;
  project_id: string;
  candidate_clip_id: string;
  start_seconds: number;
  end_seconds: number;
  hook_text?: string | null;
  caption_preset: string;
  crop_mode: string;
  status: string;
  settings: Record<string, unknown>;
};

export type ExportRecord = {
  export_id: string;
  project_id: string;
  edit_timeline_id: string;
  status: string;
  format: string;
  include_burned_captions: boolean;
  include_srt: boolean;
  include_vtt: boolean;
  include_metadata: boolean;
  video_path?: string | null;
  srt_path?: string | null;
  vtt_path?: string | null;
  metadata_path?: string | null;
  download_urls?: { video?: string | null; srt?: string | null; vtt?: string | null; metadata?: string | null };
  error?: string | null;
};

export type RenderJob = {
  job_id: string;
  export_id?: string | null;
  project_id: string;
  stage: string;
  progress: number;
  message: string;
  status: string;
  error?: string | null;
};

export function absoluteApiUrl(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_ORIGIN}${path}`;
}

async function jsonRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function createProject(input: { name: string; source_type: 'upload' | 'link' | 'unknown'; rights_confirmed: boolean }): Promise<Project> {
  return jsonRequest('/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) });
}

export async function createLinkSource(projectId: string, input: { url: string; rights_confirmed: boolean }): Promise<{ project_id: string; source: Source; job_id: string; status: string }> {
  return jsonRequest(`/projects/${projectId}/sources/link`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) });
}

export async function createUploadSource(projectId: string, input: { file: File; rights_confirmed: boolean }): Promise<{ project_id: string; source: Source; job_id: string; status: string }> {
  const body = new FormData();
  body.append('file', input.file);
  body.append('rights_confirmed', String(input.rights_confirmed));
  return jsonRequest(`/projects/${projectId}/sources/upload`, { method: 'POST', body });
}

export async function listSources(projectId: string): Promise<{ project_id: string; sources: Source[] }> {
  return jsonRequest(`/projects/${projectId}/sources`, { cache: 'no-store' });
}

export async function detectGameSenseAudio(sourceId: string, replaceExisting = true): Promise<{ source_id: string; project_id: string; detector: string; created_count: number; events: GameSenseEvent[]; message?: string }> {
  return jsonRequest(`/sources/${sourceId}/gamesense/detect/audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ replace_existing: replaceExisting }),
  });
}

export async function generateCandidates(projectId: string): Promise<{ project_id: string; candidates: Candidate[] }> {
  return jsonRequest(`/projects/${projectId}/candidates/generate`, { method: 'POST' });
}

export async function generateGameSenseCandidates(projectId: string, sourceId?: string | null, replaceExisting = false): Promise<{ project_id: string; source_id?: string | null; generated_count: number; candidates: Candidate[] }> {
  const search = new URLSearchParams();
  if (sourceId) search.set('source_id', sourceId);
  if (replaceExisting) search.set('replace_existing', 'true');
  const query = search.toString();
  return jsonRequest(`/projects/${projectId}/gamesense/candidates/generate${query ? `?${query}` : ''}`, { method: 'POST' });
}

export async function rescoreCandidates(projectId: string): Promise<{ project_id: string; updated_count: number; candidates: Candidate[] }> {
  return jsonRequest(`/projects/${projectId}/candidates/rescore`, { method: 'POST' });
}

export async function listCandidates(projectId: string): Promise<{ project_id: string; candidates: Candidate[] }> {
  return jsonRequest(`/projects/${projectId}/candidates`, { cache: 'no-store' });
}

export async function createEditTimeline(candidateId: string, input: { hook_text?: string; caption_preset?: string; crop_mode?: string } = {}): Promise<EditTimeline> {
  return jsonRequest(`/candidates/${candidateId}/edits`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hook_text: input.hook_text, caption_preset: input.caption_preset || 'bpc_clean_editorial', crop_mode: input.crop_mode || 'speaker_focus' }) });
}

export async function createExport(editId: string, input: { format?: string; include_burned_captions?: boolean; include_srt?: boolean; include_vtt?: boolean; include_metadata?: boolean } = {}): Promise<ExportRecord> {
  return jsonRequest(`/edits/${editId}/exports`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ format: input.format || 'vertical_1080x1920', include_burned_captions: input.include_burned_captions ?? true, include_srt: input.include_srt ?? true, include_vtt: input.include_vtt ?? true, include_metadata: input.include_metadata ?? true }) });
}

export async function renderExport(exportId: string): Promise<ExportRecord> {
  return jsonRequest(`/exports/${exportId}/render`, { method: 'POST' });
}

export async function queueRenderExport(exportId: string): Promise<RenderJob> {
  return jsonRequest(`/exports/${exportId}/queue-render`, { method: 'POST' });
}

export async function getRenderJob(jobId: string): Promise<RenderJob> {
  return jsonRequest(`/render-jobs/${jobId}`, { cache: 'no-store' });
}

export async function getExport(exportId: string): Promise<ExportRecord> {
  return jsonRequest(`/exports/${exportId}`, { cache: 'no-store' });
}
