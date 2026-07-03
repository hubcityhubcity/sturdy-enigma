import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bpc_clipper.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    from models import CandidateClip, EditTimeline, ExportRecord, GameSenseEvent, Job, Project, Source, Transcript, TranscriptSegment, TranscriptWord  # noqa: F401
    from workspace_models import Workspace, WorkspaceProject  # noqa: F401
    Base.metadata.create_all(bind=engine)
