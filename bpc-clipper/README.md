# BPC Clipper

Black Podcast Clips AI Clipper is a local-first application for turning long-form podcast content into ranked short-form clip candidates.

## Current milestone
Foundation scaffold.

## Planned local stack

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

## First MVP target
A user can create a project, add a source, see job status, view mock ranked candidates, and understand the path toward rendering real clips.