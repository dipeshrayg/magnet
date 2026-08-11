from app.growth_logic import dedupe_by_text, funnel_from_events, hook_and_virality, roi_by_module, score_post
from app.models import GrowthEvent


def test_intent_scoring_rewards_keyword_and_intent_matches():
    keywords = ["shift scheduling", "roster software"]
    pain_points = ["building the weekly roster by hand"]
    high = score_post("Looking for shift scheduling recommendations, tired of building the weekly roster by hand?",
                       keywords, pain_points, post_id=1)
    low = score_post("What's your favorite podcast for commutes?", keywords, pain_points, post_id=2)
    assert high["opportunity_score"] > low["opportunity_score"]


def test_dedupe_by_text_removes_duplicates():
    items = [{"text": "same post"}, {"text": "Same Post"}, {"text": "different"}]
    out = dedupe_by_text(items)
    assert len(out) == 2


def test_virality_score_bounded_and_responsive():
    plain = hook_and_virality("ok")
    rich = hook_and_virality("Did you know 9 out of 10 teams waste hours weekly? Here's the fix.")
    assert 0 <= plain["virality_score"] <= 1
    assert rich["virality_score"] > plain["virality_score"]


def test_funnel_conversion_rates():
    events = (
        [GrowthEvent(stage="visit") for _ in range(100)]
        + [GrowthEvent(stage="lead") for _ in range(20)]
        + [GrowthEvent(stage="signup") for _ in range(10)]
        + [GrowthEvent(stage="activation") for _ in range(5)]
        + [GrowthEvent(stage="revenue", value=50.0) for _ in range(2)]
    )
    funnel = funnel_from_events(events)
    assert funnel["counts"]["visit"] == 100
    assert funnel["conversion_rates"]["lead"] == 0.2
    assert funnel["revenue"] == 100.0


def test_roi_by_module_attributes_revenue():
    events = [
        GrowthEvent(stage="revenue", value=100.0, source_module="M2 Lead Radar"),
        GrowthEvent(stage="revenue", value=50.0, source_module="M11 Referrals"),
        GrowthEvent(stage="lead", source_module="M2 Lead Radar"),
    ]
    roi = roi_by_module(events)
    assert roi["M2 Lead Radar"]["revenue"] == 100.0
    assert roi["M11 Referrals"]["revenue"] == 50.0
    assert roi["M2 Lead Radar"]["leads"] == 1
