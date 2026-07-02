import time

from database import SessionLocal
from models import EditTimeline, ExportRecord, Job
from render_service import render_export_with_best_source


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

        export_id = (job.source_url or "").replace("export:", "", 1)
        export = db.get(ExportRecord, export_id)
        if export is None:
            job.status = "failed"
            job.error_message = "export_not_found"
            db.commit()
            return True

        edit = db.get(EditTimeline, export.edit_timeline_id)
        if edit is None:
            job.status = "failed"
            job.error_message = "edit_not_found"
            export.status = "failed"
            export.error_message = "edit_not_found"
            db.commit()
            return True

        job.status = "running"
        job.progress = 10
        job.message = "Rendering export"
        export.status = "rendering"
        edit.status = "rendering"
        db.commit()

        try:
            paths = render_export_with_best_source(db, export, edit)
            export.video_path = paths["video_path"]
            export.srt_path = paths["srt_path"]
            export.vtt_path = paths["vtt_path"]
            export.metadata_path = paths["metadata_path"]
            export.status = "render_complete" if str(export.video_path).endswith(".mp4") else "placeholder_complete"
            edit.status = "render_complete" if export.status == "render_complete" else "export_placeholder_complete"
            job.status = "complete"
            job.progress = 100
            job.message = "Render complete"
        except Exception as error:
            export.status = "failed"
            export.error_message = str(error)
            edit.status = "export_failed"
            job.status = "failed"
            job.error_message = str(error)
            job.message = "Render failed"
        db.commit()
        return True
    finally:
        db.close()


def run_worker_loop(poll_seconds: float = 2.0) -> None:
    print("BPC render worker started")
    while True:
        did_work = process_one_render_job()
        if not did_work:
            time.sleep(poll_seconds)


if __name__ == "__main__":
    run_worker_loop()
