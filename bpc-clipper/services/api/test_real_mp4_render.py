import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import CandidateClip, EditTimeline, ExportRecord, Project, Source
from render_service import render_export_with_best_source


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for real MP4 smoke test")
class RealMp4RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_real_media_source_renders_a_playable_vertical_mp4(self):
        source_path = self.root / "source.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
            "-t", "3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(source_path),
        ], check=True, capture_output=True, text=True)

        db = self.Session()
        project = Project(id="project-1", name="Real render", source_type="upload", rights_confirmed=True, status="created")
        source = Source(id="source-1", project_id=project.id, source_type="upload", original_filename="source.mp4", title="source.mp4", storage_path=str(source_path), duration_seconds=3.0, width=1280, height=720, fps=30.0, video_codec="h264", audio_codec="aac", validation_status="valid", validation_message="ready", rights_confirmed=True)
        candidate = CandidateClip(id="candidate-1", project_id=project.id, source_id=source.id, start_seconds=0.0, end_seconds=2.0, title="Real moment", excerpt="Real moment", score=80, category="high_retention", explanation="Test", score_breakdown={}, risk_flags=[])
        edit = EditTimeline(id="edit-1", project_id=project.id, candidate_clip_id=candidate.id, start_seconds=0.0, end_seconds=2.0, hook_text="Real moment", caption_preset="bpc_clean_editorial", crop_mode="speaker_focus", status="ready_to_render", settings={})
        export = ExportRecord(id="export-1", project_id=project.id, edit_timeline_id=edit.id, status="ready_to_render", format="vertical_1080x1920", include_burned_captions=False, include_srt=True, include_vtt=True, include_metadata=True)
        db.add_all([project, source, candidate, edit, export])
        db.commit()

        paths = render_export_with_best_source(db, export, edit)
        video_path = Path(paths["video_path"])
        self.assertEqual(video_path.suffix.lower(), ".mp4")
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 0)
        self.assertTrue(Path(paths["srt_path"]).exists())
        self.assertTrue(Path(paths["vtt_path"]).exists())
        self.assertTrue(Path(paths["metadata_path"]).exists())
        db.close()


if __name__ == "__main__":
    unittest.main()
