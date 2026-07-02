# BPC Clipper

Black Podcast Clips AI Clipper is a local-first application for turning long-form podcast content into ranked short-form clip candidates.

## Current milestone
Connected foundation scaffold.

The web app can now:
- Create a project through the FastAPI backend.
- Queue a pasted link source.
- Generate mock candidate clips.
- Open Producer Mode for that project.
- Fall back to demo candidates if the API is not running.

## Stack

- Web app: Next.js
- API: FastAPI
- Worker: Python
- Database: PostgreSQL
- Queue: Redis
- Media tools: FFmpeg

## Main workflow

1. Create project.
2. Upload a file or paste a direct media link.
3. Confirm permission to process the source.
4. Import media.
5. Generate or load transcript.
6. Generate candidate clips.
7. Review in Producer Mode.
8. Apply preset and export.

## Folder layout

```text
apps/web
services/api
services/worker
packages/shared
packages/presets
infra
```

## Run the API locally

From `bpc-clipper/services/api`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

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

## Connected demo flow

1. Start the API.
2. Start the web app.
3. Open `/new-project`.
4. Enter a project name.
5. Choose `Paste a link`.
6. Add a direct media URL.
7. Confirm permission.
8. Submit.
9. Open Producer Mode from the result.

## First MVP target
A user can create a project, add a source, see job status, view mock ranked candidates, and understand the path toward rendering real clips.

## Next engineering targets
- Add real file upload endpoint.
- Persist projects and candidates in PostgreSQL.
- Replace in-memory mock data.
- Add FFprobe media validation.
- Add direct URL media import.
- Add transcript adapter.
- Add real candidate segmentation.
- Add export/render endpoint.