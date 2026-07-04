"""Visual-analysis runtime for real face detection and shot-aware crop planning.

The runtime is deliberately explicit: it does not claim speaker focus unless the local
YuNet model is available, detection completes, and the resulting plan contains a stable
subject. It uses a pinned model URL and SHA-256 check rather than trusting arbitrary model
paths or downloads.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from visual_editing import FaceBox, FaceObservation, VisualEditPlan, build_visual_edit_plan


class VisualAnalysisConfigurationError(RuntimeError):
    pass


YUNET_MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"
YUNET_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx?download=1"
)
YUNET_MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
YUNET_MODEL_MAX_BYTES = 2_000_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def visual_model_root() -> Path:
    return Path(os.getenv("VISUAL_MODEL_ROOT", "/data/visual-models"))


def ensure_yunet_model(
    root: Path | None = None,
    downloader: Callable[[str], bytes] | None = None,
) -> Path:
    """Return a verified local YuNet model, downloading only the allowlisted asset."""
    destination_root = root or visual_model_root()
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / YUNET_MODEL_FILENAME
    if destination.exists() and _sha256(destination) == YUNET_MODEL_SHA256:
        return destination

    if downloader is None:
        def downloader(url: str) -> bytes:
            request = Request(url, headers={"User-Agent": "Titan-Clipper-Visual-Analysis/1.0"})
            with urlopen(request, timeout=45) as response:  # nosec B310: URL is fixed above.
                payload = response.read(YUNET_MODEL_MAX_BYTES + 1)
            return payload

    payload = downloader(YUNET_MODEL_URL)
    if len(payload) > YUNET_MODEL_MAX_BYTES:
        raise VisualAnalysisConfigurationError("The approved face-detection model exceeded its expected size limit.")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != YUNET_MODEL_SHA256:
        raise VisualAnalysisConfigurationError("The approved face-detection model failed SHA-256 verification.")

    with tempfile.NamedTemporaryFile(dir=destination_root, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(destination)
    return destination


class YuNetVisualAnalyzer:
    provider_name = "opencv_yunet"

    def __init__(self, model_path: Path | None = None):
        try:
            import cv2  # type: ignore
        except ImportError as error:
            raise VisualAnalysisConfigurationError(
                "Visual analysis requires OpenCV. Install requirements-visual.txt in the API runtime."
            ) from error
        self.cv2 = cv2
        resolved_model = model_path or ensure_yunet_model()
        self.detector = cv2.FaceDetectorYN.create(
            str(resolved_model),
            "",
            (320, 320),
            score_threshold=0.82,
            nms_threshold=0.30,
            top_k=5000,
        )

    def detect_faces(self, frame) -> list[FaceBox]:
        height, width = frame.shape[:2]
        if not width or not height:
            return []
        self.detector.setInputSize((width, height))
        _, faces = self.detector.detect(frame)
        if faces is None:
            return []
        detected: list[FaceBox] = []
        for row in faces:
            x, y, face_width, face_height, *rest = [float(value) for value in row]
            confidence = rest[-1] if rest else 0.0
            if face_width <= 0 or face_height <= 0:
                continue
            detected.append(
                FaceBox(
                    x=max(0.0, min(1.0, x / width)),
                    y=max(0.0, min(1.0, y / height)),
                    width=max(0.0, min(1.0, face_width / width)),
                    height=max(0.0, min(1.0, face_height / height)),
                    confidence=max(0.0, min(1.0, confidence)),
                )
            )
        return detected

    def analyze_video(
        self,
        media_path: Path,
        start_seconds: float = 0.0,
        end_seconds: float | None = None,
        sample_hz: float = 2.0,
        shot_threshold: float = 0.42,
    ) -> VisualEditPlan:
        if sample_hz <= 0:
            raise ValueError("sample_hz must be positive")
        if not media_path.exists():
            raise FileNotFoundError(f"Media file not found for visual analysis: {media_path}")

        capture = self.cv2.VideoCapture(str(media_path))
        if not capture.isOpened():
            raise VisualAnalysisConfigurationError("OpenCV could not open the uploaded source for visual analysis.")
        duration = capture.get(self.cv2.CAP_PROP_FRAME_COUNT) / max(capture.get(self.cv2.CAP_PROP_FPS), 1.0)
        clip_start = max(0.0, start_seconds)
        clip_end = min(duration, end_seconds if end_seconds is not None else duration)
        if clip_end <= clip_start:
            capture.release()
            raise ValueError("Visual analysis window must have positive duration.")

        interval = 1.0 / sample_hz
        timestamp = clip_start
        observations: list[FaceObservation] = []
        cut_times: list[tuple[float, float]] = []
        previous_histogram = None
        last_cut_time = -99.0

        try:
            while timestamp <= clip_end + 0.0001:
                capture.set(self.cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
                ok, frame = capture.read()
                if not ok:
                    timestamp += interval
                    continue
                relative_time = timestamp - clip_start
                for face in self.detect_faces(frame):
                    observations.append(FaceObservation(relative_time, face))

                small = self.cv2.resize(frame, (160, 90))
                hsv = self.cv2.cvtColor(small, self.cv2.COLOR_BGR2HSV)
                histogram = self.cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
                self.cv2.normalize(histogram, histogram)
                if previous_histogram is not None:
                    difference = float(self.cv2.compareHist(previous_histogram, histogram, self.cv2.HISTCMP_BHATTACHARYYA))
                    if difference >= shot_threshold and relative_time - last_cut_time >= 1.0:
                        cut_times.append((relative_time, min(1.0, difference)))
                        last_cut_time = relative_time
                previous_histogram = histogram
                timestamp += interval
        finally:
            capture.release()

        plan = build_visual_edit_plan(clip_end - clip_start, observations, cut_times)
        if not observations:
            plan.warnings.append("YuNet did not detect a face in the selected window.")
        return plan


def get_visual_analyzer(provider_name: str | None = None) -> YuNetVisualAnalyzer:
    selected = (provider_name or os.getenv("VISUAL_ANALYSIS_PROVIDER", "")).strip().lower()
    if selected == "yunet":
        return YuNetVisualAnalyzer()
    if not selected or selected in {"unconfigured", "disabled", "none"}:
        raise VisualAnalysisConfigurationError(
            "Visual analysis is not configured. Set VISUAL_ANALYSIS_PROVIDER=yunet and install requirements-visual.txt."
        )
    raise VisualAnalysisConfigurationError(f"Unsupported visual-analysis provider: {selected}")
