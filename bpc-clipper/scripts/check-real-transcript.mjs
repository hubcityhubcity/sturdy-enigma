const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const PROJECT_ID = process.env.PROJECT_ID;
const SOURCE_ID = process.env.SOURCE_ID;
const PROVIDER = process.env.TRANSCRIPTION_PROVIDER || 'whisper';

async function request(path, options = {}) {
  const response = await fetch(API_BASE_URL + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(JSON.stringify(payload));
  }
  return payload;
}

async function findSourceId() {
  if (SOURCE_ID) return SOURCE_ID;
  if (!PROJECT_ID) {
    throw new Error('Set SOURCE_ID, or set PROJECT_ID to use the newest source from that project.');
  }
  const sources = await request('/projects/' + PROJECT_ID + '/sources');
  const source = sources.sources && sources.sources[0];
  if (!source) throw new Error('No source found for project ' + PROJECT_ID);
  return source.source_id;
}

async function main() {
  const sourceId = await findSourceId();
  console.log('Real transcript check');
  console.log('Source:', sourceId);
  console.log('Provider:', PROVIDER);

  const transcript = await request('/sources/' + sourceId + '/transcript/real', {
    method: 'POST',
    body: JSON.stringify({ provider: PROVIDER, force: true }),
  });

  console.log('Transcript:', transcript.transcript_id);
  console.log('Provider used:', transcript.provider);
  console.log('Segments:', transcript.segments.length);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
