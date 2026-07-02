# Persistence Notes

## What changed

The FastAPI backend now uses SQLAlchemy instead of in-memory dictionaries.

Added files:
- `services/api/database.py`
- `services/api/models.py`

Updated files:
- `services/api/main.py`
- `services/api/requirements.txt`

## Current persisted entities

- Project
- Job
- CandidateClip

## Current behavior

- `POST /api/v1/projects` writes a project to the database.
- `GET /api/v1/projects/{project_id}` reads a project from the database.
- `POST /api/v1/projects/{project_id}/sources/link` writes a job to the database.
- `GET /api/v1/jobs/{job_id}` reads job status from the database.
- `POST /api/v1/projects/{project_id}/candidates/generate` creates mock candidates once, then reuses existing persisted candidates.
- `GET /api/v1/projects/{project_id}/candidates` reads candidates ordered by score.

## Development database

The API uses `DATABASE_URL` when provided.

If `DATABASE_URL` is not set, the API falls back to local SQLite:

```text
sqlite:///./bpc_clipper.db
```

This keeps the MVP easy to run without PostgreSQL.

## Next backend targets

1. Add Alembic migrations.
2. Add source table.
3. Add upload endpoint.
4. Add FFprobe metadata validation.
5. Add direct link media import.
6. Add transcript table and mock transcript adapter.
7. Replace mock candidates with transcript-based segmentation.
8. Add tests for project, job, and candidate endpoints.
