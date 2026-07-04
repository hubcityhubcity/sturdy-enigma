"""Persistent worker for queued Titan Clipper render jobs.

Run this as a separate process from the API:
    python render_worker.py

Deploy one replica until the queue claim is upgraded for distributed multi-worker
locking. The API and worker must share both DATABASE_URL and STORAGE_ROOT.
"""

from __future__ import annotations

import os
import signal
import time
from datetime import datetime

from database import SessionLocal, create_db_and_tables
from models import EditTimeline, ExportRecord, Job
from render_service import render_export_with_best_source


_should_stop = False


def export_id_for(job: Job) -> str | None:
    source_url = job.source_url or ""
    return source_url.removeprefix("export:") if source_url.startswith("export:") else None


def process_one_render_job() -> bool:
    db = SessionLocal()
    try:
        job = (
            db.query(Job)
            .filter(Job.stage == "render_export", Job.status == "queued")
            .order_by(Job.created_at.asc())
            .first()
        )
        if job is None:
            return False

        job.status = "running"
        job.progress = max(job.progress, 10)
        job.message = "Render worker claimed job"
        job.updated_at = datetime.utcnow()
        db.commit()

        export_id = export_id_for(job)
        export = db.get(ExportRecord, export_id) if export_id else None
        if export is None:
            job.status = "failed"
            job.progress = 100
            job.message = "Render job could not resolve its export"
            job.error_message = "export_not_found"
            job.updated_at = datetime.utcnow()
            db.commit()
            return True

        edit = db.get(EditTimeline, export.edit_timeline_id)
        if edit is None:
            job.status = "failed"
            job.progress = 100
            job.message = "Render job could not resolve its edit"
            job.error_message = "edit_not_found"
            job.updated_at = datetime.utcnow()
            export.status = "failed"
            export.error_message = "edit_not_found"
            db.commit()
            return True

        export.status = "rendering"
        edit.status = "rendering"
        job.progress = 20
        job.message = "Rendering export with FFmpeg"
        job.updated_at = datetime.utcnow()
        db.commit()

        try:
            paths = render_export_with_best_source(db, export, edit)
            export.video_path = paths["video_path"]
            export.srt_path = paths["srt_path"]
            export.vtt_path = paths["vtt_path"]
            export.metadata_path = paths["metadata_path"]
            export.status = "render_complete" if str(export.video_path).endswith(".mp4") else "placeholder_complete"
            export.completed_at = datetime.utcnow()
            edit.status = "render_complete" if export.status == "render_complete" else "export_placeholder_complete"
            job.status = "complete"
            job.progress = 100
            job.message = "Render complete" if export.status == "render_complete" else "Render completed with placeholder output"
            job.error_message = None
        except Exception as error:
            export.status = "failed"
            export.error_message = str(error)
            edit.status = "export_failed"
            job.status = "failed"
            job.progress = 100
            job.error_message = str(error)
            job.message = "Render failed"
        finally:
            job.updated_at = datetime.utcnow()
            db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def handle_shutdown(*_args: object) -> None:
    global _should_stop
    _should_stop = True


def run_worker_loop(poll_seconds: float | None = None) -> None:
    global _should_stop
    _should_stop = False
    resolved_poll_seconds = poll_seconds if poll_seconds is not None else float(os.getenv("RENDER_WORKER_POLL_SECONDS", "2"))
    resolved_poll_seconds = max(0.5, resolved_poll_seconds)
    create_db_and_tables()
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    print(f"Titan render worker started; polling every {resolved_poll_seconds:g} second(s).", flush=True)

    while not _should_stop:
        try:
            did_work = process_one_render_job()
            if not did_work:
                time.sleep(resolved_poll_seconds)
        except Exception as error:
            print(f"Render worker loop error: {error}", flush=True)
            time.sleep(resolved_poll_seconds)

    print("Titan render worker stopped.", flush=True)


if __name__ == "__main__":
    run_worker_loop()
