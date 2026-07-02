from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from typing import Literal
from uuid import uuid4

from database import create_db_and_tables, get_db
from models import CandidateClip, Job, Project


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="BPC Clipper API", version="0.2.0", lifespan=lifespan)


class ProjectCreate(BaseModel):
    name: str
    source_type: Literal["upload", "link", "unknown"] = "unknown"
    rights_confirmed: bool


class LinkSourceCreate(BaseModel):
    url: HttpUrl
    rights_confirmed: bool


def serialize_project(project: Project) -> dict:
    return {
        "project_id": project.id,
        "name": project.name,
        "source_type": project.source_type,
        "rights_confirmed": project.rights_confirmed,
        "status": project.status,
    }


def serialize_job(job: Job) -> dict:
    return {
        "job_id": job.id,
        "project_id": job.project_id,
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


@app.post("/api/v1/projects/{project_id}/sources/link")
def create_link_source(project_id: str, payload: LinkSourceCreate, db: Session = Depends(get_db)):
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmation_required")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    job = Job(
        id=str(uuid4()),
        project_id=project_id,
        stage="queued",
        progress=0,
        message="Link source queued for import",
        status="queued",
        source_url=str(payload.url),
    )
    project.source_type = "link"
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"project_id": project_id, "job_id": job.id, "status": job.status}


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
