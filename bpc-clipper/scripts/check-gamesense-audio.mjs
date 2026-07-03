const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const DIRECT_MEDIA_URL = process.env.DIRECT_MEDIA_URL || 'https://filesamples.com/samples/video/mp4/sample_640x360.mp4';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const text = await response.text();
  let payload;
  try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
  if (!response.ok) {
    throw new Error(`${options.method || 'GET'} ${path} failed: ${response.status} ${JSON.stringify(payload)}`);
  }
  return payload;
}

async function main() {
  console.log('Titan GameSense audio-scan smoke check');
  console.log(`API: ${API_BASE_URL}`);

  const project = await request('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: `Audio Scan Check ${new Date().toISOString()}`,
      source_type: 'link',
      rights_confirmed: true,
    }),
  });

  const sourceResult = await request(`/projects/${project.project_id}/sources/link`, {
    method: 'POST',
    body: JSON.stringify({ url: DIRECT_MEDIA_URL, rights_confirmed: true, title: 'Audio scan smoke-check media' }),
  });
  const sourceId = sourceResult.source.source_id;

  const detected = await request(`/sources/${sourceId}/gamesense/detect/audio`, {
    method: 'POST',
    body: JSON.stringify({ replace_existing: true }),
  });

  if (detected.source_id !== sourceId) throw new Error('Audio detector returned the wrong source.');
  if (detected.detector !== 'ffmpeg_astats_audio_spike_v1') throw new Error(`Unexpected detector: ${detected.detector}`);
  if (!Array.isArray(detected.events) || detected.created_count !== detected.events.length) {
    throw new Error('Audio detector count does not match its returned events.');
  }
  for (const event of detected.events) {
    if (event.event_type !== 'audio_spike' || event.modality !== 'audio') throw new Error('Returned event is not an audio spike.');
    if (event.start_seconds > event.end_seconds) throw new Error('Audio event has an invalid time window.');
    if (!event.evidence?.detector || event.evidence.detector !== 'ffmpeg_astats_audio_spike_v1') throw new Error('Audio event is missing detector evidence.');
  }

  console.log('PASS: GameSense audio scan completed');
  console.log('Audio spikes:', detected.created_count);
  console.log('Source:', sourceId);
  console.log('Note: zero spikes is valid for calm/sample media; this verifies the automatic scan flow.');
}

main().catch((error) => {
  console.error('FAIL:', error.message || error);
  process.exit(1);
});
