from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from typing import Literal
from uuid import uuid4

from database import create_db_and_tables, get_db
from export_downloads import router as export_download_router
from link_importer import import_direct_media_url
from local_storage import save_uploaded_file
from media_probe import probe_media
from mock_transcript import get_mock_segments, word_timings_for_segment
from models import CandidateClip, EditTimeline, ExportRecord, Job, Project, Source, Transcript, TranscriptSegment, TranscriptWord
from render_scaffold import create_placeholder_export_files
from render_service import render_export_with_best_source


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="BPC Clipper API", version="0.11.0", lifespan=lifespan)
app.include_router(export_download_router, prefix="/api/v1")


class ProjectCreate(BaseModel):
    name: str
    source_type: Literal["upload", "link", "unknown"] = "unknown"
    rights_confirmed: bool


class LinkSourceCreate(BaseModel):
    url: HttpUrl
    rights_confirmed: bool
    title: str | None = None


class EditTimelineCreate(BaseModel):
    hook_text: str | None = None
    caption_preset: str = "bpc_clean_editorial"
    crop_mode: str = "speaker_focus"


class EditTimelineUpdate(BaseModel):
    start_seconds: float | None = None
    end_seconds: float | None = None
    hook_text: str | None = None
    caption_preset: str | None = None
    crop_mode: str | None = None
    status: str | None = None
    settings: dict | None = None


class ExportCreate(BaseModel):
    format: str = "vertical_1080x1920"
    include_burned_captions: bool = True
    include_srt: bool = True
    include_vtt: bool = True
    include_metadata: bool = True


def serialize_project(project: Project) -> dict:
    return {"project_id": project.id, "name": project.name, "source_type": project.source_type, "rights_confirmed": project.rights_confirmed, "status": project.status}


def serialize_source(source: Source) -> dict:
    return {"source_id": source.id, "project_id": source.project_id, "source_type": source.source_type, "original_filename": source.original_filename, "original_url": source.original_url, "title": source.title, "storage_path": source.storage_path, "duration_seconds": source.duration_seconds, "width": source.width, "height": source.height, "fps": source.fps, "video_codec": source.video_codec, "audio_codec": source.audio_codec, "validation_status": source.validation_status, "validation_message": source.validation_message, "rights_confirmed": source.rights_confirmed}


def serialize_job(job: Job) -> dict:
    return {"job_id": job.id, "project_id": job.project_id, "source_id": job.source_id, "stage": job.stage, "progress": job.progress, "message": job.message, "status": job.status, "source_url": job.source_url, "error": job.error_message}


def serialize_segment(segment: TranscriptSegment) -> dict:
    return {"segment_id": segment.id, "speaker_label": segment.speaker_label, "start_seconds": segment.start_seconds, "end_seconds": segment.end_seconds, "text": segment.text, "confidence": segment.confidence}


def serialize_transcript(transcript: Transcript) -> dict:
    return {"transcript_id": transcript.id, "project_id": transcript.project_id, "source_id": transcript.source_id, "language": transcript.language, "provider": transcript.provider, "confidence": transcript.confidence, "segments": [serialize_segment(segment) for segment in transcript.segments]}


def serialize_candidate(candidate: CandidateClip) -> dict:
    return {"candidate_id": candidate.id, "project_id": candidate.project_id, "start_seconds": candidate.start_seconds, "end_seconds": candidate.end_seconds, "title": candidate.title, "excerpt": candidate.excerpt, "score": candidate.score, "category": candidate.category, "explanation": candidate.explanation, "risk_flags": candidate.risk_flags or [], "status": candidate.status}


def serialize_edit_timeline(edit: EditTimeline) -> dict:
    return {"edit_id": edit.id, "project_id": edit.project_id, "candidate_clip_id": edit.candidate_clip_id, "start_seconds": edit.start_seconds, "end_seconds": edit.end_seconds, "hook_text": edit.hook_text, "caption_preset": edit.caption_preset, "crop_mode": edit.crop_mode, "status": edit.status, "settings": edit.settings or {}}


def serialize_export(export: ExportRecord) -> dict:
    return {"export_id": export.id, "project_id": export.project_id, "edit_timeline_id": export.edit_timeline_id, "status": export.status, "format": export.format, "include_burned_captions": export.include_burned_captions, "include_srt": export.include_srt, "include_vtt": export.include_vtt, "include_metadata": export.include_metadata, "video_path": export.video_path, "srt_path": export.srt_path, "vtt_path": export.vtt_path, "metadata_path": export.metadata_path, "download_urls": {"video": f"/api/v1/exports/{export.id}/files/video" if export.video_path else None, "srt": f"/api/v1/exports/{export.id}/files/srt" if export.srt_path else None, "vtt": f"/api/v1/exports/{export.id}/files/vtt" if export.vtt_path else None, "metadata": f"/api/v1/exports/{export.id}/files/metadata" if export.metadata_path else None}, "error": export.error_message}


