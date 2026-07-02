from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from mock_transcript import get_mock_segments, word_timings_for_segment


@dataclass
class TranscribedWord:
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float = 1.0


@dataclass
class TranscribedSegment:
    speaker_label: str
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float = 1.0
    words: list[TranscribedWord] | None = None


@dataclass
class TranscriptionResult:
    language: str
    provider: str
    confidence: float
    segments: list[TranscribedSegment]


class TranscriptionProvider(Protocol):
    name: str

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        ...


class MockTranscriptionProvider:
    name = "mock"

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        segments: list[TranscribedSegment] = []
        for mock_segment in get_mock_segments():
            words = [
                TranscribedWord(
                    start_seconds=word["start_seconds"],
                    end_seconds=word["end_seconds"],
                    text=word["text"],
                    confidence=word["confidence"],
                )
                for word in word_timings_for_segment(mock_segment)
            ]
            segments.append(
                TranscribedSegment(
                    speaker_label=mock_segment.speaker_label,
                    start_seconds=mock_segment.start_seconds,
                    end_seconds=mock_segment.end_seconds,
                    text=mock_segment.text,
                    confidence=mock_segment.confidence,
                    words=words,
                )
            )
        return TranscriptionResult(language="en", provider=self.name, confidence=1.0, segments=segments)


class WhisperTranscriptionProvider:
    name = "whisper"

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        raise NotImplementedError(
            "Whisper provider scaffold only. Install/configure a Whisper backend before enabling this provider."
        )


def get_transcription_provider(provider_name: str | None = None) -> TranscriptionProvider:
    if provider_name == "whisper":
        return WhisperTranscriptionProvider()
    return MockTranscriptionProvider()
