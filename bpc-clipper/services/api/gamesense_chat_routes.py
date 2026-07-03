from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from gamesense_chat import ChatMessage, detect_chat_spikes
from models import GameSenseEvent, Source


router = APIRouter(tags=["gamesense"])


class ChatMessageInput(BaseModel):
    seconds: float = Field(ge=0)
    text: str = Field(default="", max_length=2000)
    author: str | None = Field(default=None, max_length=255)


class ChatDetectionRequest(BaseModel):
    messages: list[ChatMessageInput] = Field(min_length=1, max_length=100_000)
    replace_existing: bool = False


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


@router.post("/sources/{source_id}/gamesense/detect/chat")
def detect_gamesense_chat(source_id: str, payload: ChatDetectionRequest, db: Session = Depends(get_db)):
    """Detect chat explosions from normalized, timestamped stream-chat messages."""
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    existing_query = db.query(GameSenseEvent).filter(
        GameSenseEvent.source_id == source.id,
        GameSenseEvent.event_type == "chat_spike",
        GameSenseEvent.modality == "chat",
        GameSenseEvent.evidence["detector"].as_string() == "chat_burst_v1",
    )
    existing = existing_query.order_by(GameSenseEvent.start_seconds.asc()).all()
    if existing and not payload.replace_existing:
        return {
            "source_id": source.id,
            "project_id": source.project_id,
            "detector": "chat_burst_v1",
            "created_count": 0,
            "events": [serialize_event(event) for event in existing],
            "message": "Existing automatic chat spike events returned. Send replace_existing=true to recalculate.",
        }
    if existing:
        for event in existing:
            db.delete(event)
        db.flush()

    messages = [ChatMessage(seconds=item.seconds, text=item.text, author=item.author) for item in payload.messages]
    spikes = detect_chat_spikes(messages)
    created: list[GameSenseEvent] = []
    for spike in spikes:
        event = GameSenseEvent(
            id=str(uuid4()),
            project_id=source.project_id,
            source_id=source.id,
            event_type="chat_spike",
            modality="chat",
            start_seconds=spike.start_seconds,
            end_seconds=spike.end_seconds,
            confidence=spike.confidence,
            intensity=spike.intensity,
            evidence={
                "detector": "chat_burst_v1",
                "message_count": spike.message_count,
                "messages_per_second": spike.messages_per_second,
                "baseline_messages_per_second": spike.baseline_messages_per_second,
                "hype_message_count": spike.hype_message_count,
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
        "detector": "chat_burst_v1",
        "created_count": len(created),
        "events": [serialize_event(event) for event in created],
    }
