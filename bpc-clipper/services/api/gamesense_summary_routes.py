from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from gamesense_summary import summarize_gamesense_events
from models import GameSenseEvent, Project


router = APIRouter(tags=["gamesense"])


@router.get("/projects/{project_id}/gamesense/summary")
def get_gamesense_summary(project_id: str, source_id: str | None = None, db: Session = Depends(get_db)):
    """Return transparent evidence counts and strongest signals for a GameSense project."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    query = db.query(GameSenseEvent).filter(GameSenseEvent.project_id == project_id)
    if source_id:
        query = query.filter(GameSenseEvent.source_id == source_id)
    events = query.order_by(GameSenseEvent.start_seconds.asc()).all()

    return {
        "project_id": project_id,
        "source_id": source_id,
        **summarize_gamesense_events(events),
    }
