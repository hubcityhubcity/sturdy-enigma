"""FFmpeg-backed audio spike detection for Titan GameSense.

This module detects unusually loud audio windows. It cannot label the sound as a scream,
laugh, or explosion by itself; it emits honest `audio_spike` evidence that becomes more
valuable when fused with gameplay, chat, or facecam signals.
"""

from __future__ import annotations

import math
import statistics
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioLevel:
    seconds: float
    rms_db: float


@dataclass(frozen=True)
class AudioSpike:
    start_seconds: float
    end_seconds: float
    intensity: int
    peak_db: float
    baseline_db: float
    confidence: float


def parse_astats_metadata(text: str) -> list[AudioLevel]:
    """Parse FFmpeg ametadata output containing pts_time and Overall.RMS_level."""
    current_time: float | None = None
    levels: list[AudioLevel] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "pts_time:" in line:
            try:
                current_time = float(line.split("pts_time:", 1)[1].split()[0])
            except (ValueError, IndexError):
                continue
        if "lavfi.astats.Overall.RMS_level=" in line and current_time is not None:
            value = line.split("=", 1)[1].strip()
            if value in {"-inf", "inf", "nan"}:
                continue
            try:
                levels.append(AudioLevel(seconds=current_time, rms_db=float(value)))
            except ValueError:
                continue

    return levels


def clamp_intensity(value: float) -> int:
    return max(0, min(100, round(value)))


def detect_audio_spikes_from_levels(
    levels: list[AudioLevel],
    absolute_threshold_db: float = -20.0,
    relative_gain_db: float = 10.0,
    merge_gap_seconds: float = 1.25,
) -> list[AudioSpike]:
    """Convert RMS samples into merged high-energy events.

    The dynamic threshold protects quieter streams: a window must be both loud enough
    in absolute terms and materially above the recording's median audio level.
    """
    if not levels:
        return []

    baseline_db = statistics.median(level.rms_db for level in levels)
    threshold_db = max(absolute_threshold_db, baseline_db + relative_gain_db)
    active = [level for level in levels if level.rms_db >= threshold_db]
    if not active:
        return []

    groups: list[list[AudioLevel]] = [[active[0]]]
    for level in active[1:]:
        if level.seconds - groups[-1][-1].seconds <= merge_gap_seconds:
            groups[-1].append(level)
        else:
            groups.append([level])

    spikes: list[AudioSpike] = []
    sample_step = max(0.1, statistics.median([
        right.seconds - left.seconds
        for left, right in zip(levels, levels[1:])
        if right.seconds > left.seconds
    ]) if len(levels) > 1 else 0.5)

    for group in groups:
        peak_db = max(level.rms_db for level in group)
        gain_db = max(0.0, peak_db - baseline_db)
        intensity = clamp_intensity(50 + (gain_db * 3.0) + max(0.0, peak_db - absolute_threshold_db) * 1.5)
        confidence = min(0.98, 0.55 + (gain_db / 40.0) + min(0.12, len(group) * 0.02))
        spikes.append(AudioSpike(
            start_seconds=round(group[0].seconds, 3),
            end_seconds=round(group[-1].seconds + sample_step, 3),
            intensity=intensity,
            peak_db=round(peak_db, 2),
            baseline_db=round(baseline_db, 2),
            confidence=round(confidence, 3),
        ))
    return spikes


def analyze_audio_spikes(media_path: str | Path) -> list[AudioSpike]:
    """Run FFmpeg astats on a local media file and return high-energy audio windows."""
    path = Path(media_path)
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")

    with tempfile.TemporaryDirectory(prefix="titan-gamesense-audio-") as temp_dir:
        metadata_path = Path(temp_dir) / "astats.txt"
        filter_graph = f"astats=metadata=1:reset=0.5,ametadata=print:file='{metadata_path.as_posix()}'"
        command = [
            "ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
            "-vn", "-af", filter_graph, "-f", "null", "-",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except FileNotFoundError as error:
            raise RuntimeError("FFmpeg is required for GameSense audio detection but was not found.") from error

        if result.returncode != 0 or not metadata_path.exists():
            detail = (result.stderr or "FFmpeg audio analysis failed.").strip()[-1000:]
            raise RuntimeError(detail)

        levels = parse_astats_metadata(metadata_path.read_text(encoding="utf-8", errors="replace"))
        return detect_audio_spikes_from_levels(levels)
