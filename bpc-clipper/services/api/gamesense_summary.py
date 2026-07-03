"""Evidence summaries for transparent Titan GameSense project analysis."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


DEFAULT_MODALITIES = ("audio", "visual", "chat", "facecam", "gameplay", "transcript")


def summarize_gamesense_events(events: Iterable[object]) -> dict:
    """Return deterministic counts and strongest-signal metadata for a project timeline."""
    event_list = list(events)
    modality_counts = Counter(getattr(event, "modality", "unknown") or "unknown" for event in event_list)
    event_type_counts = Counter(getattr(event, "event_type", "unknown") or "unknown" for event in event_list)

    modalities = {modality: modality_counts.get(modality, 0) for modality in DEFAULT_MODALITIES}
    for modality, count in sorted(modality_counts.items()):
        modalities.setdefault(modality, count)

    strongest = sorted(
        event_list,
        key=lambda event: (
            -int(getattr(event, "intensity", 0) or 0),
            -float(getattr(event, "confidence", 0) or 0),
            float(getattr(event, "start_seconds", 0) or 0),
        ),
    )[:5]

    return {
        "total_events": len(event_list),
        "modality_counts": modalities,
        "event_type_counts": dict(sorted(event_type_counts.items())),
        "strongest_events": [
            {
                "event_type": getattr(event, "event_type", "unknown"),
                "modality": getattr(event, "modality", "unknown"),
                "start_seconds": getattr(event, "start_seconds", 0),
                "end_seconds": getattr(event, "end_seconds", 0),
                "intensity": getattr(event, "intensity", 0),
                "confidence": getattr(event, "confidence", 0),
                "evidence": getattr(event, "evidence", None) or {},
            }
            for event in strongest
        ],
    }
