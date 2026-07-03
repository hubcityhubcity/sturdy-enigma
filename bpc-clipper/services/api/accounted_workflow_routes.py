from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from database import get_db
from link_importer import import_direct_media_url
from local_storage import save_uploaded_file
from media_probe import probe_media
from models import EditTimeline, ExportRecord, Job, Project, Source
from render_scaffold import create_placeholder_export_files
from workspace_billing import claim_project, enforce_export_quota, enforce_source_quota, require_project
from workspace_routes import current_workspace

router = APIRouter(tags=["workspace-workflow"])


class AccountProjectCreate(BaseModel):
    name: str
    source_type: str = "unknown"
    rights_confirmed: bool


class AccountLinkSourceCreate(BaseModel):
    url: HttpUrl
    rights_confirmed: bool
    title: str | None = None


class AccountExportCreate(BaseModel):
    format: str = "vertical_1080x1920"
    include_burned_captions: bool = True
    include_srt: bool = True
    include_vtt: bool = True
    include_metadata: bool = True


def serialize_project(project: Project) -> dict:
    return {"project_id": project.id, "name": project.name, "source_type": project.source_type, "rights_confirmed": project.rights_confirmed, "status": project.status}


def serialize_source(source: Source) -> dict:
    return {"source_id": source.id, "project_id": source.project_id, "source_type": source.source_type, "original_filename": source.original_filename, "original_url": source.original_url, "title": source.title, "storage_path": source.storage_path, "duration_seconds": source.duration_seconds, "width": source.width, "height": source.height, "fps": source.fps, "video_codec": source.video_codec, "audio_codec": source.audio_codec, "validation_status": source.validation_status, "validation_message": source.validation_message, "rights_confirmed": source.rights_confirmed}


def serialize_export(export: ExportRecord) -> dict:
    return {"export_id": export.id, "project_id": export.project_id, "edit_timeline_id": export.edit_timeline_id, "status": export.status, "format": export.format, "include_burned_captions": export.include_burned_captions, "include_srt": export.include_srt, "include_vtt": export.include_vtt, "include_metadata": export.include_metadata, "video_path": export.video_path, "srt_path": export.srt_path, "vtt_path": export.vtt_path, "metadata_path": export.metadata_path, "download_urls": {"video": f"/api/v1/exports/{export.id}/files/video" if export.video_path else None, "srt": f"/api/v1/exports/{export.id}/files/srt" if export.srt_path else None, "vtt": f"/api/v1/exports/{export.id}/files/vtt" if export.vtt_path else None, "metadata": f"/api/v1/exports/{export.id}/files/metadata" if export.metadata_path else None}, "error": export.error_message}


def create_source_job(project_id: str, source: Source, status: str) -> Job:
    ready = status == "queued"
    return Job(id=str(uuid4()), project_id=project_id, source_id=source.id, stage="queued" if ready else "probing_media", progress=0 if ready else 25, message="Source queued for processing" if ready else (source.validation_message or "Source needs attention"), status=status, source_url=source.original_url)


@router.post("/workspace/projects")
def create_workspace_project(payload: AccountProjectCreate, workspace=Depends(current_workspace), db: Session = Depends(get_db)):
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")
    project = Project(id=str(uuid4()), name=payload.name[:255] or "Untitled Titan Clipper Project", source_type=payload.source_type, rights_confirmed=True, status="created")
    db.add(project)
    db.flush()
    claim_project(db, workspace, project.id)
    db.commit()
    db.refresh(project)
    return serialize_project(project)


@router.post("/workspace/projects/{project_id}/sources/upload")
async def create_workspace_upload_source(project_id: str, rights_confirmed: bool = Form(...), file: UploadFile = File(...), workspace=Depends(current_workspace), db: Session = Depends(get_db)):
    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")
    require_project(db, workspace, project_id)
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    saved_path = await save_uploaded_file(project_id, file)
    probe = probe_media(str(saved_path))
    enforce_source_quota(db, workspace, probe.duration_seconds)
    source = Source(id=str(uuid4()), project_id=project_id, source_type="upload", original_filename=file.filename, title=file.filename, storage_path=str(saved_path), duration_seconds=probe.duration_seconds, width=probe.width, height=probe.height, fps=probe.fps, video_codec=probe.video_codec, audio_codec=probe.audio_codec, validation_status=probe.validation_status, validation_message=probe.validation_message, rights_confirmed=True)
    db.add(source)
    db.flush()
    job = create_source_job(project_id, source, "queued" if probe.validation_status == "valid" else "needs_attention")
    project.source_type = "upload"
    db.add(job)
    db.commit()
    db.refresh(source)
    db.refresh(job)
    return {"project_id": project_id, "source": serialize_source(source), "job_id": job.id, "status": job.status}


@router.post("/workspace/projects/{project_id}/sources/link")
def create_workspace_link_source(project_id: str, payload: AccountLinkSourceCreate, workspace=Depends(current_workspace), db: Session = Depends(get_db)):
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")
    require_project(db, workspace, project_id)
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    downloaded_path, import_status, import_message = import_direct_media_url(project_id, str(payload.url))
    probe = probe_media(str(downloaded_path)) if downloaded_path else None
    enforce_source_quota(db, workspace, probe.duration_seconds if probe else None)
    source = Source(id=str(uuid4()), project_id=project_id, source_type="link", original_url=str(payload.url), title=payload.title, storage_path=str(downloaded_path) if downloaded_path else None, duration_seconds=probe.duration_seconds if probe else None, width=probe.width if probe else None, height=probe.height if probe else None, fps=probe.fps if probe else None, video_codec=probe.video_codec if probe else None, audio_codec=probe.audio_codec if probe else None, validation_status=probe.validation_status if probe else import_status, validation_message=probe.validation_message if probe else import_message, rights_confirmed=True)
    db.add(source)
    db.flush()
    job = create_source_job(project_id, source, "queued" if source.validation_status == "valid" else "needs_attention")
    project.source_type = "link"
    db.add(job)
    db.commit()
    db.refresh(source)
    db.refresh(job)
    return {"project_id": project_id, "source": serialize_source(source), "job_id": job.id, "status": job.status}


@router.post("/workspace/edits/{edit_id}/exports")
def create_workspace_export(edit_id: str, payload: AccountExportCreate, workspace=Depends(current_workspace), db: Session = Depends(get_db)):
    edit = db.get(EditTimeline, edit_id)
    if edit is None:
        raise HTTPException(status_code=404, detail="edit_not_found")
    require_project(db, workspace, edit.project_id)
    enforce_export_quota(db, workspace)
    export = ExportRecord(id=str(uuid4()), project_id=edit.project_id, edit_timeline_id=edit.id, status="queued", format=payload.format, include_burned_captions=payload.include_burned_captions, include_srt=payload.include_srt, include_vtt=payload.include_vtt, include_metadata=payload.include_metadata)
    db.add(export)
    db.flush()
    try:
        paths = create_placeholder_export_files(export, edit)
        export.video_path = paths["video_path"]
        export.srt_path = paths["srt_path"]
        export.vtt_path = paths["vtt_path"]
        export.metadata_path = paths["metadata_path"]
        export.status = "placeholder_complete"
        edit.status = "export_placeholder_complete"
    except Exception as error:
        export.status = "failed"
        export.error_message = str(error)
        edit.status = "export_failed"
    db.commit()
    db.refresh(export)
    return serialize_export(export)
