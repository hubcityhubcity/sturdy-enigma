# Build Steps

## Step 1: Repo foundation
Create the monorepo structure:

- apps/web
- services/api
- services/worker
- packages/shared
- packages/presets
- infra
- docs

## Step 2: Local development stack
Add Docker Compose with:

- PostgreSQL
- Redis
- API service
- worker service
- web service

## Step 3: API foundation
Build:

- health endpoint
- project creation endpoint
- source creation endpoint
- job status endpoint
- candidate list endpoint
- preset list endpoint

## Step 4: Web dashboard shell
Build screens:

- Home dashboard
- New project
- Upload or paste link
- Job progress
- Producer Mode
- Clip editor placeholder
- Export history

## Step 5: Source ingest MVP
Build:

- local upload handler
- direct link handler
- media validation
- source metadata extraction
- storage path creation

## Step 6: Transcript MVP
Build:

- mock transcript adapter first
- transcript data model
- transcript viewer
- transcript correction interface later

## Step 7: Candidate generator
Build:

- segmentation from transcript timing
- duration filters
- overlap removal
- score calculation
- explanation generation
- category assignment

## Step 8: Producer Mode
Build:

- ranked candidate list
- score breakdown display
- transcript excerpt
- source timecodes
- candidate categories
- approve or reject controls

## Step 9: Edit timeline MVP
Build:

- trim start and end
- hook text
- caption preset
- crop mode
- export settings

## Step 10: Render MVP
Build:

- FFmpeg trim render
- vertical output setting
- burned caption placeholder
- SRT and VTT export
- metadata JSON export

## Step 11: Analytics MVP
Build manual metric entry for exports.

## Step 12: Learning engine
Use performance metrics to improve ranking suggestions over time.

## Definition of done for first MVP
A user can create a project, upload or link a source, process a mock transcript, see ranked clip candidates, select one, apply a preset, and export a publishing pack placeholder.