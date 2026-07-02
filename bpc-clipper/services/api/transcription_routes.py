from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Source, Transcript, TranscriptSegment, TranscriptWord
from transcription_adapter import get_transcription_provider

router = APIRouter()


class RealTranscriptCreate(BaseModel):
    provider: str | None = None
    force: bool = False


def serialize_segment(segment: TranscriptSegment) -> dict:
    return {
        "segment_id": segment.id,
        "speaker_label": segment.speaker_label,
        "start_seconds": segment.start_seconds,
        "end_seconds": segment.end_seconds,
        "text": segment.text,
        "confidence": segment.confidence,
    }


def serialize_transcript(transcript: Transcript) -> dict:
    return {
        "transcript_id": transcript.id,
        "project_id": transcript.project_id,
        "source_id": transcript.source_id,
        "language": transcript.language,
        "provider": transcript.provider,
        "confidence": transcript.confidence,
        "segments": [serialize_segment(segment) for segment in transcript.segments],
    }


@router.post("/sources/{source_id}/transcript/real")
def generate_real_transcript(source_id: str, payload: RealTranscriptCreate | None = None, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")

    if not source.storage_path:
        raise HTTPException(status_code=400, detail="source_has_no_local_media_path")

    request = payload or RealTranscriptCreate()
    if not request.force:
        existing = (
            db.query(Transcript)
            .filter(Transcript.source_id == source.id)
            .order_by(Transcript.created_at.desc())
            .first()
        )
        if existing and not existing.provider.startswith("mock"):
            return serialize_transcript(existing)

    provider = get_transcription_provider(request.provider)
    try:
        result = provider.transcribe(Path(source.storage_path))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    transcript = Transcript(
        id=str(uuid4()),
        project_id=source.project_id,
        source_id=source.id,
        language=result.language,
        provider=result.provider,
        confidence=result.confidence,
    )
    db.add(transcript)
    db.flush()

    for result_segment in result.segments:
        segment = TranscriptSegment(
            id=str(uuid4()),
            transcript_id=transcript.id,
            speaker_label=result_segment.speaker_label,
            start_seconds=result_segment.start_seconds,
            end_seconds=result_segment.end_seconds,
            text=result_segment.text,
            confidence=result_segment.confidence,
        )
        db.add(segment)
        db.flush()
        for word in result_segment.words or []:
            db.add(
                TranscriptWord(
                    id=str(uuid4()),
                    segment_id=segment.id,
                    start_seconds=word.start_seconds,
                    end_seconds=word.end_seconds,
                    text=word.text,
                    confidence=word.confidence,
                )
            )

    db.commit()
    db.refresh(transcript)
    return serialize_transcript(transcript)
