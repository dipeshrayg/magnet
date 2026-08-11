from app.db import SessionLocal
from app.growth_logic import funnel_from_events, roi_by_module
from app.models import ContentPiece, GrowthEvent, Lead, Page, ProductProfile, Workspace
from app.seed import run_seed


def test_seed_creates_three_distinct_products(client):
    names = run_seed()
    assert len(names) == 3

    db = SessionLocal()
    try:
        workspaces = db.query(Workspace).all()
        assert len(workspaces) == 3

        profiles = {ws.id: db.query(ProductProfile).filter_by(workspace_id=ws.id).first() for ws in workspaces}
        keyword_sets = [set(p.keywords) for p in profiles.values()]
        # No two workspaces should have identical keyword sets.
        assert keyword_sets[0] != keyword_sets[1] != keyword_sets[2] != keyword_sets[0]

        for ws in workspaces:
            leads = db.query(Lead).filter_by(workspace_id=ws.id).all()
            pages = db.query(Page).filter_by(workspace_id=ws.id).all()
            assert len(leads) > 0
            assert len(pages) >= 100, f"{ws.name} should have 100+ pSEO pages, got {len(pages)}"

        lead_evidence = [
            {lead.evidence for lead in db.query(Lead).filter_by(workspace_id=ws.id).all()}
            for ws in workspaces
        ]
        assert lead_evidence[0] != lead_evidence[1]

        for ws in workspaces:
            events = db.query(GrowthEvent).filter_by(workspace_id=ws.id).all()
            funnel = funnel_from_events(events)
            assert funnel["counts"]["visit"] > 0
            roi = roi_by_module(events)
            assert len(roi) > 0
    finally:
        db.close()


def test_content_differs_by_workspace(client):
    run_seed()
    db = SessionLocal()
    try:
        workspaces = db.query(Workspace).all()
        content_bodies = [
            {c.body for c in db.query(ContentPiece).filter_by(workspace_id=ws.id).all()}
            for ws in workspaces
        ]
        assert content_bodies[0].isdisjoint(content_bodies[1])
    finally:
        db.close()


def test_no_outward_action_without_approval_across_seeded_data(client):
    from app.models import ApprovalItem
    run_seed()
    db = SessionLocal()
    try:
        sent_without_approval = db.query(ApprovalItem).filter(
            ApprovalItem.status.in_(["SENT", "EXPORTED"]), ApprovalItem.decided_by == ""
        ).count()
        assert sent_without_approval == 0
    finally:
        db.close()
