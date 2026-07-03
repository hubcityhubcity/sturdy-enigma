from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from gamesense_visual import analyze_visual_scene_changes
from models import GameSenseEvent, Source


router = APIRouter(tags=["gamesense"])


class VisualDetectionRequest(BaseModel):
    replace_existing: bool = False
    threshold: float = Field(default=0.30, ge=0.05, le=0.95)


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


@router.post("/sources/{source_id}/gamesense/detect/visual")
def detect_gamesense_visual(source_id: str, payload: VisualDetectionRequest, db: Session = Depends(get_db)):
    """Detect sharp visual changes in a local video with FFmpeg scene scoring."""
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    if not source.storage_path:
        raise HTTPException(status_code=400, detail="source_media_not_available")

    existing = db.query(GameSenseEvent).filter(
        GameSenseEvent.source_id == source.id,
        GameSenseEvent.event_type == "scene_change",
        GameSenseEvent.modality == "visual",
    ).order_by(GameSenseEvent.start_seconds.asc()).all()
    if existing and not payload.replace_existing:
        return {
            "source_id": source.id,
            "project_id": source.project_id,
            "detector": "ffmpeg_scene_change_v1",
            "created_count": 0,
            "events": [serialize_event(event) for event in existing],
            "message": "Existing visual scene-change events returned. Send replace_existing=true to recalculate.",
        }
    if existing:
        for event in existing:
            db.delete(event)
        db.flush()

    try:
        changes = analyze_visual_scene_changes(source.storage_path, threshold=payload.threshold)
    except FileNotFoundError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=422, detail={"visual_detection_failed": str(error)}) from error

    created: list[GameSenseEvent] = []
    for change in changes:
        event = GameSenseEvent(
            id=str(uuid4()),
            project_id=source.project_id,
            source_id=source.id,
            event_type="scene_change",
            modality="visual",
            start_seconds=change.start_seconds,
            end_seconds=change.end_seconds,
            confidence=change.confidence,
            intensity=change.intensity,
            evidence={
                "detector": "ffmpeg_scene_change_v1",
                "scene_threshold": change.threshold,
            },
        )
        db.add(event)
        created.append(event)

    db.commit()
    for event in created:
        db.refresh(event)
    return {
        "source_id": source.id,
        "project_id": source.project_id,
        "detector": "ffmpeg_scene_change_v1",
        "created_count": len(created),
        "events": [serialize_event(event) for event in created],
    }
