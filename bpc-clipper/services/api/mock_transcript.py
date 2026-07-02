from dataclasses import dataclass


@dataclass
class MockSegment:
    speaker_label: str
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float = 1.0


MOCK_SEGMENTS = [
    MockSegment(
        "Speaker 1",
        12.0,
        34.0,
        "Let me ask you something that most people avoid. If the system is built to keep creators broke, why are we still playing by their rules?",
    ),
    MockSegment(
        "Speaker 2",
        34.5,
        58.0,
        "That is exactly the point. The problem is not talent. The problem is ownership, distribution, and whether you control the audience after the clip goes viral.",
    ),
    MockSegment(
        "Speaker 1",
        72.0,
        101.0,
        "The wild part is people think going viral is the business. Going viral is just the front door. The real business is what happens after people walk in.",
    ),
    MockSegment(
        "Speaker 2",
        120.0,
        164.0,
        "If you are building a media brand, you cannot only think like a creator. You have to think like a producer, a distributor, and a software company at the same time.",
    ),
    MockSegment(
        "Speaker 1",
        210.0,
        252.0,
        "The moment I stopped chasing attention and started studying retention, everything changed. Views are loud, but watch time tells the truth.",
    ),
    MockSegment(
        "Speaker 2",
        300.0,
        348.0,
        "Here is the mistake. People cut the loudest part of the podcast, but the loudest part is not always the strongest clip. Sometimes the strongest clip is the clearest idea.",
    ),
]


def get_mock_segments() -> list[MockSegment]:
    return MOCK_SEGMENTS


def word_timings_for_segment(segment: MockSegment) -> list[dict]:
    words = segment.text.split()
    if not words:
        return []

    duration = segment.end_seconds - segment.start_seconds
    step = duration / len(words)
    timings = []
    for index, word in enumerate(words):
        timings.append({
            "start_seconds": round(segment.start_seconds + index * step, 3),
            "end_seconds": round(segment.start_seconds + (index + 1) * step, 3),
            "text": word.strip(),
            "confidence": segment.confidence,
        })
    return timings
