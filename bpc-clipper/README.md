# BPC Clipper

Black Podcast Clips AI Clipper is a local-first application for turning long-form podcast content into ranked short-form clip candidates and vertical exports.

## Current milestone

Producer workflow scaffold.

The app can now:
- Create a project through the FastAPI backend.
- Upload a media file or import a direct media link.
- Validate media with FFprobe when available.
- Generate transcript data through a provider adapter. Mock is the default provider.
- Generate ranked candidate clips from transcript segments.
- Link candidate clips to the exact source media used for rendering.
- Approve a candidate into an editable timeline.
- Create an export record.
- Render a basic trimmed MP4 with FFmpeg when source media is available.
- Render 1080x1920 vertical exports for Shorts/TikTok/Reels formats.
- Burn segmented captions into the MP4 when requested.
- Serve MP4, SRT, VTT, and metadata files through API download routes.

## Stack

- Web app: Next.js
- API: FastAPI
- Worker: Python scaffold
- Database: SQLite by default, PostgreSQL-ready through `DATABASE_URL`
- Media tools: FFmpeg / FFprobe
- Transcription: provider adapter, mock default, Whisper scaffold optional

## Main workflow

1. Create project.
2. Upload a file or paste a direct media link.
3. Confirm permission to process the source.
4. Import media.
5. Generate or load transcript.
6. Generate candidate clips.
7. Review in Producer Mode.
8. Approve candidate.
9. Create edit timeline.
10. Create export.
11. Render vertical clip.
12. Open or download MP4/SRT/VTT/metadata.

## Folder layout

```text
apps/web
services/api
services/worker
packages/shared
packages/presets
infra
scripts
```

## Prerequisites

Install:

- Python 3.11+
- Node.js 18+
- FFmpeg and FFprobe

Check FFmpeg:

```bash
ffmpeg -version
ffprobe -version
```

## Run the API locally

From `bpc-clipper/services/api`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

## Optional Whisper transcription setup

The default transcription provider is `mock`, which keeps the pipeline fast and dependency-light during scaffold development.

Optional Whisper dependencies live in:

```text
services/api/requirements-whisper.txt
```

Install them from `bpc-clipper/services/api`:

```bash
pip install -r requirements-whisper.txt
```

Environment variables:

```bash
TRANSCRIPTION_PROVIDER=mock
WHISPER_MODEL=base
```

To prepare for Whisper later:

```bash
TRANSCRIPTION_PROVIDER=whisper
WHISPER_MODEL=base
uvicorn main:app --reload --port 8000
```

Important: the Whisper provider is currently a scaffold and intentionally raises until model loading is implemented. Keep `TRANSCRIPTION_PROVIDER=mock` for the working pipeline until the real provider is completed.

## Local database reset during scaffold development

This scaffold currently uses SQLAlchemy `create_all()` and does not yet include Alembic migrations.

When the data model changes, an existing local SQLite database may not receive new columns automatically. If you see an error such as `no such column: candidate_clips.source_id`, reset the local API database.

From `bpc-clipper/services/api`:

```bash
rm -f bpc_clipper.db
```

Then restart the API:

```bash
uvicorn main:app --reload --port 8000
```

On Windows PowerShell:

```powershell
Remove-Item .\bpc_clipper.db -ErrorAction SilentlyContinue
uvicorn main:app --reload --port 8000
```

This deletes local scaffold data only. Do not use this reset approach for production data.

## Run the web app locally

From `bpc-clipper/apps/web`:

```bash
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

## Connected UI flow

1. Start the API.
2. Start the web app.
3. Open `/new-project`.
4. Enter a project name.
5. Choose upload or paste a direct media link.
6. Confirm permission.
7. Submit.
8. Open Producer Mode from the result.
9. Click `Approve + Render` on a candidate.
10. Open the generated MP4/SRT/VTT/metadata links.

## End-to-end pipeline check

Start the API first, then from `bpc-clipper` run:

```bash
node scripts/check-pipeline.mjs
```

Optionally provide your own direct media URL:

```bash
DIRECT_MEDIA_URL="https://example.com/video.mp4" node scripts/check-pipeline.mjs
```

Or point the script at a different API host:

```bash
API_BASE_URL="http://localhost:8000/api/v1" node scripts/check-pipeline.mjs
```

The script will:

1. Create a project.
2. Import a direct media URL.
3. Generate a mock transcript.
4. Generate candidates.
5. Approve the top candidate.
6. Create a vertical export.
7. Render the export.
8. Print MP4, SRT, VTT, and metadata download URLs.

## Export download routes

For any completed export:

```text
GET /api/v1/exports/{export_id}/files/video
GET /api/v1/exports/{export_id}/files/srt
GET /api/v1/exports/{export_id}/files/vtt
GET /api/v1/exports/{export_id}/files/metadata
```

## First MVP target

A user can create a project, add a source, generate candidates, approve one, render a vertical clip with captions, and open the generated output files from Producer Mode.

## Next engineering targets

- Implement Whisper provider model loading.
- Add Alembic migrations.
- Add render queue/background worker.
- Add better caption timing from transcript words.
- Add smart crop/face tracking.
- Add render progress polling.
