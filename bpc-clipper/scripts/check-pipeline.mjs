const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const DIRECT_MEDIA_URL = process.env.DIRECT_MEDIA_URL || 'https://filesamples.com/samples/video/mp4/sample_640x360.mp4';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = text;
  }

  if (!response.ok) {
    throw new Error(`${options.method || 'GET'} ${path} failed: ${response.status} ${JSON.stringify(payload)}`);
  }

  return payload;
}

function absoluteUrl(path) {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_BASE_URL.replace(/\/api\/v1\/?$/, '')}${path}`;
}

async function main() {
  console.log('BPC Clipper pipeline check');
  console.log(`API: ${API_BASE_URL}`);

  const project = await request('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: `Pipeline Check ${new Date().toISOString()}`,
      source_type: 'link',
      rights_confirmed: true,
    }),
  });
  console.log('Project:', project.project_id);

  const sourceResult = await request(`/projects/${project.project_id}/sources/link`, {
    method: 'POST',
    body: JSON.stringify({
      url: DIRECT_MEDIA_URL,
      rights_confirmed: true,
      title: 'Pipeline check media',
    }),
  });
  console.log('Source:', sourceResult.source.source_id, sourceResult.source.validation_status);

  await request(`/sources/${sourceResult.source.source_id}/transcript/mock`, { method: 'POST' });
  console.log('Transcript: generated mock transcript');

  const candidatesResult = await request(`/projects/${project.project_id}/candidates/generate`, { method: 'POST' });
  const candidate = candidatesResult.candidates[0];
  if (!candidate) throw new Error('No candidate returned from candidate generation');
  console.log('Candidate:', candidate.candidate_id, candidate.score);

  const edit = await request(`/candidates/${candidate.candidate_id}/edits`, {
    method: 'POST',
    body: JSON.stringify({
      hook_text: candidate.excerpt,
      caption_preset: candidate.category === 'debate_heat' ? 'bpc_debate_heat' : 'bpc_clean_editorial',
      crop_mode: 'speaker_focus',
    }),
  });
  console.log('Edit:', edit.edit_id, edit.status);

  const exportRecord = await request(`/edits/${edit.edit_id}/exports`, {
    method: 'POST',
    body: JSON.stringify({
      format: 'vertical_1080x1920',
      include_burned_captions: true,
      include_srt: true,
      include_vtt: true,
      include_metadata: true,
    }),
  });
  console.log('Export queued:', exportRecord.export_id, exportRecord.status);

  const rendered = await request(`/exports/${exportRecord.export_id}/render`, { method: 'POST' });
  console.log('Rendered:', rendered.export_id, rendered.status);

  const urls = rendered.download_urls || {};
  console.log('Download URLs:');
  console.log('  Video:', absoluteUrl(urls.video));
  console.log('  SRT:', absoluteUrl(urls.srt));
  console.log('  VTT:', absoluteUrl(urls.vtt));
  console.log('  Metadata:', absoluteUrl(urls.metadata));

  if (rendered.error) {
    console.log('Render error:', rendered.error);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
