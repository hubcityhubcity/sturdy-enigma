from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from typing import Literal
from uuid import uuid4

from database import create_db_and_tables, get_db
from link_importer import import_direct_media_url
from local_storage import save_uploaded_file
from media_probe import probe_media
from models import CandidateClip, Job, Project, Source


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="BPC Clipper API", version="0.5.0", lifespan=lifespan)


class ProjectCreate(BaseModel):
    name: str
    source_type: Literal["upload", "link", "unknown"] = "unknown"
    rights_confirmed: bool


class LinkSourceCreate(BaseModel):
    url: HttpUrl
    rights_confirmed: bool
    title: str | None = None


def serialize_project(project: Project) -> dict:
    return {
        "project_id": project.id,
        "name": project.name,
        "source_type": project.source_type,
        "rights_confirmed": project.rights_confirmed,
        "status": project.status,
    }


def serialize_source(source: Source) -> dict:
    return {
        "source_id": source.id,
        "project_id": source.project_id,
        "source_type": source.source_type,
        "original_filename": source.original_filename,
        "original_url": source.original_url,
        "title": source.title,
        "storage_path": source.storage_path,
        "duration_seconds": source.duration_seconds,
        "width": source.width,
        "height": source.height,
        "fps": source.fps,
        "video_codec": source.video_codec,
        "audio_codec": source.audio_codec,
        "validation_status": source.validation_status,
        "validation_message": source.validation_message,
        "rights_confirmed": source.rights_confirmed,
    }


def serialize_job(job: Job) -> dict:
    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "source_id": job.source_id,
        "stage": job.stage,
        "progress": job.progress,
        "message": job.message,
        "status": job.status,
        "source_url": job.source_url,
        "error": job.error_message,
    }


def serialize_candidate(candidate: CandidateClip) -> dict:
    return {
        "candidate_id": candidate.id,
        "project_id": candidate.project_id,
        "start_seconds": candidate.start_seconds,
        "end_seconds": candidate.end_seconds,
        "title": candidate.title,
        "excerpt": candidate.excerpt,
        "score": candidate.score,
        "category": candidate.category,
        "explanation": candidate.explanation,
        "risk_flags": candidate.risk_flags or [],
    }


def make_job_for_source(project_id: str, source: Source, message: str, status: str = "queued") -> Job:
    return Job(
        id=str(uuid4()),
        project_id=project_id,
        source_id=source.id,
        stage="queued" if status == "queued" else "importing_source",
        progress=0 if status == "queued" else 30,
        message=message,
        status=status,
        source_url=source.original_url,
    )


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "bpc-clipper-api", "persistence": "database"}


