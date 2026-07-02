from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import EditTimeline, ExportRecord, Job
from render_queue import enqueue_render_job, serialize_render_job

router = APIRouter()


@router.post("/exports/{export_id}/queue-render")
def queue_export_render(export_id: str, db: Session = Depends(get_db)):
    export = db.get(ExportRecord, export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="export_not_found")

    edit = db.get(EditTimeline, export.edit_timeline_id)
    if edit is None:
        raise HTTPException(status_code=404, detail="edit_not_found")

    existing = (
        db.query(Job)
        .filter(Job.stage == "render_export", Job.source_url == f"export:{export.id}", Job.status.in_(["queued", "running"]))
        .first()
    )
    if existing:
        return serialize_render_job(existing)

    job = enqueue_render_job(db, export, edit)
    return serialize_render_job(job)


@router.get("/render-jobs/{job_id}")
def get_render_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None or job.stage != "render_export":
        raise HTTPException(status_code=404, detail="render_job_not_found")
    return serialize_render_job(job)
