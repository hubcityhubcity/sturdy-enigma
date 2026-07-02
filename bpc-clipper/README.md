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
- Queue export render jobs for a background worker.
- Serve MP4, SRT, VTT, and metadata files through API download routes.

## Stack

- Web app: Next.js
- API: FastAPI
- Worker: Python scaffold
- Database: SQLite by default, PostgreSQL-ready through `DATABASE_URL`
- Media tools: FFmpeg / FFprobe
- Transcription: provider adapter, mock default, Whisper optional
- Migrations: Alembic

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
11. Render vertical clip immediately or queue it for the worker.
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
alembic upgrade head
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

## Run the render worker locally

Start the API in one terminal. In a second terminal, from `bpc-clipper/services/api` run:

```bash
source .venv/bin/activate
python render_worker.py
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python render_worker.py
```

The worker polls the database for queued render jobs and processes one job at a time.

## Queued render flow

Immediate render still exists:

```text
POST /api/v1/exports/{export_id}/render
```

Queued render uses the worker:

```text
POST /api/v1/exports/{export_id}/queue-render
GET /api/v1/render-jobs/{job_id}
```

Typical queued flow:

1. Create an export.
2. Queue the export render.
3. Start or keep `python render_worker.py` running.
4. Poll the render job until status is `complete` or `failed`.
5. Fetch the export and open the download URLs.

## Database migrations

Alembic files live in:

```text
services/api/migrations
```

Create or update the local database:

```bash
cd bpc-clipper/services/api
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply the new migration:

```bash
alembic upgrade head
```

Rollback one migration:

```bash
alembic downgrade -1
```

Use a non-default database with `DATABASE_URL`:

```bash
DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/bpc_clipper" alembic upgrade head
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

To run the API with Whisper enabled:

```bash
TRANSCRIPTION_PROVIDER=whisper
WHISPER_MODEL=base
uvicorn main:app --reload --port 8000
```

Whisper model choices include `tiny`, `base`, `small`, `medium`, and `large`. Start with `base` for local testing.

## Local database reset during scaffold development

Prefer Alembic migrations first. If the local SQLite database is badly out of sync during scaffold development, a reset is still available.

From `bpc-clipper/services/api`:

```bash
rm -f bpc_clipper.db
alembic upgrade head
```

Then restart the API:

```bash
uvicorn main:app --reload --port 8000
```

On Windows PowerShell:

```powershell
Remove-Item .\bpc_clipper.db -ErrorAction SilentlyContinue
alembic upgrade head
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

## Real transcription check

Use this after creating a project/source through the UI or pipeline script.

With a known source ID:

```bash
SOURCE_ID="your-source-id" TRANSCRIPTION_PROVIDER=whisper node scripts/check-real-transcript.mjs
```

Or with a project ID, using that project's newest source:

```bash
PROJECT_ID="your-project-id" TRANSCRIPTION_PROVIDER=whisper node scripts/check-real-transcript.mjs
```

For a mock check through the real transcript endpoint:

```bash
SOURCE_ID="your-source-id" TRANSCRIPTION_PROVIDER=mock node scripts/check-real-transcript.mjs
```

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

- Wire Producer Mode to queued render jobs.
- Add better caption timing from transcript words.
- Add smart crop/face tracking.
- Add render progress polling.
