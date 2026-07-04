import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mock_transcript import get_mock_segments, word_timings_for_segment


class TranscriptionConfigurationError(RuntimeError):
    """Raised when Titan would otherwise fabricate a transcript from demo data."""


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
    """Explicit demo-only provider. Never select this automatically for user media."""

    name = "mock_demo"

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

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "base")
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            import whisper  # type: ignore
        except ImportError as error:
            raise TranscriptionConfigurationError(
                "Whisper is selected but not installed. Install requirements-whisper.txt or select a configured transcription provider."
            ) from error
        self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        if not media_path or not media_path.exists():
            raise FileNotFoundError(f"Media file not found for Whisper transcription: {media_path}")

        model = self._load_model()
        raw_result = model.transcribe(str(media_path), word_timestamps=True)
        language = raw_result.get("language") or "en"
        raw_segments = raw_result.get("segments") or []
        segments: list[TranscribedSegment] = []

        for raw_segment in raw_segments:
            words: list[TranscribedWord] = []
            for raw_word in raw_segment.get("words") or []:
                word_text = str(raw_word.get("word") or raw_word.get("text") or "").strip()
                if not word_text:
                    continue
                words.append(
                    TranscribedWord(
                        start_seconds=float(raw_word.get("start") or 0.0),
                        end_seconds=float(raw_word.get("end") or raw_word.get("start") or 0.0),
                        text=word_text,
                        confidence=float(raw_word.get("probability") or raw_word.get("confidence") or 1.0),
                    )
                )

            segment_text = str(raw_segment.get("text") or "").strip()
            if not segment_text and words:
                segment_text = " ".join(word.text for word in words)
            if not segment_text:
                continue

            segments.append(
                TranscribedSegment(
                    speaker_label="Speaker 1",
                    start_seconds=float(raw_segment.get("start") or 0.0),
                    end_seconds=float(raw_segment.get("end") or raw_segment.get("start") or 0.0),
                    text=segment_text,
                    confidence=float(raw_segment.get("avg_logprob") or 1.0),
                    words=words,
                )
            )

        return TranscriptionResult(language=language, provider=f"{self.name}:{self.model_name}", confidence=1.0, segments=segments)


def get_transcription_provider(provider_name: str | None = None) -> TranscriptionProvider:
    selected_provider = (provider_name or os.getenv("TRANSCRIPTION_PROVIDER", "")).strip().lower()
    if selected_provider in {"mock", "demo", "mock_demo"}:
        return MockTranscriptionProvider()
    if selected_provider == "whisper":
        return WhisperTranscriptionProvider()
    if not selected_provider or selected_provider in {"unconfigured", "disabled", "none"}:
        raise TranscriptionConfigurationError(
            "Real transcription is not configured. Set TRANSCRIPTION_PROVIDER=whisper and install requirements-whisper.txt before analyzing uploaded media."
        )
    raise TranscriptionConfigurationError(f"Unsupported transcription provider: {selected_provider}")
