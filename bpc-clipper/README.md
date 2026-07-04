# Titan Clipper AI

**The AI production system for high-retention short-form content.**

Titan Clipper AI is a local-first application for turning long-form video and podcast content into ranked short-form clip candidates and vertical exports. It is built first for **Black Podcast Clips**, with an architecture designed to grow into a broader creator production platform.

## Official product naming

- **Platform:** Titan AI
- **Main product:** Titan Clipper AI
- **Scoring and recommendation layer:** Titan Brain
- **First flagship use case:** Black Podcast Clips

## Current milestone

Creator workflow, export packaging, and workspace usage foundations.

The app can now:
- Create a project through the FastAPI backend.
- Create a private browser workspace key automatically for the product flow.
- Meter workspace source minutes and exports per monthly cycle.
- Enforce free-plan source-minute and export limits at the import/export endpoints used by the web app.
- Upload a media file or import a direct media link.
- Validate media with FFprobe when available.
- Generate transcript data through a provider adapter. Mock is the default provider.
- Generate ranked candidate clips from transcript segments.
- Score candidates with explainable Hook, Curiosity, Emotion, Debate, Story, and Retention signals.
- Rescore existing candidates through Titan Brain.
- Link candidate clips to the exact source media used for rendering.
- Approve a candidate into an editable timeline.
- Create an export record.
- Render a basic trimmed MP4 with FFmpeg when source media is available.
- Render 1080x1920 vertical exports for Shorts/TikTok/Reels formats.
- Burn segmented captions into the MP4 when requested.
- Queue export render jobs for a background worker.
- Serve MP4, SRT, VTT, and metadata files through API download routes.

## Workspace plans and usage

Titan Clipper now has a plan catalog and workspace quota engine. The browser creates and stores a private workspace key locally, then sends that key with workspace-aware project, source, and export operations.

Current quota configuration is intentionally **non-billing** until a payment provider is connected:

| Plan | Source minutes / month | Exports / month |
| --- | ---: | ---: |
| Free | 30 | 5 |
| Creator | 600 | 120 |
| Studio | 3,000 | 600 |

The live plan endpoint is `GET /api/v1/plans`. A user workspace can be created at `POST /api/v1/workspaces/bootstrap`; the returned access key is shown once and should be stored securely by a production client. Existing local development can omit a key unless `TITAN_REQUIRE_WORKSPACE_KEY=true` is set. When that variable is true, workspace-aware requests must provide `X-Titan-Workspace-Key`.

This milestone does not process payments. It deliberately does not expose a fake self-serve paid upgrade: connect Stripe or another payment provider before enabling plan changes in production.

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
8. Review Titan Brain score breakdowns.
9. Optionally click `Rescore with BPC Brain` to refresh existing candidates.
10. Approve candidate.
11. Create edit timeline.
12. Create export.
13. Render vertical clip immediately or queue it for the worker.
14. Open or download MP4/SRT/VTT/metadata.

## Titan Brain scoring

Titan Brain v1 uses deterministic, explainable heuristic scoring. It is not a guarantee of platform performance. Each candidate receives:

- **Hook** — strength of the opening attention cue.
- **Curiosity** — whether the language creates an information gap or open loop.
- **Emotion** — intensity and emotional language signals.
- **Debate** — tension, disagreement, or challenge signals.
- **Story** — narrative structure and story cues.
- **Retention** — pacing, duration, and filler-word checks.
- **Overall** — weighted blend of the six signals.

Generate new candidates with scores:

```text
POST /api/v1/projects/{project_id}/candidates/generate
```

Refresh scores for existing candidates:

```text
POST /api/v1/projects/{project_id}/candidates/rescore
```

After schema changes, apply migrations before rescoring:

```bash
cd bpc-clipper/services/api
alembic upgrade head
```

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
DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/titan_clipper" alembic upgrade head
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
