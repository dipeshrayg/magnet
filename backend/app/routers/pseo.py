from fastapi import APIRouter, Depends

from ..growth_logic import generate_pseo_pages
from ..models import Page, ProductProfile
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["pseo"])


@router.get("/workspaces/{workspace_id}/pages")
def list_pages(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(Page).all())


@router.get("/workspaces/{workspace_id}/pages/{slug}")
def get_page(slug: str, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_dict(ctx.query(Page).filter(Page.slug == slug).first())


@router.post("/workspaces/{workspace_id}/pages/generate")
def generate_pages(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    profile = ctx.query(ProductProfile).first()
    ctx.query(Page).delete()
    pages_data = generate_pseo_pages({
        "name": profile.name, "use_cases": profile.use_cases,
        "value_props": profile.value_props, "pain_points": profile.pain_points,
    })
    for pd in pages_data:
        ctx.add(Page(**pd))
    ctx.db.commit()
    return {"pages_created": len(pages_data)}
