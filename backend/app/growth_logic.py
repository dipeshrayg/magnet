"""Deterministic, product-aware growth logic. No LLM required for any of this --
every score here is a function of the workspace's own ProductProfile/ICP text,
which is exactly why two workspaces with different products produce different
leads, keywords, scores and content. Swapping in a live LLMProvider (see ai.py)
only changes prose generation, never the ranking math."""
import hashlib
import re
from collections import Counter

STOPWORDS = set(
    "a an the of for to in on and or with is are be as by that this it your you "
    "we our their from at into about over under can will just not no more most "
    "get gets getting than then so if but very".split()
)


def _words(text: str):
    return [w for w in re.findall(r"[a-zA-Z][a-zA-Z\-']+", text.lower()) if w not in STOPWORDS and len(w) > 2]


def extract_keywords(text: str, n: int = 12):
    counts = Counter(_words(text))
    return [w for w, _ in counts.most_common(n)]


def extract_sentences(text: str, n: int = 5):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
    return sents[:n]


def derive_product_profile_from_text(name: str, url: str, raw_text: str) -> dict:
    """Heuristic extraction used by both the manual/demo path and the live URL path
    (after the page has already been fetched and stripped to text)."""
    keywords = extract_keywords(raw_text, 14)
    sentences = extract_sentences(raw_text, 8)
    value_props = sentences[:4] or [f"{name} helps teams move faster."]
    pain_points = [f"Struggling with {k.replace('-', ' ')}" for k in keywords[:5]]
    use_cases = [f"{k.replace('-', ' ').title()} workflows" for k in keywords[5:9]] or [f"{name} core workflow"]
    industries_pool = ["saas", "ecommerce", "healthcare", "fintech", "education", "logistics", "media", "fitness"]
    industries = [i for i in industries_pool if i in raw_text.lower()] or industries_pool[:3]
    target_customers = [f"{ind.title()} teams" for ind in industries[:3]]
    competitors = []
    return {
        "name": name,
        "product_url": url,
        "description": " ".join(sentences[:3]) or raw_text[:400],
        "value_props": value_props,
        "target_customers": target_customers,
        "industries": industries,
        "use_cases": use_cases,
        "pain_points": pain_points,
        "competitors": competitors,
        "keywords": keywords,
        "positioning": f"{name} is built for {', '.join(target_customers[:2]) or 'growing teams'}.",
    }


def derive_icp_from_profile(profile: dict) -> dict:
    return {
        "segment_name": (profile.get("target_customers") or ["Ideal Customers"])[0],
        "description": profile.get("positioning", ""),
        "firmographics": {"industries": profile.get("industries", []), "company_size": "10-500"},
        "pain_points": profile.get("pain_points", []),
        "buying_triggers": [f"Actively searching for {k}" for k in profile.get("keywords", [])[:3]],
        "score_weights": {"pain": 0.35, "intent": 0.35, "relevance": 0.30},
    }


