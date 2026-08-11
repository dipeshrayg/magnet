"""WorkspaceContext: the single choke point for workspace-scoped data access.

Every workspace-scoped query MUST go through here so isolation is enforced at
the data-access layer, not left to individual routers to remember.
"""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import Workspace


class WorkspaceContext:
    def __init__(self, db: Session, workspace: Workspace):
        self.db = db
        self.workspace = workspace
        self.workspace_id = workspace.id

    def query(self, model):
        """Return a query for a workspace-scoped model, pre-filtered by workspace_id.
        Raises if the model has no workspace_id column (i.e. isn't workspace-scoped)."""
        if not hasattr(model, "workspace_id"):
            raise TypeError(f"{model.__name__} is not workspace-scoped")
        return self.db.query(model).filter(model.workspace_id == self.workspace_id)

    def get_or_404(self, model, obj_id: int):
        obj = self.query(model).filter(model.id == obj_id).first()
        if obj is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} {obj_id} not found in this workspace")
        return obj

    def add(self, obj):
        """Stamp workspace_id and persist. Prevents cross-workspace writes by construction."""
        if hasattr(obj, "workspace_id"):
            obj.workspace_id = self.workspace_id
        self.db.add(obj)
        return obj


def get_workspace_ctx(workspace_id: int, db: Session = Depends(get_db)) -> WorkspaceContext:
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceContext(db, ws)
