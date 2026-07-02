from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional
from uuid import uuid4

app = FastAPI(title="BPC Clipper API", version="0.1.0")


class ProjectCreate(BaseModel):
    name: str
    source_type: Literal["upload", "link", "unknown"] = "unknown"
    rights_confirmed: bool


class LinkSourceCreate(BaseModel):
    url: HttpUrl
    rights_confirmed: bool


PROJECTS = {}
JOBS = {}
CANDIDATES = {}


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "bpc-clipper-api"}


@app.post("/api/v1/projects")
def create_project(payload: ProjectCreate):
    project_id = str(uuid4())
    project = {
        "project_id": project_id,
        "name": payload.name,
        "source_type": payload.source_type,
        "rights_confirmed": payload.rights_confirmed,
        "status": "created",
    }
    PROJECTS[project_id] = project
    return project


@app.get("/api/v1/projects/{project_id}")
def get_project(project_id: str):
    return PROJECTS.get(project_id, {"error": "project_not_found"})


@app.post("/api/v1/projects/{project_id}/sources/link")
def create_link_source(project_id: str, payload: LinkSourceCreate):
    if not payload.rights_confirmed:
        return {"error": "rights_confirmation_required"}

    job_id = str(uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "project_id": project_id,
        "stage": "queued",
        "progress": 0,
        "message": "Link source queued for import",
        "status": "queued",
        "source_url": str(payload.url),
    }
    return {"project_id": project_id, "job_id": job_id, "status": "queued"}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    return JOBS.get(job_id, {"error": "job_not_found"})


@app.post("/api/v1/projects/{project_id}/candidates/generate")
def generate_candidates(project_id: str):
    candidates = [
        {
            "candidate_id": str(uuid4()),
            "project_id": project_id,
            "start_seconds": 120,
            "end_seconds": 164,
            "title": "Strong opening debate moment",
            "excerpt": "Mock transcript excerpt for the first recommended clip.",
            "score": 88,
            "category": "debate_heat",
            "explanation": "Strong hook, clear contrast, and a clean payoff.",
            "risk_flags": [],
        },
        {
            "candidate_id": str(uuid4()),
            "project_id": project_id,
            "start_seconds": 442,
            "end_seconds": 489,
            "title": "Story mode clip",
            "excerpt": "Mock transcript excerpt for a storytelling moment.",
            "score": 81,
            "category": "story_mode",
            "explanation": "Good narrative setup and emotional clarity.",
            "risk_flags": [],
        },
    ]
    CANDIDATES[project_id] = candidates
    return {"project_id": project_id, "candidates": candidates}


@app.get("/api/v1/projects/{project_id}/candidates")
def list_candidates(project_id: str):
    return {"project_id": project_id, "candidates": CANDIDATES.get(project_id, [])}


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
