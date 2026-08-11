from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..ai import get_provider
from ..approval_lib import create_draft
from ..growth_logic import hook_and_virality
from ..models import (
    AppUser,
    ContentPiece,
    FreeToolLead,
    GrowthEvent,
    Lead,
    LifecycleMessage,
    OutreachMessage,
    ProductProfile,
)
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["content"])

CHANNELS = ["twitter", "linkedin", "newsletter", "video_script"]


# ---------- M7 Content Studio ----------

class ContentIdeaRequest(BaseModel):
    idea: str


@router.get("/workspaces/{workspace_id}/content")
def list_content(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(ContentPiece).order_by(ContentPiece.created_at.desc()).all())


@router.post("/workspaces/{workspace_id}/content/generate")
def generate_content(body: ContentIdeaRequest, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    profile = ctx.query(ProductProfile).first()
    provider = get_provider()
    positioning = profile.positioning if profile else ""
    created = []
    for ch in CHANNELS:
        body_text = provider.draft(
            f"You write {ch} copy. Product positioning: {positioning}",
            f"Write a {ch} post about: {body.idea}",
        )
        scores = hook_and_virality(body_text)
        piece = ContentPiece(idea=body.idea, channel=ch, body=body_text, status="draft", **scores)
        ctx.add(piece)
        created.append(piece)
    # A/B copy variants for the strongest channel-agnostic hook
    for variant in ("A", "B"):
        variant_text = provider.draft("You write short ad copy variants.", f"{body.idea} (variant {variant})")
        scores = hook_and_virality(variant_text)
        piece = ContentPiece(idea=body.idea, channel=f"ab_variant_{variant}", body=variant_text,
                             status="draft", **scores)
        ctx.add(piece)
        created.append(piece)
    # Case study
    case_text = provider.draft(
        "You write short customer case studies.",
        f"Write a brief case study showing how {profile.name if profile else 'the product'} solved: {body.idea}",
    )
    case_scores = hook_and_virality(case_text)
    case_piece = ContentPiece(idea=body.idea, channel="case_study", body=case_text, status="draft", **case_scores)
    ctx.add(case_piece)
    created.append(case_piece)
    ctx.db.commit()
    return to_list(created)


@router.post("/workspaces/{workspace_id}/content/{content_id}/schedule")
def schedule_content(content_id: int, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """Export-only scheduling: creates an approval-gated export action, never posts."""
    piece = ctx.get_or_404(ContentPiece, content_id)
    item = create_draft(ctx, "social_post", "M7 Content Studio", piece.channel, piece.body,
                        reason="Scheduled for export via Content Studio", ref_table="content_pieces", ref_id=piece.id)
    return to_dict(item)


# ---------- M8 Outreach ----------

@router.get("/workspaces/{workspace_id}/outreach")
def list_outreach(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(OutreachMessage).all())


@router.post("/workspaces/{workspace_id}/outreach/{lead_id}/generate")
def generate_outreach(lead_id: int, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    lead = ctx.get_or_404(Lead, lead_id)
    profile = ctx.query(ProductProfile).first()
    provider = get_provider()
    steps = [
        ("Quick question", "personalized first line + soft opener"),
        ("Following up", "value-prop reminder with one concrete use case"),
        ("Last note + unsubscribe", "final nudge, must include unsubscribe copy"),
    ]
    created = []
    for i, (subject, instructions) in enumerate(steps, start=1):
        body = provider.draft(
            f"You write concise, non-pushy outreach. Product: {profile.name if profile else ''}. "
            f"Positioning: {profile.positioning if profile else ''}",
            f"Step {i}/{len(steps)} ({instructions}) to someone who posted: {lead.evidence}",
        )
        if i == len(steps) and "unsubscribe" not in body.lower():
            body += "\n\nReply STOP to unsubscribe."
        msg = OutreachMessage(lead_id=lead.id, step=i, subject=subject, body=body, status="draft")
        ctx.add(msg)
        created.append(msg)
    ctx.db.commit()
    first = created[0]
    item = create_draft(ctx, "outreach_email", "M8 Outreach", lead.name or lead.source, first.body,
                        reason="Step 1 of generated sequence", ref_table="outreach_messages", ref_id=first.id)
    return {"sequence": to_list(created), "approval_item": to_dict(item)}


# ---------- M9 Lifecycle ----------

@router.get("/workspaces/{workspace_id}/lifecycle")
def list_lifecycle(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(LifecycleMessage).all())


@router.post("/workspaces/{workspace_id}/lifecycle/scan")
def scan_lifecycle(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """Finds users with no activation event and drafts rescue/activation messages."""
    provider = get_provider()
    stalled = ctx.query(AppUser).filter(AppUser.activated_at.is_(None)).all()
    created = []
    for u in stalled[:15]:
        kind = "activation"
        body = provider.draft(
            "You write short, friendly lifecycle emails.",
            f"Write a 3-sentence email helping {u.name} activate their account (never activated since signup).",
        )
        msg = LifecycleMessage(user_id=u.id, kind=kind, body=body, status="draft")
        ctx.add(msg)
        ctx.db.flush()
        create_draft(ctx, "outreach_email", "M9 Lifecycle", u.email, body,
                    reason="Stalled signup, never activated", ref_table="lifecycle_messages", ref_id=msg.id)
        created.append(msg)
    ctx.db.commit()
    return {"stalled_users": len(stalled), "drafts_created": len(created)}


# ---------- M6 Free Tool ----------

class FreeToolRequest(BaseModel):
    email: str
    input_value: str


@router.post("/workspaces/{workspace_id}/freetool/run")
def run_free_tool(body: FreeToolRequest, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """A real, working ICP-fit calculator: scores the visitor's described situation
    against the workspace's own pain points/keywords (same deterministic engine
    Lead Radar uses), then captures the email as an attributed lead."""
    from ..growth_logic import score_post
    profile = ctx.query(ProductProfile).first()
    keywords = profile.keywords if profile else []
    pain_points = profile.pain_points if profile else []
    scores = score_post(body.input_value, keywords, pain_points, hash(body.email) % 100000)
    fit_pct = round(scores["opportunity_score"] * 100)
    summary = f"Fit score: {fit_pct}% -- top matched pain points: {', '.join(pain_points[:2]) or 'general'}"
    lead = FreeToolLead(email=body.email, input_value=body.input_value, result_summary=summary)
    ctx.add(lead)
    ctx.add(GrowthEvent(stage="lead", value=0, source_module="M6 Free Tool", attribution_source="free_tool"))
    ctx.db.commit()
    return {"fit_score": fit_pct, "summary": summary}


@router.get("/workspaces/{workspace_id}/freetool/leads")
def list_free_tool_leads(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(FreeToolLead).all())
