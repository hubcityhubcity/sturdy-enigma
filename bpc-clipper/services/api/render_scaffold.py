import json
import subprocess
from pathlib import Path

from caption_presets import ffmpeg_force_style
from caption_segments import CaptionSegment, build_caption_segments, build_caption_segments_from_words
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


def caption_duration(edit: EditTimeline) -> float:
    return max(1.0, edit.end_seconds - edit.start_seconds)


def caption_segments_for_export(edit: EditTimeline, caption_words: list[dict] | None = None) -> tuple[list[CaptionSegment], str]:
    """Prefer real word timestamps and retain text-only captions as a safe fallback."""
    duration = caption_duration(edit)
    timed_segments = build_caption_segments_from_words(
        caption_words or [],
        clip_start_seconds=edit.start_seconds,
        clip_duration_seconds=duration,
    )
    if timed_segments:
        return timed_segments, "word_timed"

    text = edit.hook_text or "Titan export placeholder"
    return build_caption_segments(text, duration), "estimated_from_hook_text"


def build_srt(edit: EditTimeline, caption_words: list[dict] | None = None) -> str:
    segments, _ = caption_segments_for_export(edit, caption_words)
    blocks = []
    for segment in segments:
        blocks.extend([
            str(segment.index),
            f"{format_timestamp(segment.start_seconds)} --> {format_timestamp(segment.end_seconds)}",
            segment.text,
            "",
        ])
    return "\n".join(blocks)


def build_vtt(edit: EditTimeline, caption_words: list[dict] | None = None) -> str:
    segments, _ = caption_segments_for_export(edit, caption_words)
    lines = ["WEBVTT", ""]
    for segment in segments:
        lines.extend([
            f"{format_timestamp(segment.start_seconds, '.')} --> {format_timestamp(segment.end_seconds, '.')}",
            segment.text,
            "",
        ])
    return "\n".join(lines)


def is_vertical_format(export_format: str) -> bool:
    return export_format in {"vertical_1080x1920", "tiktok", "youtube_shorts", "instagram_reels"}


def ffmpeg_subtitle_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")


def build_video_filter(export: ExportRecord, edit: EditTimeline, srt_path: Path | None) -> str | None:
    filters: list[str] = []
    if is_vertical_format(export.format):
        filters.extend([
            "scale=1080:1920:force_original_aspect_ratio=increase",
            "crop=1080:1920",
            "setsar=1",
        ])
    if export.include_burned_captions and srt_path is not None:
        style = ffmpeg_force_style(edit.caption_preset)
        filters.append(f"subtitles={ffmpeg_subtitle_path(srt_path)}:force_style='{style}'")
    return ",".join(filters) if filters else None


def write_sidecar_files(
    export: ExportRecord,
    edit: EditTimeline,
    video_path: Path,
    render_status: str,
    caption_words: list[dict] | None = None,
) -> dict:
    folder = export_dir(export.project_id, export.id)
    metadata_path = folder / "metadata.json"
    srt_path = folder / "captions.srt"
    vtt_path = folder / "captions.vtt"
    caption_segments, caption_timing_mode = caption_segments_for_export(edit, caption_words)

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
        "caption_segment_count": len(caption_segments),
        "caption_timing_mode": caption_timing_mode,
        "caption_word_count": len(caption_words or []),
        "crop_mode": edit.crop_mode,
        "status": render_status,
        "video_path": str(video_path),
        "target_aspect_ratio": "9:16" if is_vertical_format(export.format) else "source",
        "burned_captions": export.include_burned_captions,
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if export.include_srt or export.include_burned_captions:
        srt_path.write_text(build_srt(edit, caption_words), encoding="utf-8")
    if export.include_vtt:
        vtt_path.write_text(build_vtt(edit, caption_words), encoding="utf-8")

    return {
        "metadata_path": str(metadata_path),
        "srt_path": str(srt_path) if (export.include_srt or export.include_burned_captions) else None,
        "vtt_path": str(vtt_path) if export.include_vtt else None,
        "video_path": str(video_path),
    }


def create_placeholder_export_files(export: ExportRecord, edit: EditTimeline, caption_words: list[dict] | None = None) -> dict:
    folder = export_dir(export.project_id, export.id)
    video_path = folder / "video-placeholder.txt"
    video_path.write_text(
        "Placeholder only. Real FFmpeg rendering will replace this with an MP4.",
        encoding="utf-8",
    )
    return write_sidecar_files(export, edit, video_path, "placeholder_render_complete", caption_words)


def render_trimmed_mp4(
    export: ExportRecord,
    edit: EditTimeline,
    source: Source | None,
    caption_words: list[dict] | None = None,
) -> dict:
    """Render a trimmed MP4, preferring actual transcript-word timing for captions."""
    if source is None or not source.storage_path:
        return create_placeholder_export_files(export, edit, caption_words)

    input_path = Path(source.storage_path)
    if not input_path.exists():
        return create_placeholder_export_files(export, edit, caption_words)

    folder = export_dir(export.project_id, export.id)
    output_path = folder / "clip.mp4"
    duration = caption_duration(edit)
    srt_path = folder / "captions.srt"
    if export.include_burned_captions:
        srt_path.write_text(build_srt(edit, caption_words), encoding="utf-8")
    vf = build_video_filter(export, edit, srt_path if export.include_burned_captions else None)

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
        return create_placeholder_export_files(export, edit, caption_words)
    except subprocess.CalledProcessError as error:
        error_path = folder / "render-error.txt"
        error_path.write_text(error.stderr or "FFmpeg render failed.", encoding="utf-8")
        return create_placeholder_export_files(export, edit, caption_words)

    if export.include_burned_captions:
        status = "ffmpeg_burned_word_timed_captions_complete" if caption_words else "ffmpeg_burned_segmented_captions_complete"
    elif is_vertical_format(export.format):
        status = "ffmpeg_vertical_9x16_complete"
    else:
        status = "ffmpeg_trim_complete"
    return write_sidecar_files(export, edit, output_path, status, caption_words)
