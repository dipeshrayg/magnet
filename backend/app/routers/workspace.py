import re
import urllib.request
import urllib.robotparser
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..ai import is_live_mode
from ..db import get_db
from ..growth_logic import derive_icp_from_profile, derive_product_profile_from_text
from ..models import ICP, GrowthEvent, ProductProfile, Workspace
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["workspace"])

USER_AGENT = "MAGNETBot/1.0 (+https://github.com/magnet; growth-research; contact: demo@magnet.local)"


class ManualOnboardRequest(BaseModel):
    name: str
    raw_text: str


class UrlOnboardRequest(BaseModel):
    name: str
    url: str


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _fetch_public_page(url: str) -> str:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(USER_AGENT, url)
    except Exception:
        allowed = True  # no robots.txt reachable -> default allow for public pages
    if not allowed:
        raise HTTPException(status_code=403, detail="robots.txt disallows fetching this URL")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode(errors="ignore")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _create_workspace_from_profile(db: Session, profile_data: dict) -> Workspace:
    slug = _slugify(profile_data["name"])
    base_slug, i = slug, 2
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{base_slug}-{i}"
        i += 1
    ws = Workspace(name=profile_data["name"], slug=slug)
    db.add(ws)
    db.flush()
    profile = ProductProfile(workspace_id=ws.id, **profile_data)
    db.add(profile)
    icp_data = derive_icp_from_profile(profile_data)
    icp = ICP(workspace_id=ws.id, **icp_data)
    db.add(icp)
    db.commit()
    return ws


@router.get("/workspaces")
def list_workspaces(db: Session = Depends(get_db)):
    return to_list(db.query(Workspace).all())


@router.post("/workspaces/onboard/manual")
def onboard_manual(body: ManualOnboardRequest, db: Session = Depends(get_db)):
    """Path B: works with zero external calls and zero API keys."""
    profile_data = derive_product_profile_from_text(body.name, "", body.raw_text)
    ws = _create_workspace_from_profile(db, profile_data)
    return {"workspace": to_dict(ws), "mode": "manual"}


@router.post("/workspaces/onboard/url")
def onboard_url(body: UrlOnboardRequest, db: Session = Depends(get_db)):
    """Path A: fetches a public landing page (robots.txt respected) and derives the profile."""
    text = _fetch_public_page(body.url)
    profile_data = derive_product_profile_from_text(body.name, body.url, text)
    ws = _create_workspace_from_profile(db, profile_data)
    return {"workspace": to_dict(ws), "mode": "url"}


@router.get("/workspaces/{workspace_id}/profile")
def get_profile(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    profile = ctx.query(ProductProfile).first()
    return to_dict(profile)


@router.put("/workspaces/{workspace_id}/profile")
def update_profile(patch: dict, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    profile = ctx.query(ProductProfile).first()
    for k, v in patch.items():
        if hasattr(profile, k) and k not in ("id", "workspace_id"):
            setattr(profile, k, v)
    ctx.db.commit()
    return to_dict(profile)


@router.get("/workspaces/{workspace_id}/icp")
def get_icp(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(ICP).all())


@router.get("/system/mode")
def system_mode():
    return {"mode": "LIVE" if is_live_mode() else "DEMO"}


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db)):
    """Aggregates every workspace's funnel/ROI for cross-product comparison."""
    from ..growth_logic import funnel_from_events
    out = []
    for ws in db.query(Workspace).all():
        events = db.query(GrowthEvent).filter(GrowthEvent.workspace_id == ws.id).all()
        funnel = funnel_from_events(events)
        out.append({
            "workspace": to_dict(ws),
            "funnel": funnel,
        })
    return out
