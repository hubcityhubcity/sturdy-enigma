from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import ExportRecord

router = APIRouter()

ExportFileKind = Literal["video", "srt", "vtt", "metadata"]


def path_for_kind(export: ExportRecord, kind: ExportFileKind) -> str | None:
    if kind == "video":
        return export.video_path
    if kind == "srt":
        return export.srt_path
    if kind == "vtt":
        return export.vtt_path
    if kind == "metadata":
        return export.metadata_path
    return None


def media_type_for_kind(kind: ExportFileKind) -> str:
    return {
        "video": "video/mp4",
        "srt": "application/x-subrip",
        "vtt": "text/vtt",
        "metadata": "application/json",
    }[kind]


def filename_for_kind(export: ExportRecord, kind: ExportFileKind) -> str:
    extension = {
        "video": "mp4",
        "srt": "srt",
        "vtt": "vtt",
        "metadata": "json",
    }[kind]
    return f"bpc-export-{export.id}.{extension}"


@router.get("/exports/{export_id}/files/{kind}")
def download_export_file(export_id: str, kind: ExportFileKind, db: Session = Depends(get_db)):
    export = db.get(ExportRecord, export_id)
    if export is None:
        raise HTTPException(status_code=404, detail="export_not_found")

    selected_path = path_for_kind(export, kind)
    if not selected_path:
        raise HTTPException(status_code=404, detail="export_file_not_available")

    file_path = Path(selected_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="export_file_missing")

    return FileResponse(
        path=file_path,
        media_type=media_type_for_kind(kind),
        filename=filename_for_kind(export, kind),
    )
