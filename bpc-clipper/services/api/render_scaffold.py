import json
from pathlib import Path

from local_storage import STORAGE_ROOT
from models import EditTimeline, ExportRecord


def format_timestamp(seconds: float, separator: str = ',') -> str:
    total_ms = int(seconds * 1000)
    hours = total_ms // 3_600_000
    total_ms %= 3_600_000
    minutes = total_ms // 60_000
    total_ms %= 60_000
    secs = total_ms // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{millis:03}"


def export_dir(project_id: str, export_id: str) -> Path:
    path = STORAGE_ROOT / "exports" / project_id / export_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_srt(edit: EditTimeline) -> str:
    text = edit.hook_text or "BPC export placeholder"
    return "\n".join([
        "1",
        f"{format_timestamp(0)} --> {format_timestamp(max(1.0, edit.end_seconds - edit.start_seconds))}",
        text,
        "",
    ])


def build_vtt(edit: EditTimeline) -> str:
    text = edit.hook_text or "BPC export placeholder"
    return "\n".join([
        "WEBVTT",
        "",
        f"{format_timestamp(0, '.')} --> {format_timestamp(max(1.0, edit.end_seconds - edit.start_seconds), '.')}",
        text,
        "",
    ])


def create_placeholder_export_files(export: ExportRecord, edit: EditTimeline) -> dict:
    folder = export_dir(export.project_id, export.id)

    metadata_path = folder / "metadata.json"
    srt_path = folder / "captions.srt"
    vtt_path = folder / "captions.vtt"
    video_path = folder / "video-placeholder.txt"

    metadata = {
        "export_id": export.id,
        "project_id": export.project_id,
        "edit_timeline_id": edit.id,
        "format": export.format,
        "start_seconds": edit.start_seconds,
        "end_seconds": edit.end_seconds,
        "duration_seconds": round(edit.end_seconds - edit.start_seconds, 3),
        "hook_text": edit.hook_text,
        "caption_preset": edit.caption_preset,
        "crop_mode": edit.crop_mode,
        "status": "placeholder_render_complete",
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if export.include_srt:
        srt_path.write_text(build_srt(edit), encoding="utf-8")
    if export.include_vtt:
        vtt_path.write_text(build_vtt(edit), encoding="utf-8")

    video_path.write_text(
        "Placeholder only. Real FFmpeg rendering will replace this with an MP4.",
        encoding="utf-8",
    )

    return {
        "metadata_path": str(metadata_path),
        "srt_path": str(srt_path) if export.include_srt else None,
        "vtt_path": str(vtt_path) if export.include_vtt else None,
        "video_path": str(video_path),
    }