def make_job_for_source(project_id: str, source: Source, message: str, status: str = "queued") -> Job:
    return Job(id=str(uuid4()), project_id=project_id, source_id=source.id, stage="queued" if status == "queued" else "importing_source", progress=0 if status == "queued" else 30, message=message, status=status, source_url=source.original_url)


def create_mock_transcript_for_source(db: Session, project_id: str, source_id: str) -> Transcript:
    existing = db.query(Transcript).filter(Transcript.project_id == project_id, Transcript.source_id == source_id).first()
    if existing:
        return existing
    transcript = Transcript(id=str(uuid4()), project_id=project_id, source_id=source_id, language="en", provider="mock", confidence=1.0)
    db.add(transcript); db.flush()
    for mock_segment in get_mock_segments():
        segment = TranscriptSegment(id=str(uuid4()), transcript_id=transcript.id, speaker_label=mock_segment.speaker_label, start_seconds=mock_segment.start_seconds, end_seconds=mock_segment.end_seconds, text=mock_segment.text, confidence=mock_segment.confidence)
        db.add(segment); db.flush()
        for word in word_timings_for_segment(mock_segment):
            db.add(TranscriptWord(id=str(uuid4()), segment_id=segment.id, start_seconds=word["start_seconds"], end_seconds=word["end_seconds"], text=word["text"], confidence=word["confidence"]))
    db.commit(); db.refresh(transcript)
    return transcript


def choose_primary_source(db: Session, project_id: str) -> Source | None:
    return db.query(Source).filter(Source.project_id == project_id).order_by(Source.created_at.desc()).first()


def segment_score(segment: TranscriptSegment) -> int:
    text = segment.text.lower(); score = 60
    if "let me ask" in text or "here is" in text: score += 12
    if "business" in text or "ownership" in text or "retention" in text: score += 10
    if "viral" in text or "truth" in text or "mistake" in text: score += 8
    duration = segment.end_seconds - segment.start_seconds
    if 20 <= duration <= 55: score += 8
    return min(score, 95)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "bpc-clipper-api", "persistence": "database"}


