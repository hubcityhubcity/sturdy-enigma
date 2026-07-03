from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import CandidateClip, Project, Source


router = APIRouter(tags=["candidates"])


def serialize_candidate(candidate: CandidateClip) -> dict:
    return {
        "candidate_id": candidate.id,
        "project_id": candidate.project_id,
        "source_id": candidate.source_id,
        "start_seconds": candidate.start_seconds,
        "end_seconds": candidate.end_seconds,
        "title": candidate.title,
        "excerpt": candidate.excerpt,
        "score": candidate.score,
        "category": candidate.category,
        "explanation": candidate.explanation,
        "score_breakdown": candidate.score_breakdown or {},
        "risk_flags": candidate.risk_flags or [],
        "status": candidate.status,
    }


@router.get("/projects/{project_id}/sources/{source_id}/candidates")
def list_source_candidates(project_id: str, source_id: str, db: Session = Depends(get_db)):
    """Return only the candidates that belong to one verified project source."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    source = db.get(Source, source_id)
    if source is None or source.project_id != project_id:
        raise HTTPException(status_code=404, detail="source_not_found")

    candidates = (
        db.query(CandidateClip)
        .filter(CandidateClip.project_id == project_id, CandidateClip.source_id == source_id)
        .order_by(CandidateClip.score.desc(), CandidateClip.start_seconds.asc())
        .all()
    )
    return {
        "project_id": project_id,
        "source_id": source_id,
        "candidates": [serialize_candidate(candidate) for candidate in candidates],
    }
