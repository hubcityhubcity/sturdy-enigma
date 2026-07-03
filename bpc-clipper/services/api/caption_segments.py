from dataclasses import dataclass
import re


@dataclass
class CaptionSegment:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


def split_text_into_chunks(text: str, max_words: int = 6, max_chars: int = 42) -> list[str]:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ["Titan export placeholder"]

    words = cleaned.split(" ")
    chunks: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join([*current, word]).strip()
        should_break = len(current) >= max_words or len(candidate) > max_chars
        if should_break and current:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(" ".join(current))

    return chunks


def build_caption_segments(text: str, duration_seconds: float) -> list[CaptionSegment]:
    chunks = split_text_into_chunks(text)
    duration = max(1.0, duration_seconds)
    step = duration / len(chunks)
    segments: list[CaptionSegment] = []

    for index, chunk in enumerate(chunks, start=1):
        start = round((index - 1) * step, 3)
        end = round(index * step, 3)
        segments.append(CaptionSegment(index=index, start_seconds=start, end_seconds=end, text=chunk))

    return segments


def build_caption_segments_from_words(
    words: list[dict],
    clip_start_seconds: float,
    clip_duration_seconds: float,
    max_words: int = 6,
    max_chars: int = 42,
) -> list[CaptionSegment]:
    """Group timestamped transcript words into readable, clip-relative captions.

    Inputs are source-relative word timestamps. The returned caption timestamps begin at
    0 because the rendered media is trimmed to the clip start time.
    """
    if not words:
        return []

    clip_end_seconds = clip_start_seconds + max(1.0, clip_duration_seconds)
    normalized = []
    for word in words:
        text = re.sub(r"\s+", " ", str(word.get("text") or "")).strip()
        start = float(word.get("start_seconds", clip_start_seconds))
        end = float(word.get("end_seconds", start))
        if not text or end <= clip_start_seconds or start >= clip_end_seconds:
            continue
        normalized.append({
            "text": text,
            "start": max(clip_start_seconds, start),
            "end": min(clip_end_seconds, max(end, start + 0.05)),
        })

    if not normalized:
        return []

    segments: list[CaptionSegment] = []
    current: list[dict] = []

    def flush() -> None:
        if not current:
            return
        start = max(0.0, current[0]["start"] - clip_start_seconds)
        end = min(clip_duration_seconds, current[-1]["end"] - clip_start_seconds)
        if end <= start:
            end = min(clip_duration_seconds, start + 0.1)
        segments.append(CaptionSegment(
            index=len(segments) + 1,
            start_seconds=round(start, 3),
            end_seconds=round(end, 3),
            text=" ".join(item["text"] for item in current),
        ))

    for word in normalized:
        candidate_text = " ".join([*(item["text"] for item in current), word["text"]]).strip()
        should_break = bool(current) and (len(current) >= max_words or len(candidate_text) > max_chars)
        if should_break:
            flush()
            current = []
        current.append(word)

    flush()
    return segments
