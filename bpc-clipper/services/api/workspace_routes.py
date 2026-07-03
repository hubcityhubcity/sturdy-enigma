from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from workspace_billing import PLANS, WORKSPACE_HEADER, create_workspace, resolve_workspace, serialize_workspace, usage_snapshot

router = APIRouter(tags=["workspaces"])


class WorkspaceBootstrap(BaseModel):
    name: str = Field(default="My Titan Workspace", min_length=1, max_length=160)


def current_workspace(
    x_titan_workspace_key: str | None = Header(default=None, alias=WORKSPACE_HEADER),
    db: Session = Depends(get_db),
):
    return resolve_workspace(db, x_titan_workspace_key)


@router.get("/plans")
def list_plans():
    return {"plans": [{"code": code, **plan} for code, plan in PLANS.items()], "billing_status": "payment_processor_not_connected"}


@router.post("/workspaces/bootstrap")
def bootstrap_workspace(payload: WorkspaceBootstrap, db: Session = Depends(get_db)):
    workspace, access_key = create_workspace(db, payload.name)
    return {"workspace": serialize_workspace(workspace), "usage": usage_snapshot(db, workspace), "access_key": access_key}


@router.get("/workspaces/me")
def get_current_workspace(workspace=Depends(current_workspace), db: Session = Depends(get_db)):
    return {"workspace": serialize_workspace(workspace), "usage": usage_snapshot(db, workspace)}
