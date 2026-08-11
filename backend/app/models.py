from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text

from .db import Base


def now():
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=now)


class ProductProfile(Base):
    __tablename__ = "product_profiles"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    product_url = Column(String, default="")
    description = Column(Text, default="")
    value_props = Column(JSON, default=list)
    target_customers = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    use_cases = Column(JSON, default=list)
    pain_points = Column(JSON, default=list)
    competitors = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    positioning = Column(Text, default="")


class ICP(Base):
    __tablename__ = "icps"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    segment_name = Column(String, nullable=False)
    description = Column(Text, default="")
    firmographics = Column(JSON, default=dict)
    pain_points = Column(JSON, default=list)
    buying_triggers = Column(JSON, default=list)
    score_weights = Column(JSON, default=dict)


class AppUser(Base):
    __tablename__ = "app_users"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, default="")
    plan = Column(String, default="trial")
    signup_at = Column(DateTime, default=now)
    activated_at = Column(DateTime, nullable=True)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    type = Column(String, nullable=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)


class CommunityPost(Base):
    __tablename__ = "community_posts"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    source = Column(String, nullable=False)
    author = Column(String, default="")
    text = Column(Text, default="")
    url = Column(String, default="")
    posted_at = Column(DateTime, default=now)
    pain_score = Column(Float, default=0.0)
    intent_score = Column(Float, default=0.0)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=True)
    name = Column(String, default="")
    source = Column(String, default="")
    intent_score = Column(Float, default=0.0)
    pain_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    status = Column(String, default="new")
    evidence = Column(Text, default="")


class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, default="")
    notes = Column(Text, default="")


class CompetitorEvent(Base):
    __tablename__ = "competitor_events"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, default="")
    severity = Column(String, default="medium")
    detected_at = Column(DateTime, default=now)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    source = Column(String, default="")
    author = Column(String, default="")
    rating = Column(Float, default=3.0)
    text = Column(Text, default="")
    sentiment = Column(String, default="neutral")
    subject = Column(String, default="own")
    posted_at = Column(DateTime, default=now)


class ContentPiece(Base):
    __tablename__ = "content_pieces"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    idea = Column(Text, default="")
    channel = Column(String, nullable=False)
    body = Column(Text, default="")
    hook_score = Column(Float, default=0.0)
    virality_score = Column(Float, default=0.0)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=now)


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    step = Column(Integer, default=1)
    subject = Column(String, default="")
    body = Column(Text, default="")
    status = Column(String, default="draft")


class LifecycleMessage(Base):
    __tablename__ = "lifecycle_messages"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    kind = Column(String, default="activation")
    body = Column(Text, default="")
    status = Column(String, default="draft")


class VocItem(Base):
    __tablename__ = "voc_items"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    cluster = Column(String, nullable=False)
    text = Column(Text, default="")
    source = Column(String, default="")
    priority = Column(Float, default=0.0)
    evidence = Column(Text, default="")
    roadmap_status = Column(String, default="requested")


class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    slug = Column(String, nullable=False)
    title = Column(String, nullable=False)
    meta_description = Column(String, default="")
    body = Column(Text, default="")
    template = Column(String, default="")
    canonical_url = Column(String, default="")


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    referrer_user_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    referred_email = Column(String, default="")
    position = Column(Integer, default=0)
    reward = Column(String, default="")
    created_at = Column(DateTime, default=now)


class FreeToolLead(Base):
    __tablename__ = "free_tool_leads"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    email = Column(String, nullable=False)
    input_value = Column(String, default="")
    result_summary = Column(String, default="")
    created_at = Column(DateTime, default=now)


class ApprovalItem(Base):
    __tablename__ = "approval_items"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # e.g. outreach_email, community_reply, review_response, social_post
    source_module = Column(String, nullable=False)
    target = Column(String, default="")
    draft_content = Column(Text, default="")
    reason = Column(Text, default="")
    status = Column(String, default="PENDING_APPROVAL")
    ref_table = Column(String, default="")
    ref_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=now)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, default="")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    approval_item_id = Column(Integer, ForeignKey("approval_items.id"), nullable=True)
    actor = Column(String, default="operator")
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=now)


class GrowthEvent(Base):
    __tablename__ = "growth_events"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)  # visit, lead, signup, activation, revenue
    value = Column(Float, default=0.0)
    source_module = Column(String, default="")
    attribution_source = Column(String, default="")
    created_at = Column(DateTime, default=now)
