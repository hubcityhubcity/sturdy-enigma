"""FFmpeg-backed scene-change detection for Titan GameSense.

This detector identifies sharp visual changes such as cuts, victory screens, replay
transitions, kill-screen changes, and jump-scare edits. It does not claim to identify
specific in-game actions; GameSense relies on multimodal fusion for that meaning.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


SHOWINFO_PTS_PATTERN = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")


@dataclass(frozen=True)
class VisualSceneChange:
    start_seconds: float
    end_seconds: float
    intensity: int
    confidence: float
    threshold: float


def parse_showinfo_scene_times(text: str) -> list[float]:
    """Extract selected-frame timestamps from FFmpeg showinfo logs."""
    times: list[float] = []
    for match in SHOWINFO_PTS_PATTERN.finditer(text):
        seconds = float(match.group(1))
        if not times or abs(seconds - times[-1]) > 0.001:
            times.append(seconds)
    return times


def scene_changes_from_times(times: list[float], threshold: float) -> list[VisualSceneChange]:
    """Create normalized GameSense events from selected scene-change timestamps."""
    threshold = max(0.0, min(1.0, threshold))
    intensity = max(0, min(100, round(45 + threshold * 55)))
    confidence = max(0.5, min(0.95, round(0.55 + threshold * 0.35, 3)))
    return [
        VisualSceneChange(
            start_seconds=round(seconds, 3),
            end_seconds=round(seconds + 0.35, 3),
            intensity=intensity,
            confidence=confidence,
            threshold=threshold,
        )
        for seconds in sorted(set(times))
    ]


def analyze_visual_scene_changes(media_path: str | Path, threshold: float = 0.30) -> list[VisualSceneChange]:
    """Use FFmpeg scene scoring to find sharp visual transitions in a local video."""
    path = Path(media_path)
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")

    normalized_threshold = max(0.0, min(1.0, threshold))
    video_filter = f"select='gt(scene,{normalized_threshold})',showinfo"
    command = [
        "ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-an", "-vf", video_filter, "-f", "null", "-",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        raise RuntimeError("FFmpeg is required for GameSense visual detection but was not found.") from error

    if result.returncode != 0:
        detail = (result.stderr or "FFmpeg visual analysis failed.").strip()[-1000:]
        raise RuntimeError(detail)

    return scene_changes_from_times(parse_showinfo_scene_times(result.stderr or ""), normalized_threshold)