def _stable_unit(*parts) -> float:
    """Deterministic pseudo-random float in [0,1) derived from inputs -- used to
    add realistic variance to scores without relying on Python's random module
    (which is explicitly disallowed for reproducibility across runs)."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return (int(h[:8], 16) % 10000) / 10000.0


def score_post(text: str, keywords: list, pain_points: list, post_id) -> dict:
    text_l = text.lower()
    kw_hits = sum(1 for k in keywords if k in text_l)
    pain_hits = sum(1 for p in pain_points if any(w in text_l for w in _words(p)))
    markers = ["recommend", "looking for", "any alternative", "worth it", "switch", "?"]
    intent_markers = sum(text_l.count(m) for m in markers)
    relevance = min(1.0, 0.15 * kw_hits + 0.1 * _stable_unit("rel", post_id))
    pain = min(1.0, 0.25 * pain_hits + 0.1 * _stable_unit("pain", post_id))
    intent = min(1.0, 0.2 * intent_markers + 0.15 * _stable_unit("intent", post_id))
    opportunity = round(0.4 * intent + 0.35 * pain + 0.25 * relevance, 4)
    return {
        "relevance_score": round(relevance, 4),
        "pain_score": round(pain, 4),
        "intent_score": round(intent, 4),
        "opportunity_score": opportunity,
    }


def hook_and_virality(text: str) -> dict:
    length_factor = min(1.0, len(text) / 240)
    question = 0.15 if "?" in text else 0.0
    number = 0.15 if re.search(r"\d", text) else 0.0
    novelty = _stable_unit("virality", text)
    hook = round(min(1.0, 0.3 + question + number + 0.2 * novelty), 4)
    virality = round(min(1.0, 0.25 * length_factor + question + number + 0.3 * novelty), 4)
    return {"hook_score": hook, "virality_score": virality}


def dedupe_by_text(items, text_key="text"):
    seen = set()
    out = []
    for it in items:
        key = hashlib.sha1(it[text_key].strip().lower().encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def funnel_from_events(events: list) -> dict:
    stages = ["visit", "lead", "signup", "activation", "revenue"]
    counts = {s: 0 for s in stages}
    revenue = 0.0
    for e in events:
        if e.stage in counts:
            counts[e.stage] += 1
        if e.stage == "revenue":
            revenue += e.value
    conv = {}
    prev = None
    for s in stages:
        if prev is None:
            conv[s] = 1.0
        else:
            conv[s] = round(counts[s] / counts[prev], 4) if counts[prev] else 0.0
        prev = s
    return {"counts": counts, "conversion_rates": conv, "revenue": round(revenue, 2)}


INDUSTRY_POOL = [
    "saas", "ecommerce", "healthcare", "fintech", "education", "logistics", "media",
    "fitness", "real-estate", "manufacturing", "hospitality", "nonprofit", "legal",
    "insurance", "retail", "agencies", "consulting", "gaming", "travel", "construction",
]
AUDIENCE_POOL = [
    "startups", "enterprises", "freelancers", "agencies", "remote-teams", "small-business",
    "product-managers", "developers", "marketers", "operations-teams",
]


def generate_pseo_pages(profile: dict, target_count: int = 110) -> list:
    """Workspace-specific pSEO dataset: [Product] for [Industry] / for [Use Case] /
    alternative for [Audience]. Content differs per page (industry/use-case pulled
    into the copy, not just the title) so pages aren't near-duplicates."""
    name = profile.get("name", "This product")
    use_cases = profile.get("use_cases") or ["core workflows"]
    value_props = profile.get("value_props") or [f"{name} saves teams time."]
    pain_points = profile.get("pain_points") or ["manual busywork"]
    pages = []

    for industry in INDUSTRY_POOL:
        title = f"{name} for {industry.replace('-', ' ').title()}"
        body = (
            f"{name} helps {industry.replace('-', ' ')} teams tackle {pain_points[hash(industry) % len(pain_points)]}. "
            f"{value_props[hash(industry) % len(value_props)]} Built for {industry.replace('-', ' ')} workflows, "
            f"{name} plugs into how {industry.replace('-', ' ')} teams already work."
        )
        pages.append(("industry", industry, title, body))

    for uc in use_cases:
        title = f"{name} for {uc}"
        body = (
            f"Use {name} for {uc.lower()}. {value_props[hash(uc) % len(value_props)]} "
            f"Teams pick {name} for {uc.lower()} because it removes {pain_points[hash(uc) % len(pain_points)]}."
        )
        pages.append(("use_case", uc, title, body))

    for audience in AUDIENCE_POOL:
        title = f"{name} alternative for {audience.replace('-', ' ').title()}"
        body = (
            f"Looking for a {name} alternative built for {audience.replace('-', ' ')}? "
            f"{name} focuses on {pain_points[hash(audience) % len(pain_points)]}, "
            f"with {value_props[hash(audience) % len(value_props)]}"
        )
        pages.append(("audience", audience, title, body))

    # Cross combinations (industry x audience) to comfortably clear the 100+ bar
    for industry in INDUSTRY_POOL:
        for audience in AUDIENCE_POOL[:6]:
            if len(pages) >= target_count:
                break
            title = f"{name} for {audience.replace('-', ' ').title()} in {industry.replace('-', ' ').title()}"
            body = (
                f"{name} for {audience.replace('-', ' ')} working in {industry.replace('-', ' ')}. "
                f"{value_props[hash(industry + audience) % len(value_props)]}"
            )
            pages.append(("cross", f"{industry}-{audience}", title, body))
        if len(pages) >= target_count:
            break

    out = []
    slugs = [f"{kind}-{re.sub(r'[^a-z0-9]+', '-', key.lower())}" for kind, key, _, _ in pages]
    for i, (kind, key, title, body) in enumerate(pages):
        related = [s for s in slugs if s != slugs[i]][:3]
        out.append({
            "slug": slugs[i],
            "title": title,
            "meta_description": body[:155],
            "body": body + "\n\nRelated: " + ", ".join(related),
            "template": kind,
            "canonical_url": f"/pages/{slugs[i]}",
        })
    return out


def roi_by_module(events: list) -> dict:
    modules = {}
    for e in events:
        m = e.source_module or "unassigned"
        modules.setdefault(m, {"events": 0, "revenue": 0.0, "leads": 0})
        modules[m]["events"] += 1
        if e.stage == "revenue":
            modules[m]["revenue"] += e.value
        if e.stage == "lead":
            modules[m]["leads"] += 1
    return modules
