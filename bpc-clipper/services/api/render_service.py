from sqlalchemy.orm import Session

from models import CandidateClip, EditTimeline, ExportRecord, Source, Transcript, TranscriptSegment, TranscriptWord
from render_scaffold import render_trimmed_mp4


def caption_words_for_edit(db: Session, edit: EditTimeline, source: Source | None) -> list[dict]:
    """Return timestamped transcript words inside the edit window.

    Timestamps remain source-relative here. The renderer converts them to clip-relative
    times because FFmpeg trims the source at ``edit.start_seconds``.
    """
    if source is None:
        return []

    transcript = (
        db.query(Transcript)
        .filter(Transcript.source_id == source.id)
        .order_by(Transcript.created_at.desc())
        .first()
    )
    if transcript is None:
        return []

    rows = (
        db.query(TranscriptWord)
        .join(TranscriptSegment, TranscriptWord.segment_id == TranscriptSegment.id)
        .filter(TranscriptSegment.transcript_id == transcript.id)
        .filter(TranscriptWord.end_seconds > edit.start_seconds)
        .filter(TranscriptWord.start_seconds < edit.end_seconds)
        .order_by(TranscriptWord.start_seconds.asc())
        .all()
    )

    return [
        {
            "start_seconds": word.start_seconds,
            "end_seconds": word.end_seconds,
            "text": word.corrected_text or word.text,
        }
        for word in rows
    ]


def render_export_with_best_source(db: Session, export: ExportRecord, edit: EditTimeline) -> dict:
    """Render an export using the candidate-linked source when available.

    Older rows may not have candidate.source_id yet, so the newest project source remains
    a safe fallback during local development.
    """
    candidate = db.get(CandidateClip, edit.candidate_clip_id)
    source = None

    if candidate and candidate.source_id:
        source = db.get(Source, candidate.source_id)

    if source is None:
        source = (
            db.query(Source)
            .filter(Source.project_id == edit.project_id)
            .order_by(Source.created_at.desc())
            .first()
        )

    return render_trimmed_mp4(
        export,
        edit,
        source,
        caption_words=caption_words_for_edit(db, edit, source),
    )
