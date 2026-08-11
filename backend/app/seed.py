"""Seeds three demo workspaces (three different product categories) with
fixture data: users, community posts, planted high-intent leads, competitors,
reviews, content, VOC items, referrals, pSEO pages, and growth events.
Deterministic: uses random.Random(fixed_seed) per workspace, never the global
random module, so re-running produces identical data."""
import glob
import os
import random
from datetime import timedelta

import yaml

from .db import Base, SessionLocal, engine
from .growth_logic import derive_icp_from_profile, generate_pseo_pages, hook_and_virality, score_post
from .models import (
    ICP,
    AppUser,
    CommunityPost,
    Competitor,
    CompetitorEvent,
    ContentPiece,
    Event,
    GrowthEvent,
    Lead,
    Page,
    ProductProfile,
    Referral,
    Review,
    VocItem,
    Workspace,
    now,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")

NOISE_POSTS = [
    "Just wanted to share my Monday routine, coffee first always.",
    "What's your favorite podcast for long commutes?",
    "Anyone going to the conference next month?",
    "How do you organize your notes app, mine is chaos.",
    "Looking for book recommendations for summer.",
    "Our team is hiring, DM me if interested.",
    "What's a good budget laptop for students right now?",
    "Unpopular opinion: pineapple belongs on pizza.",
    "Does anyone else procrastinate by cleaning their desk?",
    "Recommend me a good sci-fi show to binge.",
]
SOURCES = ["reddit", "forum", "hn", "producthunt"]
FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Jamie", "Drew", "Avery",
               "Priya", "Wei", "Fatima", "Diego", "Noor", "Liam", "Zara", "Omar", "Elena", "Kofi"]
LAST_NAMES = ["Chen", "Patel", "Garcia", "Kim", "Nguyen", "Smith", "Okafor", "Rossi", "Muller", "Silva"]


