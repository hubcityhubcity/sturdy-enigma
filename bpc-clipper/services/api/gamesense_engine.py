"""Deterministic multimodal scoring for gaming-stream moments.

GameSense receives normalized, time-coded signals from gameplay, audio, chat, facecam,
visual analysis, or transcript adapters and combines nearby evidence into clip-ready
moments with setup and reaction room.
"""

from dataclasses import dataclass
from typing import Iterable


MODALITY_WEIGHTS = {
    "gameplay": 1.0,
    "audio": 0.78,
    "chat": 0.72,
    "facecam": 0.86,
    "visual": 0.66,
    "transcript": 0.5,
}

EVENT_TYPE_BONUSES = {
    "clutch": 22,
    "victory": 18,
    "elimination": 15,
    "knockout": 15,
    "jump_scare": 18,
    "rage": 16,
    "laugh": 12,
    "scream": 14,
    "chat_spike": 14,
    "audio_spike": 10,
    "scene_change": 9,
    "reaction": 12,
    "fail": 10,
    "combo": 14,
    "round_end": 8,
}

CATEGORY_PRIORITY = [
    ("clutch", "clutch"),
    ("victory", "victory"),
    ("jump_scare", "jump_scare"),
    ("rage", "rage_moment"),
    ("fail", "funny_fail"),
    ("combo", "insane_play"),
    ("elimination", "insane_play"),
    ("knockout", "insane_play"),
    ("laugh", "funny_reaction"),
]


@dataclass(frozen=True)
class GameSignal:
    event_type: str
    modality: str
    start_seconds: float
    end_seconds: float
    intensity: int = 50
    confidence: float = 1.0
    evidence: dict | None = None


@dataclass(frozen=True)
class GameMoment:
    start_seconds: float
    end_seconds: float
    score: int
    category: str
    explanation: str
    evidence: list[GameSignal]


def clamp(value: float, lower: float = 0, upper: float = 100) -> int:
    return int(max(lower, min(upper, round(value))))


def normalized_score(signal: GameSignal) -> float:
    modality_weight = MODALITY_WEIGHTS.get(signal.modality, 0.45)
    event_bonus = EVENT_TYPE_BONUSES.get(signal.event_type, 5)
    intensity = max(0, min(signal.intensity, 100))
    confidence = max(0.0, min(signal.confidence, 1.0))
    return (intensity * modality_weight * confidence) + event_bonus


def signals_overlap_window(anchor: GameSignal, other: GameSignal, seconds: float) -> bool:
    return other.start_seconds <= anchor.end_seconds + seconds and other.end_seconds >= anchor.start_seconds - seconds


def category_for(signals: list[GameSignal]) -> str:
    event_types = {signal.event_type for signal in signals}
    for event_type, category in CATEGORY_PRIORITY:
        if event_type in event_types:
            return category
    if "chat_spike" in event_types:
        return "chat_loses_it"
    if "audio_spike" in event_types:
        return "reaction_moment"
    if "reaction" in event_types:
        return "reaction_moment"
    return "gameplay_moment"


def describe(signals: list[GameSignal]) -> str:
    modalities = sorted({signal.modality for signal in signals})
    event_types = sorted({signal.event_type.replace("_", " ") for signal in signals})
    return f"{len(signals)} aligned signal(s): {', '.join(event_types)} across {', '.join(modalities)}."


def overlap_ratio(first: GameMoment, second: GameMoment) -> float:
    """Return overlap normalized by the shorter clip window.

    This is intentionally stricter than raw intersection-over-union because candidate
    windows are designed with setup and reaction padding. A short candidate mostly
    contained inside a longer one is almost always a duplicate highlight.
    """
    intersection = max(0.0, min(first.end_seconds, second.end_seconds) - max(first.start_seconds, second.start_seconds))
    shorter_duration = max(0.001, min(first.end_seconds - first.start_seconds, second.end_seconds - second.start_seconds))
    return intersection / shorter_duration


def suppress_near_duplicate_moments(moments: list[GameMoment], minimum_overlap: float = 0.75) -> list[GameMoment]:
    """Keep the strongest candidate when nearby signals describe the same highlight."""
    selected: list[GameMoment] = []
    for moment in sorted(moments, key=lambda item: (-item.score, item.start_seconds, item.end_seconds)):
        if any(overlap_ratio(moment, kept) >= minimum_overlap for kept in selected):
            continue
        selected.append(moment)
    return sorted(selected, key=lambda item: (-item.score, item.start_seconds))


def build_gamesense_moments(
    signals: Iterable[GameSignal],
    setup_seconds: float = 8.0,
    reaction_seconds: float = 6.0,
    fusion_window_seconds: float = 5.0,
    min_score: int = 55,
) -> list[GameMoment]:
    """Fuse nearby cross-modal signals into ranked gaming clip candidates.

    Each signal can anchor a candidate, but overlapping candidates are collapsed so a
    clutch plus scream plus chat burst becomes one clean highlight rather than four
    slightly different versions of the same clip.
    """
    ordered = sorted(signals, key=lambda item: (item.start_seconds, item.end_seconds))
    moments: list[GameMoment] = []

    for anchor in ordered:
        nearby = [signal for signal in ordered if signals_overlap_window(anchor, signal, fusion_window_seconds)]
        raw_score = normalized_score(anchor)
        raw_score += sum(normalized_score(signal) * 0.35 for signal in nearby if signal is not anchor)
        modalities = {signal.modality for signal in nearby}
        raw_score += max(0, len(modalities) - 1) * 8
        if "gameplay" in modalities and ("audio" in modalities or "facecam" in modalities or "chat" in modalities or "visual" in modalities):
            raw_score += 10

        score = clamp(raw_score)
        if score < min_score:
            continue
        start = max(0.0, round(anchor.start_seconds - setup_seconds, 3))
        end = round(max(anchor.end_seconds, max(signal.end_seconds for signal in nearby)) + reaction_seconds, 3)
        moments.append(GameMoment(
            start_seconds=start,
            end_seconds=end,
            score=score,
            category=category_for(nearby),
            explanation=describe(nearby),
            evidence=nearby,
        ))

    return suppress_near_duplicate_moments(moments)
