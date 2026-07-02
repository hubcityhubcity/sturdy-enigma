from uuid import uuid4

from sqlalchemy.orm import Session

from models import EditTimeline, ExportRecord, Job


def enqueue_render_job(db: Session, export: ExportRecord, edit: EditTimeline) -> Job:
    job = Job(
        id=str(uuid4()),
        project_id=export.project_id,
        source_id=None,
        stage="render_export",
        progress=0,
        message="Render export queued",
        status="queued",
        source_url=f"export:{export.id}",
    )
    export.status = "queued_for_render"
    edit.status = "queued_for_render"
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def serialize_render_job(job: Job) -> dict:
    export_id = None
    if job.source_url and job.source_url.startswith("export:"):
        export_id = job.source_url.replace("export:", "", 1)
    return {
        "job_id": job.id,
        "export_id": export_id,
        "project_id": job.project_id,
        "stage": job.stage,
        "progress": job.progress,
        "message": job.message,
        "status": job.status,
        "error": job.error_message,
    }