@app.post("/api/v1/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        id=str(uuid4()),
        name=payload.name,
        source_type=payload.source_type,
        rights_confirmed=payload.rights_confirmed,
        status="created",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize_project(project)


@app.get("/api/v1/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    return serialize_project(project)


@app.get("/api/v1/projects/{project_id}/sources")
def list_sources(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    sources = db.query(Source).filter(Source.project_id == project_id).all()
    return {"project_id": project_id, "sources": [serialize_source(source) for source in sources]}


@app.post("/api/v1/projects/{project_id}/sources/upload")
async def create_upload_source(
    project_id: str,
    rights_confirmed: bool = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    saved_path = await save_uploaded_file(project_id, file)
    probe = probe_media(str(saved_path))

    source = Source(
        id=str(uuid4()),
        project_id=project_id,
        source_type="upload",
        original_filename=file.filename,
        title=file.filename,
        storage_path=str(saved_path),
        duration_seconds=probe.duration_seconds,
        width=probe.width,
        height=probe.height,
        fps=probe.fps,
        video_codec=probe.video_codec,
        audio_codec=probe.audio_codec,
        validation_status=probe.validation_status,
        validation_message=probe.validation_message,
        rights_confirmed=rights_confirmed,
    )
    db.add(source)
    db.flush()

    job = Job(
        id=str(uuid4()),
        project_id=project_id,
        source_id=source.id,
        stage="probing_media" if probe.validation_status != "valid" else "queued",
        progress=25 if probe.validation_status != "valid" else 0,
        message=probe.validation_message if probe.validation_status != "valid" else "Upload source queued for processing",
        status="needs_attention" if probe.validation_status != "valid" else "queued",
    )
    project.source_type = "upload"
    db.add(job)
    db.commit()
    db.refresh(source)
    db.refresh(job)

    return {
        "project_id": project_id,
        "source": serialize_source(source),
        "job_id": job.id,
        "status": job.status,
    }


@app.post("/api/v1/projects/{project_id}/sources/link")
def create_link_source(project_id: str, payload: LinkSourceCreate, db: Session = Depends(get_db)):
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    downloaded_path, import_status, import_message = import_direct_media_url(project_id, str(payload.url))
    probe = probe_media(str(downloaded_path)) if downloaded_path else None

    source = Source(
        id=str(uuid4()),
        project_id=project_id,
        source_type="link",
        original_url=str(payload.url),
        title=payload.title,
        storage_path=str(downloaded_path) if downloaded_path else None,
        duration_seconds=probe.duration_seconds if probe else None,
        width=probe.width if probe else None,
        height=probe.height if probe else None,
        fps=probe.fps if probe else None,
        video_codec=probe.video_codec if probe else None,
        audio_codec=probe.audio_codec if probe else None,
        validation_status=probe.validation_status if probe else import_status,
        validation_message=probe.validation_message if probe else import_message,
        rights_confirmed=payload.rights_confirmed,
    )
    db.add(source)
    db.flush()

    source_is_ready = source.validation_status == "valid"
    job = make_job_for_source(
        project_id=project_id,
        source=source,
        message="Direct link imported and queued for processing" if source_is_ready else source.validation_message,
        status="queued" if source_is_ready else "needs_attention",
    )
    project.source_type = "link"
    db.add(job)
    db.commit()
    db.refresh(source)
    db.refresh(job)
    return {
        "project_id": project_id,
        "source": serialize_source(source),
        "job_id": job.id,
        "status": job.status,
    }


@app.get("/api/v1/sources/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    return serialize_source(source)


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return serialize_job(job)


@app.post("/api/v1/projects/{project_id}/candidates/generate")
def generate_candidates(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    existing = db.query(CandidateClip).filter(CandidateClip.project_id == project_id).all()
    if existing:
        return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in existing]}

    candidates = [
        CandidateClip(
            id=str(uuid4()),
            project_id=project_id,
            start_seconds=120,
            end_seconds=164,
            title="Strong opening debate moment",
            excerpt="Mock transcript excerpt for the first recommended clip.",
            score=88,
            category="debate_heat",
            explanation="Strong hook, clear contrast, and a clean payoff.",
            risk_flags=[],
        ),
        CandidateClip(
            id=str(uuid4()),
            project_id=project_id,
            start_seconds=442,
            end_seconds=489,
            title="Story mode clip",
            excerpt="Mock transcript excerpt for a storytelling moment.",
            score=81,
            category="story_mode",
            explanation="Good narrative setup and emotional clarity.",
            risk_flags=[],
        ),
    ]
    db.add_all(candidates)
    db.commit()
    for candidate in candidates:
        db.refresh(candidate)

    return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in candidates]}


@app.get("/api/v1/projects/{project_id}/candidates")
def list_candidates(project_id: str, db: Session = Depends(get_db)):
    candidates = (
        db.query(CandidateClip)
        .filter(CandidateClip.project_id == project_id)
        .order_by(CandidateClip.score.desc())
        .all()
    )
    return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in candidates]}


@app.get("/api/v1/presets")
def list_presets():
    return {
        "presets": [
            {"name": "BPC Clean Editorial", "pace": "balanced"},
            {"name": "BPC Debate Heat", "pace": "quick"},
            {"name": "BPC Story Mode", "pace": "smooth"},
            {"name": "BPC Commentary Reaction", "pace": "flexible"},
        ]
    }
