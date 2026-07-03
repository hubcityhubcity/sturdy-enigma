from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import CandidateClip, EditTimeline, ExportRecord
from publishing_package import build_publishing_package

router = APIRouter(tags=["publishing"])


@router.get("/exports/{export_id}/publishing-package")
def get_publishing_package(export_id: str, db: Session = Depends(get_db)):
    export = db.get(ExportRecord, export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="export_not_found")
    edit = db.get(EditTimeline, export.edit_timeline_id)
    if edit is None:
        raise HTTPException(status_code=404, detail="edit_not_found")
    candidate = db.get(CandidateClip, edit.candidate_clip_id)
    return build_publishing_package(export, edit, candidate)