def load_profile(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    data.setdefault("competitors", [])
    return data


def gen_users(rng: random.Random, n=50):
    users = []
    start = now() - timedelta(days=90)
    for i in range(n):
        fn, ln = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        signup = start + timedelta(days=rng.randint(0, 85), hours=rng.randint(0, 23))
        activated = signup + timedelta(hours=rng.randint(1, 48)) if rng.random() < 0.65 else None
        users.append(AppUser(
            name=f"{fn} {ln}", email=f"{fn.lower()}.{ln.lower()}{i}@example.com",
            role=rng.choice(["admin", "member", "owner"]), plan=rng.choice(["trial", "starter", "pro"]),
            signup_at=signup, activated_at=activated,
        ))
    return users


def gen_posts(rng: random.Random, profile: dict, n_total=200, n_high_intent=30):
    posts = []
    intent_templates = [
        "Anyone have recommendations for {kw}? Tired of {pain}.",
        "Is there a good alternative worth trying? We're dealing with {pain} constantly.",
        "Looking for a tool to fix {pain} -- does {kw} actually work well?",
        "What do you use for {kw}? Current setup means {pain} every week.",
        "Ready to switch tools because of {pain}. Any {kw} recommendations?",
    ]
    start = now() - timedelta(days=60)
    for i in range(n_high_intent):
        pain = rng.choice(profile["pain_points"])
        kw = rng.choice(profile["keywords"])
        text = rng.choice(intent_templates).format(kw=kw, pain=pain)
        posts.append(CommunityPost(
            source=rng.choice(SOURCES), author=f"user{rng.randint(1000,9999)}", text=text,
            url=f"https://example.com/thread/{rng.randint(10000,99999)}",
            posted_at=start + timedelta(days=rng.randint(0, 59)),
        ))
    for i in range(n_total - n_high_intent):
        text = rng.choice(NOISE_POSTS)
        posts.append(CommunityPost(
            source=rng.choice(SOURCES), author=f"user{rng.randint(1000,9999)}", text=text,
            url=f"https://example.com/thread/{rng.randint(10000,99999)}",
            posted_at=start + timedelta(days=rng.randint(0, 59)),
        ))
    return posts


def gen_reviews(rng: random.Random, profile: dict, n=40):
    positive = [
        f"{profile['name']} saved us hours every week. {rng.choice(profile['value_props'])}",
        f"Switched to {profile['name']} and never looked back.",
        "Support team is fast and the product just works.",
    ]
    negative = [
        f"Ran into {rng.choice(profile['pain_points'])} even after switching, disappointed.",
        "Pricing jumped without warning, considering alternatives.",
        "Onboarding was confusing and support took days to respond.",
    ]
    reviews = []
    for i in range(n):
        is_own = rng.random() < 0.75
        is_negative = rng.random() < 0.25
        rating = rng.uniform(1.0, 2.5) if is_negative else rng.uniform(3.5, 5.0)
        text = rng.choice(negative if is_negative else positive)
        subject = "own" if is_own else rng.choice(profile["competitors"]) if profile["competitors"] else "own"
        reviews.append(Review(
            source=rng.choice(["g2", "trustpilot", "app_store"]), author=f"reviewer{i}",
            rating=round(rating, 1), text=text, sentiment="negative" if is_negative else "positive",
            subject=subject, posted_at=now() - timedelta(days=rng.randint(0, 120)),
        ))
    return reviews


def seed_workspace(db, fixture_path: str, seed_offset: int):
    rng = random.Random(1000 + seed_offset)
    profile_data = load_profile(fixture_path)
    slug = profile_data["name"].lower().replace(" ", "-")
    ws = Workspace(name=profile_data["name"], slug=slug)
    db.add(ws)
    db.flush()

    profile = ProductProfile(workspace_id=ws.id, **profile_data)
    db.add(profile)
    icp_data = derive_icp_from_profile(profile_data)
    db.add(ICP(workspace_id=ws.id, **icp_data))

    users = gen_users(rng)
    for u in users:
        u.workspace_id = ws.id
        db.add(u)
    db.flush()
    for u in users:
        db.add(Event(workspace_id=ws.id, user_id=u.id, type="signup", created_at=u.signup_at))
        if u.activated_at:
            db.add(Event(workspace_id=ws.id, user_id=u.id, type="activated", created_at=u.activated_at))

    posts = gen_posts(rng, profile_data)
    for p in posts:
        p.workspace_id = ws.id
        db.add(p)
    db.flush()

    leads_created = 0
    for p in posts:
        scores = score_post(p.text, profile_data["keywords"], profile_data["pain_points"], p.id)
        p.pain_score, p.intent_score = scores["pain_score"], scores["intent_score"]
        if scores["opportunity_score"] >= 0.3:
            db.add(Lead(workspace_id=ws.id, post_id=p.id, name=p.author, source=p.source,
                        evidence=p.text[:280], status="new", **scores))
            leads_created += 1

    competitors = []
    for name in (profile_data["competitors"] or ["Competitor A", "Competitor B", "Competitor C"])[:3]:
        c = Competitor(workspace_id=ws.id, name=name, url=f"https://{name.lower().replace(' ','')}.example.com")
        db.add(c)
        competitors.append(c)
    db.flush()
    severities = ["high", "medium", "low"]
    event_types = ["outage", "price_increase", "bad_review_wave"]
    for i, c in enumerate(competitors):
        db.add(CompetitorEvent(
            workspace_id=ws.id, competitor_id=c.id, type=event_types[i % len(event_types)],
            description=f"{c.name} reported {event_types[i % len(event_types)].replace('_',' ')} affecting customers.",
            severity=severities[i % len(severities)],
        ))

    for r in gen_reviews(rng, profile_data):
        r.workspace_id = ws.id
        db.add(r)

    for idea in profile_data["pain_points"][:3]:
        for channel in ("twitter", "linkedin"):
            text = f"How we help teams stop losing time to {idea}. {rng.choice(profile_data['value_props'])}"
            scores = hook_and_virality(text)
            db.add(ContentPiece(workspace_id=ws.id, idea=idea, channel=channel, body=text, status="draft", **scores))

    roadmap_states = ["requested", "planned", "in_progress", "shipped"]
    for i, pain in enumerate(profile_data["pain_points"]):
        db.add(VocItem(
            workspace_id=ws.id, cluster=pain[:40], text=f"Users keep asking for a fix to: {pain}",
            source=rng.choice(["review", "community", "support"]), priority=round(rng.uniform(0.3, 0.95), 2),
            evidence=f"Mentioned in {rng.randint(3,25)} reviews/posts",
            roadmap_status=roadmap_states[i % len(roadmap_states)],
        ))

    for i, u in enumerate(users[:8]):
        db.add(Referral(workspace_id=ws.id, code=f"{slug[:4]}{u.id}", referrer_user_id=u.id,
                        referred_email=f"friend{i}@example.com" if i % 2 == 0 else "", position=i + 1))

    for pd in generate_pseo_pages(profile_data):
        pd["workspace_id"] = ws.id
        db.add(Page(**pd))

    visits = rng.randint(400, 900)
    leads_n = leads_created + rng.randint(10, 40)
    signups = int(leads_n * rng.uniform(0.3, 0.5))
    activations = int(signups * rng.uniform(0.4, 0.7))
    revenue_events = int(activations * rng.uniform(0.2, 0.45))
    modules = ["M2 Lead Radar", "M4 pSEO Factory", "M6 Free Tool", "M11 Referrals", "organic"]
    for stage, count in (("visit", visits), ("lead", leads_n), ("signup", signups),
                         ("activation", activations), ("revenue", revenue_events)):
        for _ in range(count):
            value = round(rng.uniform(20, 200), 2) if stage == "revenue" else 0.0
            db.add(GrowthEvent(workspace_id=ws.id, stage=stage, value=value,
                               source_module=rng.choice(modules), attribution_source=rng.choice(modules)))

    return ws


def run_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        fixture_files = sorted(glob.glob(os.path.join(FIXTURES_DIR, "product_*.yaml")))
        results = []
        for i, path in enumerate(fixture_files):
            ws = seed_workspace(db, path, i)
            db.commit()
            results.append(ws.name)
        return results
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeded workspaces:", run_seed())
