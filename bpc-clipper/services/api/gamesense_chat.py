"""Platform-neutral chat spike detection for Titan GameSense.

Adapters for Twitch, Kick, YouTube, or downloaded VOD chat only need to normalize their
messages into ``ChatMessage`` values. This module finds message-density bursts and adds
hype-context evidence without claiming to understand the game itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


HYPE_TOKENS = {
    "w", "ws", "wow", "omg", "gg", "ggez", "letsgo", "let'sgo", "lfg", "clip",
    "clipped", "insane", "crazy", "goat", "wtf", "fire", "holy", "nah", "bro",
    "rip", "dead", "sheesh", "yooo", "nooo", "pog", "poggers", "kappa", "lul",
    "omegalul", "monkas", "wutface", "ez",
}

CLIP_PHRASES = {
    "clip that", "clip it", "somebody clip", "someone clip", "no way", "holy shit",
    "oh my god", "what the hell", "that was insane", "let's go", "lets go",
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
    hype_score: int
    top_terms: list[str]
    sample_messages: list[str]


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().replace("_", " ").split())


def normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9']+", "", token.lower())


def hype_terms_for_message(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    terms: list[str] = []
    compact = normalized.replace(" ", "")
    for phrase in CLIP_PHRASES:
        if phrase in normalized:
            terms.append(phrase.replace(" ", "_"))

    for raw_token in normalized.split():
        token = normalize_token(raw_token)
        if not token:
            continue
        if token in HYPE_TOKENS or token in compact and token in {"letsgo", "noway", "clipthat"}:
            terms.append(token)
        if len(token) >= 3 and len(set(token)) == 1:
            terms.append(f"{token[0]}_spam")

    return terms


def is_hype_message(text: str) -> bool:
    return bool(hype_terms_for_message(text))


def clamp_intensity(value: float) -> int:
    return max(0, min(100, round(value)))


def top_terms(terms: list[str], limit: int = 8) -> list[str]:
    return sorted(set(terms), key=lambda term: (-terms.count(term), term))[:limit]


def detect_chat_spikes(
    messages: list[ChatMessage],
    window_seconds: float = 5.0,
    min_messages: int = 5,
    min_messages_per_second: float = 1.0,
    relative_multiplier: float = 2.5,
    merge_gap_seconds: float = 3.0,
) -> list[ChatSpike]:
    """Find unusually dense, short chat bursts with clip-worthy language.

    A candidate window must clear both an absolute rate and a dynamic baseline rate.
    Hype phrases raise confidence and intensity but density still matters.
    """
    ordered = sorted((item for item in messages if item.seconds >= 0 and item.text.strip()), key=lambda item: item.seconds)
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
        messages_in_spike = sorted(deduped.values(), key=lambda item: item.seconds)
        duration = max(1.0, end - start)
        rate = len(messages_in_spike) / duration
        terms = [term for message in messages_in_spike for term in hype_terms_for_message(message.text)]
        hype_count = sum(1 for message in messages_in_spike if hype_terms_for_message(message.text))
        hype_score = len(terms) * 3 + sum(4 for term in terms if term in {"clip_that", "clip_it", "somebody_clip", "someone_clip"})
        rate_lift = rate / max(0.1, baseline_rate)
        hype_ratio = hype_count / max(1, len(messages_in_spike))
        intensity = clamp_intensity(35 + (rate_lift * 12) + (hype_ratio * 28) + min(20, len(messages_in_spike)) + min(12, hype_score / 3))
        confidence = min(0.98, 0.5 + min(0.28, rate_lift / 10) + min(0.16, hype_ratio * 0.3) + min(0.08, len(messages_in_spike) / 100) + min(0.06, hype_score / 200))
        spikes.append(ChatSpike(
            start_seconds=round(start, 3),
            end_seconds=round(end + 0.5, 3),
            intensity=intensity,
            confidence=round(confidence, 3),
            message_count=len(messages_in_spike),
            messages_per_second=round(rate, 3),
            baseline_messages_per_second=round(baseline_rate, 3),
            hype_message_count=hype_count,
            hype_score=hype_score,
            top_terms=top_terms(terms),
            sample_messages=[message.text for message in messages_in_spike[:5]],
        ))

    return spikes
