"""Deterministic planning primitives for Titan's visual editing layer.

The module is deliberately model-agnostic: a detection provider supplies face boxes, this
module converts them into stable face tracks, shot-aware focus decisions, and bounded crop
keyframes. The renderer must only advertise ``speaker_focus`` when a plan produced here is
present and passes validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Iterable


@dataclass(frozen=True)
class FaceBox:
    """Normalized face bounds in source-frame coordinates."""

    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)


@dataclass(frozen=True)
class FaceObservation:
    timestamp: float
    face: FaceBox
    track_id: str | None = None


@dataclass(frozen=True)
class ShotBoundary:
    start_seconds: float
    end_seconds: float
    confidence: float
    reason: str


@dataclass(frozen=True)
class CropKeyframe:
    timestamp: float
    center_x: float
    center_y: float
    zoom: float
    track_id: str | None
    shot_index: int


@dataclass
class VisualEditPlan:
    version: str
    source_duration_seconds: float
    shots: list[ShotBoundary]
    keyframes: list[CropKeyframe]
    primary_track_ids: dict[int, str | None]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "source_duration_seconds": self.source_duration_seconds,
            "shots": [shot.__dict__ for shot in self.shots],
            "keyframes": [keyframe.__dict__ for keyframe in self.keyframes],
            "primary_track_ids": self.primary_track_ids,
            "warnings": self.warnings,
        }


class VisualPlanError(RuntimeError):
    pass


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def iou(a: FaceBox, b: FaceBox) -> float:
    left = max(a.x, b.x)
    top = max(a.y, b.y)
    right = min(a.x + a.width, b.x + b.width)
    bottom = min(a.y + a.height, b.y + b.height)
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    union = a.area + b.area - intersection
    return intersection / union if union else 0.0


def assign_face_tracks(
    observations: Iterable[FaceObservation],
    min_iou: float = 0.22,
    max_gap_seconds: float = 1.0,
) -> list[FaceObservation]:
    """Assign stable IDs with greedy IoU matching and time-gap protection."""
    ordered = sorted(observations, key=lambda item: item.timestamp)
    active: dict[str, FaceObservation] = {}
    output: list[FaceObservation] = []
    next_id = 1

    for observation in ordered:
        if observation.track_id:
            assigned = observation.track_id
        else:
            candidates = [
                (track_id, prior)
                for track_id, prior in active.items()
                if observation.timestamp - prior.timestamp <= max_gap_seconds
            ]
            candidates.sort(key=lambda candidate: iou(observation.face, candidate[1].face), reverse=True)
            assigned = None
            if candidates and iou(observation.face, candidates[0][1].face) >= min_iou:
                assigned = candidates[0][0]
            if assigned is None:
                assigned = f"face_{next_id}"
                next_id += 1

        tracked = FaceObservation(timestamp=observation.timestamp, face=observation.face, track_id=assigned)
        active[assigned] = tracked
        output.append(tracked)
    return output


def build_shots(
    source_duration_seconds: float,
    cut_times: Iterable[tuple[float, float]],
    minimum_shot_seconds: float = 1.0,
) -> list[ShotBoundary]:
    """Convert candidate cut moments to clean, non-chattery source shots."""
    valid_cuts = sorted(
        (clamp(time, 0.0, source_duration_seconds), clamp(confidence, 0.0, 1.0))
        for time, confidence in cut_times
        if minimum_shot_seconds < time < source_duration_seconds - minimum_shot_seconds
    )
    accepted: list[tuple[float, float]] = []
    for time, confidence in valid_cuts:
        if not accepted or time - accepted[-1][0] >= minimum_shot_seconds:
            accepted.append((time, confidence))
        elif confidence > accepted[-1][1]:
            accepted[-1] = (time, confidence)

    boundaries: list[ShotBoundary] = []
    start = 0.0
    for time, confidence in accepted:
        boundaries.append(ShotBoundary(start, time, confidence, "visual_cut"))
        start = time
    boundaries.append(ShotBoundary(start, source_duration_seconds, 1.0, "source_end"))
    return boundaries


def _shot_index_for_time(shots: list[ShotBoundary], timestamp: float) -> int:
    for index, shot in enumerate(shots):
        if shot.start_seconds <= timestamp <= shot.end_seconds:
            return index
    return max(0, len(shots) - 1)


def _candidate_score(observation: FaceObservation) -> float:
    center_distance = hypot(observation.face.center_x - 0.5, observation.face.center_y - 0.5)
    centrality = 1.0 - min(1.0, center_distance / 0.707)
    return observation.face.confidence * (0.78 * observation.face.area + 0.22 * centrality)


def choose_primary_tracks(
    tracked_observations: Iterable[FaceObservation],
    shots: list[ShotBoundary],
    switch_margin: float = 1.22,
) -> dict[int, str | None]:
    """Pick one stable visual subject per shot without flip-flopping frame to frame."""
    by_shot: dict[int, dict[str, float]] = {}
    for observation in tracked_observations:
        if not observation.track_id:
            continue
        shot_index = _shot_index_for_time(shots, observation.timestamp)
        bucket = by_shot.setdefault(shot_index, {})
        bucket[observation.track_id] = bucket.get(observation.track_id, 0.0) + _candidate_score(observation)

    primary: dict[int, str | None] = {}
    previous: str | None = None
    for shot_index in range(len(shots)):
        scores = by_shot.get(shot_index, {})
        if not scores:
            primary[shot_index] = previous
            continue
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        candidate, candidate_score = ranked[0]
        prior_score = scores.get(previous, 0.0) if previous else 0.0
        selected = candidate
        if previous and previous in scores and candidate != previous and candidate_score < prior_score * switch_margin:
            selected = previous
        primary[shot_index] = selected
        previous = selected
    return primary


def _average_face(observations: list[FaceObservation]) -> FaceBox:
    count = len(observations)
    return FaceBox(
        x=sum(item.face.x for item in observations) / count,
        y=sum(item.face.y for item in observations) / count,
        width=sum(item.face.width for item in observations) / count,
        height=sum(item.face.height for item in observations) / count,
        confidence=sum(item.face.confidence for item in observations) / count,
    )


def build_crop_keyframes(
    tracked_observations: Iterable[FaceObservation],
    shots: list[ShotBoundary],
    primary_track_ids: dict[int, str | None],
    max_pan_per_second: float = 0.18,
    minimum_zoom: float = 1.0,
    maximum_zoom: float = 1.55,
) -> list[CropKeyframe]:
    """Build bounded, shot-aware crop anchors."""
    grouped: dict[tuple[int, str], list[FaceObservation]] = {}
    for observation in tracked_observations:
        if not observation.track_id:
            continue
        shot_index = _shot_index_for_time(shots, observation.timestamp)
        grouped.setdefault((shot_index, observation.track_id), []).append(observation)

    keyframes: list[CropKeyframe] = []
    previous_x = 0.5
    previous_y = 0.5
    for shot_index, shot in enumerate(shots):
        selected = primary_track_ids.get(shot_index)
        observations = grouped.get((shot_index, selected), []) if selected else []
        if observations:
            face = _average_face(observations)
            target_x = clamp(face.center_x)
            target_y = clamp(face.center_y)
            face_scale = max(face.width, face.height)
            target_zoom = clamp(0.78 / max(face_scale, 0.01), minimum_zoom, maximum_zoom)
        else:
            target_x, target_y, target_zoom = previous_x, previous_y, minimum_zoom

        duration = max(0.01, shot.end_seconds - shot.start_seconds)
        allowed_distance = max_pan_per_second * duration
        distance = hypot(target_x - previous_x, target_y - previous_y)
        if distance > allowed_distance:
            ratio = allowed_distance / distance
            target_x = previous_x + (target_x - previous_x) * ratio
            target_y = previous_y + (target_y - previous_y) * ratio

        keyframes.append(CropKeyframe(shot.start_seconds, previous_x, previous_y, minimum_zoom, selected, shot_index))
        keyframes.append(CropKeyframe(shot.end_seconds, target_x, target_y, target_zoom, selected, shot_index))
        previous_x, previous_y = target_x, target_y
    return keyframes


def build_visual_edit_plan(
    source_duration_seconds: float,
    observations: Iterable[FaceObservation],
    cut_times: Iterable[tuple[float, float]],
) -> VisualEditPlan:
    if source_duration_seconds <= 0:
        raise VisualPlanError("Visual planning requires a positive source duration.")

    shots = build_shots(source_duration_seconds, cut_times)
    tracked = assign_face_tracks(observations)
    primary = choose_primary_tracks(tracked, shots)
    keyframes = build_crop_keyframes(tracked, shots, primary)
    warnings: list[str] = []
    if not tracked:
        warnings.append("No faces were detected; speaker-focused reframing is unavailable.")
    if not any(primary.values()):
        warnings.append("No stable primary visual subject could be selected.")
    return VisualEditPlan(
        version="titan_visual_v1",
        source_duration_seconds=source_duration_seconds,
        shots=shots,
        keyframes=keyframes,
        primary_track_ids=primary,
        warnings=warnings,
    )
