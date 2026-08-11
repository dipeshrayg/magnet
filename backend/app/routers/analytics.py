from fastapi import APIRouter, Depends

from ..growth_logic import funnel_from_events, roi_by_module
from ..models import GrowthEvent
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["analytics"])


@router.get("/workspaces/{workspace_id}/analytics/funnel")
def funnel(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    events = ctx.query(GrowthEvent).all()
    return funnel_from_events(events)


@router.get("/workspaces/{workspace_id}/analytics/roi")
def roi(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    events = ctx.query(GrowthEvent).all()
    return roi_by_module(events)


@router.get("/workspaces/{workspace_id}/analytics/report")
def weekly_report(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    events = ctx.query(GrowthEvent).all()
    funnel_data = funnel_from_events(events)
    roi_data = roi_by_module(events)
    top_module = max(roi_data.items(), key=lambda kv: kv[1]["revenue"], default=(None, None))
    return {
        "workspace": ctx.workspace.name,
        "funnel": funnel_data,
        "roi_by_module": roi_data,
        "top_module": top_module[0],
        "summary": (
            f"{ctx.workspace.name}: {funnel_data['counts']['visit']} visits -> "
            f"{funnel_data['counts']['revenue']} revenue events, "
            f"${funnel_data['revenue']} tracked revenue this period."
        ),
    }
