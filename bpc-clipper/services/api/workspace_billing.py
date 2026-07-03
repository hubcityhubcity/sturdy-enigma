from __future__ import annotations

from calendar import monthrange
from datetime import datetime
from hashlib import sha256
import os
import secrets
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import ExportRecord, Source
from workspace_models import Workspace, WorkspaceProject

WORKSPACE_HEADER = "X-Titan-Workspace-Key"
PLANS = {
    "free": {
        "name": "Free",
        "source_minutes_per_month": 30,
        "exports_per_month": 5,
        "features": ["Titan Brain scoring", "Vertical exports", "SRT and VTT captions", "Publishing packages"],
    },
    "creator": {
        "name": "Creator",
        "source_minutes_per_month": 600,
        "exports_per_month": 120,
        "features": ["Everything in Free", "Higher monthly processing limits", "Priority render queue ready"],
    },
    "studio": {
        "name": "Studio",
        "source_minutes_per_month": 3000,
        "exports_per_month": 600,
        "features": ["Everything in Creator", "Team and billing integration ready", "High-volume workflow ready"],
    },
}


def hash_access_key(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def generate_access_key() -> str:
    return f"titan_{secrets.token_urlsafe(24)}"


def cycle_start(now: datetime | None = None) -> datetime:
    value = now or datetime.utcnow()
    return datetime(value.year, value.month, 1)


def cycle_end(now: datetime | None = None) -> datetime:
    value = now or datetime.utcnow()
    last_day = monthrange(value.year, value.month)[1]
    return datetime(value.year, value.month, last_day, 23, 59, 59)


def plan_for(code: str) -> dict:
    return PLANS.get(code, PLANS["free"])


def serialize_workspace(workspace: Workspace) -> dict:
    plan = plan_for(workspace.plan_code)
    return {
        "workspace_id": workspace.id,
        "name": workspace.name,
        "plan_code": workspace.plan_code,
        "plan_name": plan["name"],
        "limits": {
            "source_minutes_per_month": plan["source_minutes_per_month"],
            "exports_per_month": plan["exports_per_month"],
        },
        "features": plan["features"],
    }


def create_workspace(db: Session, name: str) -> tuple[Workspace, str]:
    access_key = generate_access_key()
    workspace = Workspace(
        id=str(uuid4()),
        name=(name or "My Titan Workspace").strip()[:160] or "My Titan Workspace",
        plan_code="free",
        access_key_hash=hash_access_key(access_key),
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace, access_key


def development_workspace(db: Session) -> Workspace:
    key = os.getenv("TITAN_DEVELOPMENT_WORKSPACE_KEY", "local-development")
    existing = db.query(Workspace).filter(Workspace.access_key_hash == hash_access_key(key)).first()
    if existing:
        return existing
    workspace = Workspace(id=str(uuid4()), name="Local Development Workspace", plan_code="studio", access_key_hash=hash_access_key(key))
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def resolve_workspace(db: Session, access_key: str | None) -> Workspace:
    if access_key:
        workspace = db.query(Workspace).filter(Workspace.access_key_hash == hash_access_key(access_key.strip())).first()
        if workspace:
            return workspace
        raise HTTPException(status_code=401, detail="invalid_workspace_key")
    if os.getenv("TITAN_REQUIRE_WORKSPACE_KEY", "false").lower() == "true":
        raise HTTPException(status_code=401, detail="workspace_key_required")
    return development_workspace(db)


def claim_project(db: Session, workspace: Workspace, project_id: str) -> None:
    existing = db.query(WorkspaceProject).filter(WorkspaceProject.project_id == project_id).first()
    if existing and existing.workspace_id != workspace.id:
        raise HTTPException(status_code=403, detail="project_not_available_for_workspace")
    if not existing:
        db.add(WorkspaceProject(workspace_id=workspace.id, project_id=project_id))


def require_project(db: Session, workspace: Workspace, project_id: str) -> None:
    link = db.query(WorkspaceProject).filter(WorkspaceProject.workspace_id == workspace.id, WorkspaceProject.project_id == project_id).first()
    if link is None:
        raise HTTPException(status_code=404, detail="project_not_found")


def workspace_project_ids(db: Session, workspace: Workspace) -> list[str]:
    return [row.project_id for row in db.query(WorkspaceProject).filter(WorkspaceProject.workspace_id == workspace.id).all()]


def usage_snapshot(db: Session, workspace: Workspace) -> dict:
    start = cycle_start()
    project_ids = workspace_project_ids(db, workspace)
    plan = plan_for(workspace.plan_code)
    if not project_ids:
        source_seconds = 0.0
        export_count = 0
    else:
        source_seconds = float(db.query(func.coalesce(func.sum(Source.duration_seconds), 0.0)).filter(Source.project_id.in_(project_ids), Source.created_at >= start).scalar() or 0.0)
        export_count = int(db.query(func.count(ExportRecord.id)).filter(ExportRecord.project_id.in_(project_ids), ExportRecord.created_at >= start).scalar() or 0)
    source_minutes = round(source_seconds / 60, 2)
    return {
        "cycle_started_at": start.isoformat(),
        "source_minutes_used": source_minutes,
        "source_minutes_limit": plan["source_minutes_per_month"],
        "source_minutes_remaining": max(0, round(plan["source_minutes_per_month"] - source_minutes, 2)),
        "exports_used": export_count,
        "exports_limit": plan["exports_per_month"],
        "exports_remaining": max(0, plan["exports_per_month"] - export_count),
    }


def enforce_source_quota(db: Session, workspace: Workspace, incoming_seconds: float | None) -> None:
    if not incoming_seconds or incoming_seconds <= 0:
        return
    usage = usage_snapshot(db, workspace)
    projected = usage["source_minutes_used"] + (incoming_seconds / 60)
    if projected > usage["source_minutes_limit"]:
        raise HTTPException(status_code=402, detail={"code": "source_minutes_limit_reached", "usage": usage})


def enforce_export_quota(db: Session, workspace: Workspace) -> None:
    usage = usage_snapshot(db, workspace)
    if usage["exports_used"] >= usage["exports_limit"]:
        raise HTTPException(status_code=402, detail={"code": "exports_limit_reached", "usage": usage})
