"""Shared helper so every module creates outward-action drafts the same way.
This is the single path into the Approval Inbox -- no module writes directly
to a 'sent' state, which is what makes 'AI draft != outward action' provable."""
from .models import ApprovalItem
from .workspace_ctx import WorkspaceContext


def create_draft(ctx: WorkspaceContext, type_: str, source_module: str, target: str,
                  content: str, reason: str, ref_table: str = "", ref_id: int = None) -> ApprovalItem:
    item = ApprovalItem(
        type=type_,
        source_module=source_module,
        target=target,
        draft_content=content,
        reason=reason,
        status="PENDING_APPROVAL",
        ref_table=ref_table,
        ref_id=ref_id,
    )
    ctx.add(item)
    ctx.db.commit()
    ctx.db.refresh(item)
    return item
