import json
import subprocess
from pathlib import Path

from local_storage import STORAGE_ROOT
from models import EditTimeline, ExportRecord, Source


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


def is_vertical_format(export_format: str) -> bool:
    return export_format in {"vertical_1080x1920", "tiktok", "youtube_shorts", "instagram_reels"}


def video_filter_for_format(export_format: str) -> str | None:
    if is_vertical_format(export_format):
        return "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
    return None


def write_sidecar_files(export: ExportRecord, edit: EditTimeline, video_path: Path, render_status: str) -> dict:
    folder = export_dir(export.project_id, export.id)
    metadata_path = folder / "metadata.json"
    srt_path = folder / "captions.srt"
    vtt_path = folder / "captions.vtt"

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
        "status": render_status,
        "video_path": str(video_path),
        "target_aspect_ratio": "9:16" if is_vertical_format(export.format) else "source",
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if export.include_srt:
        srt_path.write_text(build_srt(edit), encoding="utf-8")
    if export.include_vtt:
        vtt_path.write_text(build_vtt(edit), encoding="utf-8")

    return {
        "metadata_path": str(metadata_path),
        "srt_path": str(srt_path) if export.include_srt else None,
        "vtt_path": str(vtt_path) if export.include_vtt else None,
        "video_path": str(video_path),
    }


def create_placeholder_export_files(export: ExportRecord, edit: EditTimeline) -> dict:
    folder = export_dir(export.project_id, export.id)
    video_path = folder / "video-placeholder.txt"
    video_path.write_text(
        "Placeholder only. Real FFmpeg rendering will replace this with an MP4.",
        encoding="utf-8",
    )
    return write_sidecar_files(export, edit, video_path, "placeholder_render_complete")


def render_trimmed_mp4(export: ExportRecord, edit: EditTimeline, source: Source | None) -> dict:
    """Render a trimmed MP4 from source media.

    Current supported outputs:
    - source aspect ratio trim
    - 1080x1920 vertical crop for Shorts/TikTok/Reels formats
    """
    if source is None or not source.storage_path:
        return create_placeholder_export_files(export, edit)

    input_path = Path(source.storage_path)
    if not input_path.exists():
        return create_placeholder_export_files(export, edit)

    folder = export_dir(export.project_id, export.id)
    output_path = folder / "clip.mp4"
    duration = max(1.0, edit.end_seconds - edit.start_seconds)
    vf = video_filter_for_format(export.format)

    command = [
        "ffmpeg",
        "-y",
        "-ss", str(edit.start_seconds),
        "-i", str(input_path),
        "-t", str(duration),
    ]

    if vf:
        command.extend(["-vf", vf])

    command.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        return create_placeholder_export_files(export, edit)
    except subprocess.CalledProcessError as error:
        error_path = folder / "render-error.txt"
        error_path.write_text(error.stderr or "FFmpeg render failed.", encoding="utf-8")
        return create_placeholder_export_files(export, edit)

    status = "ffmpeg_vertical_9x16_complete" if vf else "ffmpeg_trim_complete"
    return write_sidecar_files(export, edit, output_path, status)
