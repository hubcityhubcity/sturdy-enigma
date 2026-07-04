import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import CandidateClip, EditTimeline, ExportRecord, Job, Project
import render_worker


class RenderWorkerTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def seed_render_job(self, source_url: str = "export:export-1"):
        db = self.Session()
        project = Project(id="project-1", name="Render test", source_type="upload", rights_confirmed=True, status="created")
        candidate = CandidateClip(
            id="candidate-1",
            project_id=project.id,
            source_id=None,
            start_seconds=0,
            end_seconds=10,
            title="Test moment",
            excerpt="Test moment excerpt",
            score=80,
            category="high_retention",
            explanation="Test score",
            score_breakdown={},
            risk_flags=[],
        )
        edit = EditTimeline(
            id="edit-1",
            project_id=project.id,
            candidate_clip_id=candidate.id,
            start_seconds=0,
            end_seconds=10,
            hook_text="Test moment",
            caption_preset="bpc_clean_editorial",
            crop_mode="speaker_focus",
            status="queued_for_render",
            settings={},
        )
        export = ExportRecord(
            id="export-1",
            project_id=project.id,
            edit_timeline_id=edit.id,
            status="queued_for_render",
            format="vertical_1080x1920",
            include_burned_captions=True,
            include_srt=True,
            include_vtt=True,
            include_metadata=True,
        )
        job = Job(
            id="job-1",
            project_id=project.id,
            source_id=None,
            stage="render_export",
            progress=0,
            message="Render export queued",
            status="queued",
            source_url=source_url,
        )
        db.add_all([project, candidate, edit, export, job])
        db.commit()
        db.close()

    def test_worker_completes_queued_render_job(self):
        self.seed_render_job()
        paths = {
            "video_path": "/data/storage/exports/project-1/export-1/clip.mp4",
            "srt_path": "/data/storage/exports/project-1/export-1/captions.srt",
            "vtt_path": "/data/storage/exports/project-1/export-1/captions.vtt",
            "metadata_path": "/data/storage/exports/project-1/export-1/metadata.json",
        }
        with patch.object(render_worker, "SessionLocal", side_effect=lambda: self.Session()), patch.object(render_worker, "render_export_with_best_source", return_value=paths):
            self.assertTrue(render_worker.process_one_render_job())

        db = self.Session()
        job = db.get(Job, "job-1")
        export = db.get(ExportRecord, "export-1")
        edit = db.get(EditTimeline, "edit-1")
        self.assertEqual(job.status, "complete")
        self.assertEqual(job.progress, 100)
        self.assertEqual(export.status, "render_complete")
        self.assertEqual(edit.status, "render_complete")
        self.assertEqual(export.video_path, paths["video_path"])
        db.close()

    def test_worker_marks_invalid_export_reference_as_failed(self):
        self.seed_render_job(source_url="export:missing-export")
        with patch.object(render_worker, "SessionLocal", side_effect=lambda: self.Session()):
            self.assertTrue(render_worker.process_one_render_job())

        db = self.Session()
        job = db.get(Job, "job-1")
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_message, "export_not_found")
        db.close()


if __name__ == "__main__":
    unittest.main()
