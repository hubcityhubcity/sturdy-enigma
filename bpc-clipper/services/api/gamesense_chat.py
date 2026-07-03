"""Platform-neutral chat burst detection for Titan GameSense.

Adapters for Twitch, Kick, YouTube, or downloaded VOD chat only need to normalize their
messages into ``ChatMessage`` values. This module finds message-density bursts and adds
lightweight hype-context evidence without claiming to understand the game itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median


HYPE_TOKENS = {
    "w", "ws", "wow", "omg", "gg", "ggez", "letsgo", "let'sgo", "clip", "clipped",
    "insane", "crazy", "goat", "wtf", "lfg", "fire", "holy", "nah", "no way",
}


@dataclass(frozen=True)
class ChatMessage:
    seconds: float
    text: str = ""
    author: str | None = None


@dataclass(frozen=True)
class ChatSpike:
    start_seconds: float
    end_seconds: float
    intensity: int
    confidence: float
    message_count: int
    messages_per_second: float
    baseline_messages_per_second: float
    hype_message_count: int


def normalize_token(text: str) -> str:
    return " ".join((text or "").lower().replace("_", " ").split())


def is_hype_message(text: str) -> bool:
    normalized = normalize_token(text)
    if not normalized:
        return False
    compact = normalized.replace(" ", "")
    return any(token in normalized.split() or token in compact for token in HYPE_TOKENS)


def clamp_intensity(value: float) -> int:
    return max(0, min(100, round(value)))


def detect_chat_spikes(
    messages: list[ChatMessage],
    window_seconds: float = 5.0,
    min_messages: int = 5,
    min_messages_per_second: float = 1.0,
    relative_multiplier: float = 2.5,
    merge_gap_seconds: float = 3.0,
) -> list[ChatSpike]:
    """Find unusually dense, short chat bursts.

    A candidate window must clear both a minimum absolute rate and a dynamic baseline
    threshold. This prevents busy channels from treating ordinary chat as a highlight.
    """
    ordered = sorted((item for item in messages if item.seconds >= 0), key=lambda item: item.seconds)
    if len(ordered) < min_messages:
        return []

    end_time = max(item.seconds for item in ordered)
    total_duration = max(window_seconds, end_time - ordered[0].seconds)
    baseline_rate = len(ordered) / total_duration
    threshold_rate = max(min_messages_per_second, baseline_rate * relative_multiplier)

    candidates: list[tuple[float, float, list[ChatMessage]]] = []
    left = 0
    for right, message in enumerate(ordered):
        while message.seconds - ordered[left].seconds > window_seconds:
            left += 1
        window = ordered[left:right + 1]
        rate = len(window) / window_seconds
        if len(window) >= min_messages and rate >= threshold_rate:
            candidates.append((window[0].seconds, message.seconds, window))

    if not candidates:
        return []

    groups: list[list[tuple[float, float, list[ChatMessage]]]] = [[candidates[0]]]
    for candidate in candidates[1:]:
        if candidate[0] - groups[-1][-1][1] <= merge_gap_seconds:
            groups[-1].append(candidate)
        else:
            groups.append([candidate])

    spikes: list[ChatSpike] = []
    for group in groups:
        start = group[0][0]
        end = max(item[1] for item in group)
        unique_messages = [message for _, _, window in group for message in window]
        deduped: dict[tuple[float, str, str | None], ChatMessage] = {
            (item.seconds, item.text, item.author): item for item in unique_messages
        }
        messages_in_spike = list(deduped.values())
        duration = max(1.0, end - start)
        rate = len(messages_in_spike) / duration
        hype_count = sum(is_hype_message(message.text) for message in messages_in_spike)
        rate_lift = rate / max(0.1, baseline_rate)
        hype_ratio = hype_count / max(1, len(messages_in_spike))
        intensity = clamp_intensity(35 + (rate_lift * 12) + (hype_ratio * 28) + min(20, len(messages_in_spike)))
        confidence = min(0.98, 0.5 + min(0.28, rate_lift / 10) + min(0.16, hype_ratio * 0.3) + min(0.08, len(messages_in_spike) / 100))
        spikes.append(ChatSpike(
            start_seconds=round(start, 3),
            end_seconds=round(end + 0.5, 3),
            intensity=intensity,
            confidence=round(confidence, 3),
            message_count=len(messages_in_spike),
            messages_per_second=round(rate, 3),
            baseline_messages_per_second=round(baseline_rate, 3),
            hype_message_count=hype_count,
        ))

    return spikes