@app.post("/api/v1/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(id=str(uuid4()), name=payload.name, source_type=payload.source_type, rights_confirmed=payload.rights_confirmed, status="created")
    db.add(project); db.commit(); db.refresh(project)
    return serialize_project(project)


@app.get("/api/v1/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None: raise HTTPException(status_code=404, detail="project_not_found")
    return serialize_project(project)


@app.get("/api/v1/projects/{project_id}/sources")
def list_sources(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None: raise HTTPException(status_code=404, detail="project_not_found")
    sources = db.query(Source).filter(Source.project_id == project_id).all()
    return {"project_id": project_id, "sources": [serialize_source(source) for source in sources]}


@app.post("/api/v1/projects/{project_id}/sources/upload")
async def create_upload_source(project_id: str, rights_confirmed: bool = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not rights_confirmed: raise HTTPException(status_code=400, detail="rights_confirmation_required")
    project = db.get(Project, project_id)
    if project is None: raise HTTPException(status_code=404, detail="project_not_found")
    saved_path = await save_uploaded_file(project_id, file); probe = probe_media(str(saved_path))
    source = Source(id=str(uuid4()), project_id=project_id, source_type="upload", original_filename=file.filename, title=file.filename, storage_path=str(saved_path), duration_seconds=probe.duration_seconds, width=probe.width, height=probe.height, fps=probe.fps, video_codec=probe.video_codec, audio_codec=probe.audio_codec, validation_status=probe.validation_status, validation_message=probe.validation_message, rights_confirmed=rights_confirmed)
    db.add(source); db.flush()
    job = Job(id=str(uuid4()), project_id=project_id, source_id=source.id, stage="probing_media" if probe.validation_status != "valid" else "queued", progress=25 if probe.validation_status != "valid" else 0, message=probe.validation_message if probe.validation_status != "valid" else "Upload source queued for processing", status="needs_attention" if probe.validation_status != "valid" else "queued")
    project.source_type = "upload"; db.add(job); db.commit(); db.refresh(source); db.refresh(job)
    return {"project_id": project_id, "source": serialize_source(source), "job_id": job.id, "status": job.status}


@app.post("/api/v1/projects/{project_id}/sources/link")
def create_link_source(project_id: str, payload: LinkSourceCreate, db: Session = Depends(get_db)):
    if not payload.rights_confirmed: raise HTTPException(status_code=400, detail="rights_confirmation_required")
    project = db.get(Project, project_id)
    if project is None: raise HTTPException(status_code=404, detail="project_not_found")
    downloaded_path, import_status, import_message = import_direct_media_url(project_id, str(payload.url)); probe = probe_media(str(downloaded_path)) if downloaded_path else None
    source = Source(id=str(uuid4()), project_id=project_id, source_type="link", original_url=str(payload.url), title=payload.title, storage_path=str(downloaded_path) if downloaded_path else None, duration_seconds=probe.duration_seconds if probe else None, width=probe.width if probe else None, height=probe.height if probe else None, fps=probe.fps if probe else None, video_codec=probe.video_codec if probe else None, audio_codec=probe.audio_codec if probe else None, validation_status=probe.validation_status if probe else import_status, validation_message=probe.validation_message if probe else import_message, rights_confirmed=payload.rights_confirmed)
    db.add(source); db.flush(); source_is_ready = source.validation_status == "valid"
    job = make_job_for_source(project_id=project_id, source=source, message="Direct link imported and queued for processing" if source_is_ready else source.validation_message, status="queued" if source_is_ready else "needs_attention")
    project.source_type = "link"; db.add(job); db.commit(); db.refresh(source); db.refresh(job)
    return {"project_id": project_id, "source": serialize_source(source), "job_id": job.id, "status": job.status}


@app.get("/api/v1/sources/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None: raise HTTPException(status_code=404, detail="source_not_found")
    return serialize_source(source)


@app.post("/api/v1/sources/{source_id}/transcript/mock")
def generate_mock_transcript(source_id: str, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None: raise HTTPException(status_code=404, detail="source_not_found")
    transcript = create_mock_transcript_for_source(db, source.project_id, source.id)
    return serialize_transcript(transcript)


@app.get("/api/v1/projects/{project_id}/transcript")
def get_project_transcript(project_id: str, db: Session = Depends(get_db)):
    transcript = db.query(Transcript).filter(Transcript.project_id == project_id).order_by(Transcript.created_at.desc()).first()
    if transcript is None:
        source = choose_primary_source(db, project_id)
        if source is None: raise HTTPException(status_code=404, detail="source_not_found")
        transcript = create_mock_transcript_for_source(db, project_id, source.id)
    return serialize_transcript(transcript)


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None: raise HTTPException(status_code=404, detail="job_not_found")
    return serialize_job(job)


@app.post("/api/v1/projects/{project_id}/candidates/generate")
def generate_candidates(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None: raise HTTPException(status_code=404, detail="project_not_found")
    existing = db.query(CandidateClip).filter(CandidateClip.project_id == project_id).all()
    if existing: return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in existing]}
    transcript = db.query(Transcript).filter(Transcript.project_id == project_id).order_by(Transcript.created_at.desc()).first()
    if transcript is None:
        source = choose_primary_source(db, project_id)
        if source is None: raise HTTPException(status_code=404, detail="source_not_found")
        transcript = create_mock_transcript_for_source(db, project_id, source.id)
    candidates = []
    for segment in transcript.segments:
        score = segment_score(segment); category = "debate_heat" if "ask" in segment.text.lower() or "mistake" in segment.text.lower() else "story_mode"
        candidates.append(CandidateClip(id=str(uuid4()), project_id=project_id, start_seconds=segment.start_seconds, end_seconds=segment.end_seconds, title=segment.text[:70].rstrip() + "...", excerpt=segment.text, score=score, category=category, explanation=f"Transcript-based candidate with score {score}. Strong enough for Producer Mode review.", risk_flags=[]))
    candidates = sorted(candidates, key=lambda item: item.score, reverse=True)[:10]
    db.add_all(candidates); db.commit()
    for candidate in candidates: db.refresh(candidate)
    return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in candidates]}


@app.get("/api/v1/projects/{project_id}/candidates")
def list_candidates(project_id: str, db: Session = Depends(get_db)):
    candidates = db.query(CandidateClip).filter(CandidateClip.project_id == project_id).order_by(CandidateClip.score.desc()).all()
    return {"project_id": project_id, "candidates": [serialize_candidate(item) for item in candidates]}


@app.post("/api/v1/candidates/{candidate_id}/edits")
def create_edit_timeline(candidate_id: str, payload: EditTimelineCreate, db: Session = Depends(get_db)):
    candidate = db.get(CandidateClip, candidate_id)
    if candidate is None: raise HTTPException(status_code=404, detail="candidate_not_found")
    existing = db.query(EditTimeline).filter(EditTimeline.candidate_clip_id == candidate_id).first()
    if existing: return serialize_edit_timeline(existing)
    edit = EditTimeline(id=str(uuid4()), project_id=candidate.project_id, candidate_clip_id=candidate.id, start_seconds=candidate.start_seconds, end_seconds=candidate.end_seconds, hook_text=payload.hook_text or candidate.title, caption_preset=payload.caption_preset, crop_mode=payload.crop_mode, status="draft", settings={"source": "candidate_approval"})
    candidate.status = "approved"; db.add(edit); db.commit(); db.refresh(edit)
    return serialize_edit_timeline(edit)


@app.get("/api/v1/projects/{project_id}/edits")
def list_project_edits(project_id: str, db: Session = Depends(get_db)):
    edits = db.query(EditTimeline).filter(EditTimeline.project_id == project_id).order_by(EditTimeline.created_at.desc()).all()
    return {"project_id": project_id, "edits": [serialize_edit_timeline(edit) for edit in edits]}


@app.get("/api/v1/edits/{edit_id}")
def get_edit_timeline(edit_id: str, db: Session = Depends(get_db)):
    edit = db.get(EditTimeline, edit_id)
    if edit is None: raise HTTPException(status_code=404, detail="edit_not_found")
    return serialize_edit_timeline(edit)


@app.patch("/api/v1/edits/{edit_id}")
def update_edit_timeline(edit_id: str, payload: EditTimelineUpdate, db: Session = Depends(get_db)):
    edit = db.get(EditTimeline, edit_id)
    if edit is None: raise HTTPException(status_code=404, detail="edit_not_found")
    if payload.start_seconds is not None: edit.start_seconds = payload.start_seconds
    if payload.end_seconds is not None: edit.end_seconds = payload.end_seconds
    if payload.hook_text is not None: edit.hook_text = payload.hook_text
    if payload.caption_preset is not None: edit.caption_preset = payload.caption_preset
    if payload.crop_mode is not None: edit.crop_mode = payload.crop_mode
    if payload.status is not None: edit.status = payload.status
    if payload.settings is not None: edit.settings = payload.settings
    db.commit(); db.refresh(edit)
    return serialize_edit_timeline(edit)


@app.post("/api/v1/edits/{edit_id}/exports")
def create_export(edit_id: str, payload: ExportCreate, db: Session = Depends(get_db)):
    edit = db.get(EditTimeline, edit_id)
    if edit is None: raise HTTPException(status_code=404, detail="edit_not_found")
    export = ExportRecord(id=str(uuid4()), project_id=edit.project_id, edit_timeline_id=edit.id, status="queued", format=payload.format, include_burned_captions=payload.include_burned_captions, include_srt=payload.include_srt, include_vtt=payload.include_vtt, include_metadata=payload.include_metadata)
    db.add(export); db.flush()
    try:
        paths = create_placeholder_export_files(export, edit)
        export.video_path = paths["video_path"]; export.srt_path = paths["srt_path"]; export.vtt_path = paths["vtt_path"]; export.metadata_path = paths["metadata_path"]
        export.status = "placeholder_complete"; edit.status = "export_placeholder_complete"
    except Exception as error:
        export.status = "failed"; export.error_message = str(error); edit.status = "export_failed"
    db.commit(); db.refresh(export)
    return serialize_export(export)


@app.post("/api/v1/exports/{export_id}/render")
def render_export(export_id: str, db: Session = Depends(get_db)):
    export = db.get(ExportRecord, export_id)
    if export is None: raise HTTPException(status_code=404, detail="export_not_found")
    edit = db.get(EditTimeline, export.edit_timeline_id)
    if edit is None: raise HTTPException(status_code=404, detail="edit_not_found")
    export.status = "rendering"; edit.status = "rendering"; db.commit()
    try:
        paths = render_export_with_best_source(db, export, edit)
        export.video_path = paths["video_path"]; export.srt_path = paths["srt_path"]; export.vtt_path = paths["vtt_path"]; export.metadata_path = paths["metadata_path"]
        export.status = "render_complete" if str(export.video_path).endswith(".mp4") else "placeholder_complete"
        edit.status = "render_complete" if export.status == "render_complete" else "export_placeholder_complete"
    except Exception as error:
        export.status = "failed"; export.error_message = str(error); edit.status = "export_failed"
    db.commit(); db.refresh(export)
    return serialize_export(export)


@app.get("/api/v1/projects/{project_id}/exports")
def list_project_exports(project_id: str, db: Session = Depends(get_db)):
    exports = db.query(ExportRecord).filter(ExportRecord.project_id == project_id).order_by(ExportRecord.created_at.desc()).all()
    return {"project_id": project_id, "exports": [serialize_export(export) for export in exports]}


@app.get("/api/v1/exports/{export_id}")
def get_export(export_id: str, db: Session = Depends(get_db)):
    export = db.get(ExportRecord, export_id)
    if export is None: raise HTTPException(status_code=404, detail="export_not_found")
    return serialize_export(export)


@app.get("/api/v1/presets")
def list_presets():
    return {"presets": [{"name": "BPC Clean Editorial", "pace": "balanced"}, {"name": "BPC Debate Heat", "pace": "quick"}, {"name": "BPC Story Mode", "pace": "smooth"}, {"name": "BPC Commentary Reaction", "pace": "flexible"}]}
