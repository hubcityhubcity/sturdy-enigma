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

async function fetchText(url) {
  const response = await fetch(url);
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status} ${text}`);
  }
  return text;
}

async function main() {
  console.log('Titan Clipper AI word-timed captions smoke check');
  console.log(`API: ${API_BASE_URL}`);

  const project = await request('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: `Word Caption Check ${new Date().toISOString()}`,
      source_type: 'link',
      rights_confirmed: true,
    }),
  });

  const sourceResult = await request(`/projects/${project.project_id}/sources/link`, {
    method: 'POST',
    body: JSON.stringify({
      url: DIRECT_MEDIA_URL,
      rights_confirmed: true,
      title: 'Word caption smoke-check media',
    }),
  });

  await request(`/sources/${sourceResult.source.source_id}/transcript/mock`, { method: 'POST' });
  const candidatesResult = await request(`/projects/${project.project_id}/candidates/generate`, { method: 'POST' });
  const candidate = candidatesResult.candidates[0];
  if (!candidate) throw new Error('No candidate returned from candidate generation.');

  const edit = await request(`/candidates/${candidate.candidate_id}/edits`, {
    method: 'POST',
    body: JSON.stringify({
      hook_text: candidate.excerpt,
      caption_preset: 'bpc_clean_editorial',
      crop_mode: 'speaker_focus',
    }),
  });

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

  const rendered = await request(`/exports/${exportRecord.export_id}/render`, { method: 'POST' });
  const metadataUrl = absoluteUrl(rendered.download_urls?.metadata);
  const srtUrl = absoluteUrl(rendered.download_urls?.srt);
  const vttUrl = absoluteUrl(rendered.download_urls?.vtt);
  if (!metadataUrl || !srtUrl || !vttUrl) throw new Error('Expected metadata, SRT, and VTT download URLs.');

  const metadata = JSON.parse(await fetchText(metadataUrl));
  const srt = await fetchText(srtUrl);
  const vtt = await fetchText(vttUrl);

  if (metadata.caption_timing_mode !== 'word_timed') {
    throw new Error(`Expected word_timed captions, received ${metadata.caption_timing_mode || 'none'}.`);
  }
  if (!metadata.caption_word_count || metadata.caption_word_count < 1) {
    throw new Error('Expected at least one timestamped transcript word in export metadata.');
  }
  if (!srt.includes('-->') || !vtt.includes('WEBVTT')) {
    throw new Error('Caption sidecars were not generated in valid SRT/VTT shape.');
  }

  console.log('PASS: word-timed captions selected');
  console.log('Caption words:', metadata.caption_word_count);
  console.log('Caption segments:', metadata.caption_segment_count);
  console.log('Render status:', rendered.status);
  console.log('SRT:', srtUrl);
  console.log('VTT:', vttUrl);
  console.log('Metadata:', metadataUrl);
}

main().catch((error) => {
  console.error('FAIL:', error.message || error);
  process.exit(1);
});
