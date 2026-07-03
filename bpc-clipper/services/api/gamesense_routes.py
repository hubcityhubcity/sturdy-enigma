from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from gamesense_engine import GameSignal, build_gamesense_moments
from models import CandidateClip, GameSenseEvent, Project, Source


router = APIRouter(tags=["gamesense"])


class GameSenseEventCreate(BaseModel):
    source_id: str | None = None
    event_type: str = Field(min_length=2, max_length=80)
    modality: str = Field(min_length=2, max_length=50)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    confidence: float = Field(default=1.0, ge=0, le=1)
    intensity: int = Field(default=50, ge=0, le=100)
    evidence: dict = Field(default_factory=dict)


class GameSenseEventBatchCreate(BaseModel):
    events: list[GameSenseEventCreate] = Field(min_length=1, max_length=5000)


def serialize_event(event: GameSenseEvent) -> dict:
    return {
        "event_id": event.id,
        "project_id": event.project_id,
        "source_id": event.source_id,
        "event_type": event.event_type,
        "modality": event.modality,
        "start_seconds": event.start_seconds,
        "end_seconds": event.end_seconds,
        "confidence": event.confidence,
        "intensity": event.intensity,
        "evidence": event.evidence or {},
    }


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


def resolve_source_id(db: Session, project_id: str, requested_source_id: str | None) -> str | None:
    if requested_source_id is not None:
        source = db.get(Source, requested_source_id)
        if source is None or source.project_id != project_id:
            raise HTTPException(status_code=400, detail="invalid_source_for_project")
        return source.id
    source = (
        db.query(Source)
        .filter(Source.project_id == project_id)
        .order_by(Source.created_at.desc())
        .first()
    )
    return source.id if source else None


@router.post("/projects/{project_id}/gamesense/events")
def ingest_gamesense_events(project_id: str, payload: GameSenseEventBatchCreate, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    created: list[GameSenseEvent] = []
    for incoming in payload.events:
        if incoming.end_seconds < incoming.start_seconds:
            raise HTTPException(status_code=422, detail="event_end_before_start")
        event = GameSenseEvent(
            id=str(uuid4()),
            project_id=project_id,
            source_id=resolve_source_id(db, project_id, incoming.source_id),
            event_type=incoming.event_type.strip().lower().replace(" ", "_"),
            modality=incoming.modality.strip().lower(),
            start_seconds=incoming.start_seconds,
            end_seconds=incoming.end_seconds,
            confidence=incoming.confidence,
            intensity=incoming.intensity,
            evidence=incoming.evidence,
        )
        db.add(event)
        created.append(event)

    db.commit()
    for event in created:
        db.refresh(event)
    return {"project_id": project_id, "created_count": len(created), "events": [serialize_event(event) for event in created]}


@router.get("/projects/{project_id}/gamesense/events")
def list_gamesense_events(project_id: str, source_id: str | None = None, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    query = db.query(GameSenseEvent).filter(GameSenseEvent.project_id == project_id)
    if source_id:
        query = query.filter(GameSenseEvent.source_id == source_id)
    events = query.order_by(GameSenseEvent.start_seconds.asc()).all()
    return {"project_id": project_id, "events": [serialize_event(event) for event in events]}


@router.post("/projects/{project_id}/gamesense/candidates/generate")
def generate_gamesense_candidates(project_id: str, source_id: str | None = None, replace_existing: bool = False, db: Session = Depends(get_db)):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    resolved_source_id = resolve_source_id(db, project_id, source_id)
    event_query = db.query(GameSenseEvent).filter(GameSenseEvent.project_id == project_id)
    if resolved_source_id:
        event_query = event_query.filter(GameSenseEvent.source_id == resolved_source_id)
    events = event_query.order_by(GameSenseEvent.start_seconds.asc()).all()
    if not events:
        raise HTTPException(status_code=404, detail="gamesense_events_not_found")

    existing_query = db.query(CandidateClip).filter(
        CandidateClip.project_id == project_id,
        CandidateClip.category.in_([
            "clutch", "victory", "jump_scare", "rage_moment", "funny_fail",
            "insane_play", "funny_reaction", "chat_loses_it", "reaction_moment", "gameplay_moment",
        ]),
    )
    if resolved_source_id:
        existing_query = existing_query.filter(CandidateClip.source_id == resolved_source_id)
    existing = existing_query.order_by(CandidateClip.score.desc()).all()
    if existing and not replace_existing:
        return {"project_id": project_id, "source_id": resolved_source_id, "generated_count": 0, "candidates": [serialize_candidate(item) for item in existing]}
    if existing and replace_existing:
        for candidate in existing:
            db.delete(candidate)
        db.flush()

    signals = [
        GameSignal(
            event_type=event.event_type,
            modality=event.modality,
            start_seconds=event.start_seconds,
            end_seconds=event.end_seconds,
            intensity=event.intensity,
            confidence=event.confidence,
            evidence=event.evidence or {},
        )
        for event in events
    ]
    moments = build_gamesense_moments(signals)
    candidates: list[CandidateClip] = []
    for moment in moments[:25]:
        evidence = [
            {
                "event_type": signal.event_type,
                "modality": signal.modality,
                "start_seconds": signal.start_seconds,
                "end_seconds": signal.end_seconds,
                "intensity": signal.intensity,
                "confidence": signal.confidence,
                "evidence": signal.evidence or {},
            }
            for signal in moment.evidence
        ]
        title = f"{moment.category.replace('_', ' ').title()} — GameSense Moment"
        candidate = CandidateClip(
            id=str(uuid4()),
            project_id=project_id,
            source_id=resolved_source_id,
            start_seconds=moment.start_seconds,
            end_seconds=moment.end_seconds,
            title=title,
            excerpt=moment.explanation,
            score=moment.score,
            category=moment.category,
            explanation=moment.explanation,
            score_breakdown={
                "engine": "gamesense_v1",
                "overall": {"name": "overall", "score": moment.score, "explanation": moment.explanation},
                "evidence_count": len(evidence),
                "evidence": evidence,
            },
            risk_flags=[],
        )
        db.add(candidate)
        candidates.append(candidate)

    db.commit()
    for candidate in candidates:
        db.refresh(candidate)
    return {
        "project_id": project_id,
        "source_id": resolved_source_id,
        "generated_count": len(candidates),
        "candidates": [serialize_candidate(item) for item in candidates],
    }
