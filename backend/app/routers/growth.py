from fastapi import APIRouter, Depends

from ..ai import get_provider
from ..approval_lib import create_draft
from ..config import live_sources_enabled
from ..connectors import LIVE_SOURCES
from ..growth_logic import score_post
from ..models import CommunityPost, Competitor, CompetitorEvent, GrowthEvent, Lead, ProductProfile, Review, VocItem
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["growth"])


def _ingest_live_sources(ctx: WorkspaceContext, keywords: list) -> int:
    """Best-effort: pulls fresh posts from opt-in live connectors and inserts
    any not already seen (deduped by url). A source erroring never blocks the
    others or the scan itself -- see connectors.py."""
    existing_urls = {u for (u,) in ctx.query(CommunityPost).with_entities(CommunityPost.url).all()}
    inserted = 0
    for source in LIVE_SOURCES:
        try:
            for post in source.fetch(keywords):
                if not post["text"] or post["url"] in existing_urls:
                    continue
                ctx.add(CommunityPost(
                    source=post["source"], author=post["author"], text=post["text"], url=post["url"],
                ))
                existing_urls.add(post["url"])
                inserted += 1
        except Exception:
            continue  # one failed source must not crash the pipeline
    if inserted:
        ctx.db.commit()
    return inserted


# ---------- M2 Lead Radar ----------

@router.get("/workspaces/{workspace_id}/leads")
def list_leads(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    leads = ctx.query(Lead).order_by(Lead.opportunity_score.desc()).all()
    return to_list(leads)


@router.post("/workspaces/{workspace_id}/leads/scan")
def scan_leads(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """Re-scores every community post against this workspace's ICP/keywords and
    (re)creates leads. High-opportunity leads get a helpful reply draft routed
    to the Approval Inbox -- never posted automatically."""
    profile = ctx.query(ProductProfile).first()
    keywords = profile.keywords if profile else []
    pain_points = profile.pain_points if profile else []
    live_ingested = _ingest_live_sources(ctx, keywords) if live_sources_enabled() else 0
    posts = ctx.query(CommunityPost).all()
    ctx.query(Lead).delete()
    created = []
    for post in posts:
        scores = score_post(post.text, keywords, pain_points, post.id)
        post.pain_score, post.intent_score = scores["pain_score"], scores["intent_score"]
        lead = Lead(
            post_id=post.id, name=post.author, source=post.source,
            evidence=post.text[:280], **scores,
        )
        ctx.add(lead)
        created.append(lead)
    ctx.db.commit()
    provider = get_provider()
    high_intent = [lead for lead in created if lead.opportunity_score >= 0.45]
    for lead in high_intent[:10]:
        draft = provider.draft(
            "You are a helpful community member, never salesy or spammy.",
            f"Write one genuinely useful reply (no pitch) to this post, mentioning "
            f"the product only if directly relevant: {lead.evidence}",
        )
        create_draft(ctx, "community_reply", "M2 Lead Radar", lead.source, draft,
                     reason=f"High-intent lead (opportunity={lead.opportunity_score})",
                     ref_table="leads", ref_id=lead.id)
        ctx.add(GrowthEvent(stage="lead", source_module="M2 Lead Radar", attribution_source=lead.source))
    ctx.db.commit()
    return {
        "scanned": len(posts), "leads_created": len(created), "drafts_created": len(high_intent[:10]),
        "live_posts_ingested": live_ingested,
    }


# ---------- M3 Competitor Watch ----------

@router.get("/workspaces/{workspace_id}/competitors")
def list_competitors(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(Competitor).all())


@router.get("/workspaces/{workspace_id}/competitor-events")
def list_competitor_events(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(CompetitorEvent).order_by(CompetitorEvent.detected_at.desc()).all())


@router.post("/workspaces/{workspace_id}/competitors/scan")
def scan_competitors(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """Fixture-driven: turns high-severity competitor events into switch-opportunity
    outreach drafts. All outreach stays approval-gated."""
    provider = get_provider()
    events = ctx.query(CompetitorEvent).filter(CompetitorEvent.severity == "high").all()
    drafts = 0
    for ev in events:
        comp = ctx.get_or_404(Competitor, ev.competitor_id)
        draft = provider.draft(
            "You write short, respectful switch-opportunity outreach. No trashing competitors.",
            f"{comp.name} customers may be affected by: {ev.description}. Draft a short, "
            f"helpful outreach note offering our product as an alternative.",
        )
        create_draft(ctx, "outreach_email", "M3 Competitor Watch", comp.name, draft,
                     reason=f"Competitor event: {ev.type} ({ev.severity})",
                     ref_table="competitor_events", ref_id=ev.id)
        drafts += 1
    return {"high_severity_events": len(events), "drafts_created": drafts}


# ---------- M5 Reputation ----------

@router.get("/workspaces/{workspace_id}/reviews")
def list_reviews(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(Review).all())


@router.post("/workspaces/{workspace_id}/reputation/scan")
def scan_reputation(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    provider = get_provider()
    negative = ctx.query(Review).filter(Review.subject == "own", Review.rating <= 2.5).all()
    drafts = 0
    for r in negative:
        draft = provider.draft(
            "You write empathetic, non-defensive review responses.",
            f"Draft a response to this review (rating {r.rating}/5): {r.text}",
        )
        create_draft(ctx, "review_response", "M5 Reputation", r.author or "reviewer", draft,
                     reason=f"Negative review, rating={r.rating}", ref_table="reviews", ref_id=r.id)
        drafts += 1
    return {"negative_reviews": len(negative), "drafts_created": drafts}


# ---------- M10 Voice of Customer ----------

@router.get("/workspaces/{workspace_id}/voc")
def list_voc(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(VocItem).order_by(VocItem.priority.desc()).all())


@router.put("/workspaces/{workspace_id}/voc/{voc_id}/status")
def update_voc_status(voc_id: int, body: dict, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    item = ctx.get_or_404(VocItem, voc_id)
    item.roadmap_status = body.get("status", item.roadmap_status)
    ctx.db.commit()
    return to_dict(item)
