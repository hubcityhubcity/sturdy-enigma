import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class MediaProbeResult:
    validation_status: str
    validation_message: str
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def parse_fps(rate: Optional[str]) -> Optional[float]:
    if not rate or rate == "0/0":
        return None
    if "/" not in rate:
        try:
            return float(rate)
        except ValueError:
            return None
    numerator, denominator = rate.split("/", 1)
    try:
        return round(float(numerator) / float(denominator), 3)
    except (ValueError, ZeroDivisionError):
        return None


def probe_media(path: str) -> MediaProbeResult:
    """Probe a local media file using ffprobe.

    The MVP calls this after a file exists locally. URL probing/import will download
    or stage the source first, then call this function.
    """
    media_path = Path(path)
    if not media_path.exists():
        return MediaProbeResult(
            validation_status="missing",
            validation_message=f"File does not exist: {path}",
        )

    command = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
    except FileNotFoundError:
        return MediaProbeResult(
            validation_status="ffprobe_missing",
            validation_message="ffprobe is not installed or not available on PATH.",
        )
    except subprocess.CalledProcessError as error:
        return MediaProbeResult(
            validation_status="invalid_media",
            validation_message=error.stderr or "ffprobe could not read media.",
        )
    except json.JSONDecodeError:
        return MediaProbeResult(
            validation_status="probe_parse_failed",
            validation_message="ffprobe returned unreadable metadata.",
        )

    streams = payload.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    media_format = payload.get("format", {})

    duration = None
    if media_format.get("duration"):
        try:
            duration = round(float(media_format["duration"]), 3)
        except ValueError:
            duration = None

    return MediaProbeResult(
        validation_status="valid",
        validation_message="Media metadata read successfully.",
        duration_seconds=duration,
        width=video_stream.get("width") if video_stream else None,
        height=video_stream.get("height") if video_stream else None,
        fps=parse_fps(video_stream.get("avg_frame_rate")) if video_stream else None,
        video_codec=video_stream.get("codec_name") if video_stream else None,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
    )
