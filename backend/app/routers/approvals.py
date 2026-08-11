from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..models import ApprovalItem, AuditLog
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["approvals"])


def _audit(ctx: WorkspaceContext, action: str, item: ApprovalItem, detail: str = ""):
    ctx.add(AuditLog(action=action, approval_item_id=item.id, actor="operator", detail=detail))


@router.get("/workspaces/{workspace_id}/approvals")
def list_approvals(status: str = None, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    q = ctx.query(ApprovalItem)
    if status:
        q = q.filter(ApprovalItem.status == status)
    return to_list(q.order_by(ApprovalItem.created_at.desc()).all())


class EditRequest(BaseModel):
    content: Optional[str] = None


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/edit")
def edit_approval(approval_id: int, body: EditRequest, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    item = ctx.get_or_404(ApprovalItem, approval_id)
    if item.status not in ("PENDING_APPROVAL",):
        raise HTTPException(400, "Only pending items can be edited")
    item.draft_content = body.content or item.draft_content
    ctx.db.commit()
    return to_dict(item)


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/approve")
def approve(approval_id: int, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    item = ctx.get_or_404(ApprovalItem, approval_id)
    if item.status != "PENDING_APPROVAL":
        raise HTTPException(400, f"Cannot approve item in status {item.status}")
    item.status = "APPROVED"
    item.decided_at = datetime.now(timezone.utc)
    item.decided_by = "operator"
    _audit(ctx, "approved", item)
    ctx.db.commit()
    return to_dict(item)


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/reject")
def reject(approval_id: int, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    item = ctx.get_or_404(ApprovalItem, approval_id)
    if item.status != "PENDING_APPROVAL":
        raise HTTPException(400, f"Cannot reject item in status {item.status}")
    item.status = "REJECTED"
    item.decided_at = datetime.now(timezone.utc)
    item.decided_by = "operator"
    _audit(ctx, "rejected", item)
    ctx.db.commit()
    return to_dict(item)


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/export")
def export_item(approval_id: int, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """The ONLY endpoint that moves an item to SENT/EXPORTED. Requires prior
    APPROVED status -- this is what makes 'no outward action without approval'
    an enforceable invariant rather than a UI convention."""
    item = ctx.get_or_404(ApprovalItem, approval_id)
    if item.status != "APPROVED":
        raise HTTPException(400, "Only approved items may be sent/exported")
    item.status = "SENT" if item.type in ("outreach_email", "community_reply", "review_response") else "EXPORTED"
    _audit(ctx, item.status.lower(), item, detail="Simulated external send/export (demo mode: no real network call)")
    ctx.db.commit()
    return to_dict(item)


@router.get("/workspaces/{workspace_id}/audit")
def list_audit(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(AuditLog).order_by(AuditLog.created_at.desc()).all())
