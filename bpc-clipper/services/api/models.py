from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="unknown")
    rights_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="project", cascade="all, delete-orphan")
    candidates = relationship("CandidateClip", back_populates="project", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_codec: Mapped[str | None] = mapped_column(String(80), nullable=True)
    audio_codec: Mapped[str | None] = mapped_column(String(80), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(80), default="pending")
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="sources")
    jobs = relationship("Job", back_populates="source")
    transcripts = relationship("Transcript", back_populates="source", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    stage: Mapped[str] = mapped_column(String(80), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="Queued")
    status: Mapped[str] = mapped_column(String(50), default="queued")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="jobs")
    source = relationship("Source", back_populates="jobs")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en")
    provider: Mapped[str] = mapped_column(String(80), default="mock")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="transcripts")
    source = relationship("Source", back_populates="transcripts")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"), nullable=False)
    speaker_label: Mapped[str] = mapped_column(String(80), default="Speaker 1")
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    transcript = relationship("Transcript", back_populates="segments")
    words = relationship("TranscriptWord", back_populates="segment", cascade="all, delete-orphan")


class TranscriptWord(Base):
    __tablename__ = "transcript_words"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    segment_id: Mapped[str] = mapped_column(ForeignKey("transcript_segments.id"), nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    corrected_text: Mapped[str | None] = mapped_column(String(120), nullable=True)

    segment = relationship("TranscriptSegment", back_populates="words")


class CandidateClip(Base):
    __tablename__ = "candidate_clips"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="candidates")
