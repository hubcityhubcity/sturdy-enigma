"""One-click automatic GameSense analysis for local stream sources."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from gamesense_audio import analyze_audio_spikes
from gamesense_visual import analyze_visual_scene_changes
from models import GameSenseEvent, Source


router = APIRouter(tags=["gamesense"])


class StreamAnalysisRequest(BaseModel):
    replace_existing: bool = True
    visual_threshold: float = Field(default=0.30, ge=0.05, le=0.95)


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


def delete_automatic_events(db: Session, source_id: str) -> None:
    events = db.query(GameSenseEvent).filter(
        GameSenseEvent.source_id == source_id,
        GameSenseEvent.event_type.in_(["audio_spike", "scene_change"]),
        GameSenseEvent.modality.in_(["audio", "visual"]),
    ).all()
    for event in events:
        db.delete(event)
    db.flush()


@router.post("/sources/{source_id}/gamesense/analyze")
def analyze_gamesense_stream(source_id: str, payload: StreamAnalysisRequest, db: Session = Depends(get_db)):
    """Run automatic audio + visual stream analysis and persist both evidence types."""
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    if not source.storage_path:
        raise HTTPException(status_code=400, detail="source_media_not_available")

    if payload.replace_existing:
        delete_automatic_events(db, source.id)

    try:
        audio_spikes = analyze_audio_spikes(source.storage_path)
        visual_changes = analyze_visual_scene_changes(source.storage_path, threshold=payload.visual_threshold)
    except FileNotFoundError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=422, detail={"stream_analysis_failed": str(error)}) from error

    created: list[GameSenseEvent] = []
    for spike in audio_spikes:
        event = GameSenseEvent(
            id=str(uuid4()), project_id=source.project_id, source_id=source.id,
            event_type="audio_spike", modality="audio",
            start_seconds=spike.start_seconds, end_seconds=spike.end_seconds,
            confidence=spike.confidence, intensity=spike.intensity,
            evidence={
                "detector": "ffmpeg_astats_audio_spike_v1",
                "peak_rms_db": spike.peak_db,
                "baseline_rms_db": spike.baseline_db,
                "analysis_run": "gamesense_stream_v1",
            },
        )
        db.add(event)
        created.append(event)

    for change in visual_changes:
        event = GameSenseEvent(
            id=str(uuid4()), project_id=source.project_id, source_id=source.id,
            event_type="scene_change", modality="visual",
            start_seconds=change.start_seconds, end_seconds=change.end_seconds,
            confidence=change.confidence, intensity=change.intensity,
            evidence={
                "detector": "ffmpeg_scene_change_v1",
                "scene_threshold": change.threshold,
                "analysis_run": "gamesense_stream_v1",
            },
        )
        db.add(event)
        created.append(event)

    db.commit()
    for event in created:
        db.refresh(event)

    audio_events = [event for event in created if event.modality == "audio"]
    visual_events = [event for event in created if event.modality == "visual"]
    return {
        "source_id": source.id,
        "project_id": source.project_id,
        "detector": "gamesense_stream_v1",
        "created_count": len(created),
        "summary": {
            "audio_spike_count": len(audio_events),
            "visual_scene_change_count": len(visual_events),
            "visual_threshold": payload.visual_threshold,
        },
        "events": [serialize_event(event) for event in created],
    }
