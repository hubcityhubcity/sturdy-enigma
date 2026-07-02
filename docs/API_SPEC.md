# Initial API Spec

Base path: /api/v1

## Health

GET /health

Returns service status.

## Projects

POST /projects

Creates a new clipping project.

Fields:
- name
- source_type
- rights_confirmed

GET /projects/{project_id}

Returns project details, source metadata, job history, candidate clips, edit timelines, and exports.

## Sources

POST /projects/{project_id}/sources/upload

Uploads a local video or audio file.

Fields:
- file
- rights_confirmed

POST /projects/{project_id}/sources/link

Creates a source from a pasted link.

Fields:
- url
- rights_confirmed

The first MVP should support direct media links. More source adapters can be added later.

## Jobs

GET /jobs/{job_id}

Returns the current job stage, progress percentage, readable message, timestamps, retry count, and error details.

## Transcripts

GET /projects/{project_id}/transcript

Returns transcript segments and word-level timestamps.

PATCH /projects/{project_id}/transcript/words/{word_id}

Corrects transcript text.

## Candidate Clips

POST /projects/{project_id}/candidates/generate

Generates ranked candidate clips.

Fields:
- min_duration_seconds
- max_duration_seconds
- target_count

GET /projects/{project_id}/candidates

Returns ranked candidate clips.

Candidate fields:
- candidate_id
- start_seconds
- end_seconds
- title
- excerpt
- score
- score_breakdown
- explanation
- risk_flags

## Edit Timeline

POST /candidates/{candidate_id}/edits

Creates an editable timeline from a candidate clip.

PATCH /edits/{edit_id}

Updates trim points, hook text, caption style, crop settings, or preset.

## Presets

GET /presets

Returns available Black Podcast Clips presets.

Initial presets:
- BPC Clean Editorial
- BPC Debate Heat
- BPC Story Mode
- BPC Commentary Reaction

## Exports

POST /edits/{edit_id}/exports

Queues a render job.

Fields:
- format
- include_burned_captions
- include_srt
- include_vtt
- include_metadata

GET /exports/{export_id}

Returns export status and download paths.

## Analytics

POST /exports/{export_id}/metrics

Adds manual performance metrics.

Metrics:
- views
- average_watch_seconds
- completion_rate
- likes
- comments
- shares
- saves
- follows

GET /analytics/insights

Returns performance insights across clips.