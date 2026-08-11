# Demo data

`backend/app/seed.py` seeds three workspaces from `fixtures/product_*.yaml` on
first boot (or via `python -m app.seed`). Each workspace gets its own:

- `ProductProfile` + derived `ICP` (from the yaml, not text-heuristics --
  authored profiles read more like real product copy for the demo)
- ~50 `AppUser`s with signup/activation events spread over 90 days (~35%
  never activate, for the Lifecycle module to find)
- 200 `CommunityPost`s: 30 "planted" high-intent posts referencing the
  product's own pain points/keywords, 170 generic noise posts shared across
  all three products (so Lead Radar's ranking has real signal to separate
  from real noise, not a rigged 100%-relevant feed)
- Leads scored from those posts via the same deterministic engine Lead Radar
  uses at runtime (`growth_logic.score_post`)
- 3 `Competitor`s (named in the yaml) with 1 seeded `CompetitorEvent` each,
  severities `high/medium/low` in rotation, so Competitor Watch always has at
  least one high-severity item to draft outreach from
- 40 `Review`s, ~25% negative (rating <= 2.5) so Reputation always has
  something to respond to
- A handful of seeded `ContentPiece`s (twitter/linkedin) per pain point
- `VocItem`s, one per pain point, spread across all four roadmap columns
- Referral entries for the first 8 users
- 110+ `Page`s from the pSEO generator
- `GrowthEvent`s across all five funnel stages, scaled per workspace and
  attributed to a mix of modules, so Portfolio/Analytics/ROI differ per
  product

All generation is seeded with `random.Random(1000 + i)` per workspace (never
the bare `random` module), so re-running `python -m app.seed` reproduces
identical data.

## The three products

### 1. Shiftly -- team scheduling SaaS (`fixtures/product_a_scheduler.yaml`)

B2B, hourly/shift-based teams (retail, hospitality, healthcare). Pain points
center on manual rostering and no-shows. Keywords: "shift scheduling",
"roster software", "no-show reduction". Competitors: Deputy, When I Work,
Homebase.

### 2. Routewave -- developer shipping API (`fixtures/product_b_devapi.yaml`)

Developer/API-first, ecommerce and logistics backend teams. Pain points
center on carrier integration complexity and flaky sandboxes. Keywords:
"shipping api", "carrier integration", "tracking webhook". Competitors:
EasyPost, Shippo, ShipEngine.

### 3. Pulseform -- D2C fitness app (`fixtures/product_c_fitness.yaml`)

Consumer, individual subscribers restarting or returning to fitness. Pain
points center on generic templates and motivation collapse. Keywords:
"personalized workout plan", "home workout app", "postpartum fitness".
Competitors: Future, Fitbod, Freeletics.

## Why the differences matter

The whole product thesis is "add a product once, get a product-specific
growth system." Every module reads `ProductProfile.keywords`/`pain_points` at
run time -- there's no per-product branching logic anywhere in the codebase.
That the three workspaces' leads, keywords, content, and pSEO pages come out
visibly different is proof the profile-driven design works, not a hand-tuned
demo path. `backend/tests/test_e2e.py::test_seed_creates_three_distinct_products`
and `test_content_differs_by_workspace` assert this in CI.

## Expected demo behavior

- Switching products in the sidebar changes every module's data immediately
  -- Lead Radar shows different posts, Content Studio drafts about different
  pain points, pSEO pages reference different industries.
- Lead Radar's "Scan community sources" surfaces ~3-10 high-opportunity leads
  per workspace (opportunity score >= 0.45) and drafts a reply for each,
  landing in the Approval Inbox.
- Competitor Watch always finds at least one high-severity event per
  workspace to draft outreach from.
- Reputation always finds negative reviews to respond to.
- Portfolio shows three different funnels with different visit/lead/signup/
  activation/revenue counts and different total revenue.
