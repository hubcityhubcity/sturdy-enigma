from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import CandidateClip, Transcript, TranscriptSegment
from scoring_engine import score_segment

router = APIRouter()


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


def find_matching_segment(db: Session, candidate: CandidateClip) -> TranscriptSegment | None:
    transcript = (
        db.query(Transcript)
        .filter(Transcript.project_id == candidate.project_id, Transcript.source_id == candidate.source_id)
        .order_by(Transcript.created_at.desc())
        .first()
    )
    if transcript is None:
        return None

    return (
        db.query(TranscriptSegment)
        .filter(
            TranscriptSegment.transcript_id == transcript.id,
            TranscriptSegment.start_seconds == candidate.start_seconds,
            TranscriptSegment.end_seconds == candidate.end_seconds,
        )
        .first()
    )


def category_from_breakdown(breakdown: dict) -> str:
    debate = breakdown.get("debate", {}).get("score", 0)
    story = breakdown.get("story", {}).get("score", 0)
    emotion = breakdown.get("emotion", {}).get("score", 0)
    if debate >= 70:
        return "debate_heat"
    if emotion >= 70:
        return "emotional_moment"
    if story >= 70:
        return "story_mode"
    return "high_retention"


@router.post("/projects/{project_id}/candidates/rescore")
def rescore_project_candidates(project_id: str, db: Session = Depends(get_db)):
    candidates = db.query(CandidateClip).filter(CandidateClip.project_id == project_id).all()
    if not candidates:
        raise HTTPException(status_code=404, detail="candidates_not_found")

    updated = []
    for candidate in candidates:
        segment = find_matching_segment(db, candidate)
        if segment is None:
            continue
        score = score_segment(segment)
        breakdown = score.as_dict()
        candidate.score = breakdown["overall"]["score"]
        candidate.score_breakdown = breakdown
        candidate.category = category_from_breakdown(breakdown)
        candidate.explanation = breakdown["overall"]["explanation"]
        updated.append(candidate)

    db.commit()
    for candidate in updated:
        db.refresh(candidate)

    return {
        "project_id": project_id,
        "updated_count": len(updated),
        "candidates": [serialize_candidate(candidate) for candidate in sorted(updated, key=lambda item: item.score, reverse=True)],
    }
