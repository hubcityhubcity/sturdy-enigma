from sqlalchemy.orm import Session

from models import CandidateClip, EditTimeline, ExportRecord, Source
from render_scaffold import render_trimmed_mp4


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

    return render_trimmed_mp4(export, edit, source)
