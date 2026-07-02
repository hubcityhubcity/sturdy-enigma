from sqlalchemy.orm import Session

from models import EditTimeline, ExportRecord, Source
from render_scaffold import render_trimmed_mp4


def render_export_with_best_source(db: Session, export: ExportRecord, edit: EditTimeline) -> dict:
    """Render an export using the newest source for the project.

    Later versions should link candidates directly to source_id. For now, this keeps the
    pipeline moving with the current data model.
    """
    source = (
        db.query(Source)
        .filter(Source.project_id == edit.project_id)
        .order_by(Source.created_at.desc())
        .first()
    )
    return render_trimmed_mp4(export, edit, source)
