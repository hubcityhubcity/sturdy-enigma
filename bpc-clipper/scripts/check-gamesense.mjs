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

async function main() {
  console.log('Titan GameSense API smoke check');
  console.log(`API: ${API_BASE_URL}`);

  const project = await request('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: `GameSense Check ${new Date().toISOString()}`,
      source_type: 'link',
      rights_confirmed: true,
    }),
  });

  const sourceResult = await request(`/projects/${project.project_id}/sources/link`, {
    method: 'POST',
    body: JSON.stringify({
      url: DIRECT_MEDIA_URL,
      rights_confirmed: true,
      title: 'GameSense smoke-check stream',
    }),
  });
  const sourceId = sourceResult.source.source_id;

  const eventResult = await request(`/projects/${project.project_id}/gamesense/events`, {
    method: 'POST',
    body: JSON.stringify({
      events: [
        { source_id: sourceId, event_type: 'clutch', modality: 'gameplay', start_seconds: 100, end_seconds: 103, intensity: 98, confidence: 0.96, evidence: { game: 'demo', cue: 'final elimination' } },
        { source_id: sourceId, event_type: 'scream', modality: 'audio', start_seconds: 103, end_seconds: 104.5, intensity: 91, confidence: 0.94, evidence: { peak_db: -4 } },
        { source_id: sourceId, event_type: 'reaction', modality: 'facecam', start_seconds: 103.1, end_seconds: 105.5, intensity: 89, confidence: 0.9, evidence: { expression: 'shock' } },
        { source_id: sourceId, event_type: 'chat_spike', modality: 'chat', start_seconds: 104, end_seconds: 107, intensity: 94, confidence: 0.97, evidence: { messages_per_second: 42 } },
      ],
    }),
  });

  if (eventResult.created_count !== 4) {
    throw new Error(`Expected 4 stored events; received ${eventResult.created_count}.`);
  }

  const generated = await request(`/projects/${project.project_id}/gamesense/candidates/generate?source_id=${encodeURIComponent(sourceId)}`, {
    method: 'POST',
  });
  const best = generated.candidates?.[0];
  if (!best) throw new Error('GameSense did not return a candidate.');
  if (best.category !== 'clutch') throw new Error(`Expected clutch category; received ${best.category}.`);
  if (best.start_seconds > 92 || best.end_seconds < 109) throw new Error('Candidate did not preserve setup and reaction context.');
  if (best.score_breakdown?.engine !== 'gamesense_v1') throw new Error('Candidate did not retain GameSense evidence metadata.');

  console.log('PASS: GameSense generated a ranked gaming candidate');
  console.log('Candidate:', best.candidate_id);
  console.log('Category:', best.category);
  console.log('Score:', best.score);
  console.log('Window:', `${best.start_seconds}s → ${best.end_seconds}s`);
  console.log('Evidence signals:', best.score_breakdown.evidence_count);
}

main().catch((error) => {
  console.error('FAIL:', error.message || error);
  process.exit(1);
});
