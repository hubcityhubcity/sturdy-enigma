from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JobStage(str, Enum):
    QUEUED = "queued"
    VALIDATING_SOURCE = "validating_source"
    IMPORTING_SOURCE = "importing_source"
    PROBING_MEDIA = "probing_media"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    SEGMENTING = "segmenting"
    SCORING_CANDIDATES = "scoring_candidates"
    READY_FOR_REVIEW = "ready_for_review"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class JobUpdate:
    job_id: str
    stage: JobStage
    progress: int
    message: str
    error: Optional[str] = None


def process_import_job(job_id: str, source_url: Optional[str] = None) -> list[JobUpdate]:
    """Return the expected MVP job flow.

    This is a scaffold. The next implementation pass should connect it to Redis,
    storage, FFprobe, transcript generation, and candidate scoring.
    """
    return [
        JobUpdate(job_id, JobStage.VALIDATING_SOURCE, 5, "Validating source"),
        JobUpdate(job_id, JobStage.IMPORTING_SOURCE, 20, "Importing source media"),
        JobUpdate(job_id, JobStage.PROBING_MEDIA, 35, "Reading media metadata"),
        JobUpdate(job_id, JobStage.EXTRACTING_AUDIO, 45, "Extracting audio"),
        JobUpdate(job_id, JobStage.TRANSCRIBING, 60, "Creating transcript"),
        JobUpdate(job_id, JobStage.SEGMENTING, 75, "Finding candidate moments"),
        JobUpdate(job_id, JobStage.SCORING_CANDIDATES, 90, "Scoring candidates"),
        JobUpdate(job_id, JobStage.READY_FOR_REVIEW, 100, "Ready for Producer Mode"),
    ]


if __name__ == "__main__":
    for update in process_import_job("demo-job"):
        print(update)
