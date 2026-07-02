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
        return ["BPC export placeholder"]

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
