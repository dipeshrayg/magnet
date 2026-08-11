# MAGNET -- Presentation (12 slides)

## 1. Problem

**Slide:** Running growth for one product is already scattered across a
dozen tools. Running it for three products means three of everything --
three spreadsheets, three outreach lists, three SEO backlogs, zero shared
view of what's working.

**Speaker notes:** Most of that work is mechanical: reading community threads
for buying signals, drafting the fiftieth outreach variant, noticing a
competitor's outage before a customer does. It's exactly the kind of
first-pass work an agent can do well -- as long as a human still decides
what goes out the door.

## 2. Multi-product growth insight

**Slide:** Add a product once -> get a product-specific growth system.

**Speaker notes:** The core bet: if the growth engine actually reads a
product's profile instead of hard-coding assumptions, two different products
should produce visibly different leads, keywords, content, and pages from
the exact same code. That's the test we hold the build to, not just a
demo script -- see `test_seed_creates_three_distinct_products`.

## 3. MAGNET solution

**Slide:** One workspace per product. ICP -> Leads -> Content -> Outreach ->
Analytics, all reading from the same `ProductProfile`. Everything outward
routes through one Approval Inbox.

**Speaker notes:** 12 modules, all workspace-scoped, all approval-gated. The
Portfolio view compares them side by side.

## 4. Add Product onboarding

**Slide:** Two paths -- paste a description (zero API keys, zero network) or
point at a public landing page URL (robots.txt respected). Both produce the
same `ProductProfile` + `ICP`.

**Speaker notes:** Demo this live: paste three sentences about a fictional
product, watch the ICP and keywords come out the other side in under a
second, no external calls.

## 5. Live product demo

**Slide:** Switch Shiftly -> Routewave -> Pulseform. Same nav, different
leads, different pSEO pages, different funnel numbers.

**Speaker notes:** Walk Lead Radar for Shiftly (shift-scheduling pain
points) side by side with Pulseform (postpartum fitness pain points) --
same "Scan" button, completely different output, because it's reading each
workspace's own profile.

## 6. Architecture

**Slide:** FastAPI + SQLAlchemy + SQLite backend, React + Vite + Tailwind
frontend, everything free-tier. `WorkspaceContext` is the single choke point
for data access -- no router can query a workspace-scoped table unscoped.

**Speaker notes:** Point at `backend/app/workspace_ctx.py` -- 40 lines, and
it's the entire isolation guarantee. Isolation is proven with automated
tests (`test_isolation.py`), not just a UI convention.

## 7. Approval Inbox / ethics-by-design

**Slide:** DRAFT -> PENDING_APPROVAL -> (Approve|Reject) -> (Send/Export).
No endpoint skips a step. Every transition is audit-logged.

**Speaker notes:** This is the module to spend the most time on. Show a
lead-radar-generated draft, approve it, export it, then pull up
`/api/workspaces/{id}/audit` and show the two log entries. "MAGNET never
publishes or sends automatically" isn't a tagline, it's an invariant tested
in `test_export_requires_approval_first`.

## 8. Attribution / ROI

**Slide:** Every lead/signup/revenue event carries a `source_module`. ROI by
module, funnel conversion rates, all workspace-scoped.

**Speaker notes:** Show the Analytics page's ROI table -- different modules
lead for different products (Shiftly's top module differs from Pulseform's),
because the underlying `GrowthEvent` distribution is seeded differently per
product, same as everything else.

## 9. Portfolio comparison

**Slide:** All three products' funnels side by side. Click through to any
one.

**Speaker notes:** This is the "it's obviously multi-product" slide --
three cards, three different funnel shapes, one screen.

## 10. Results

**Slide:** 21 automated tests (isolation, approval-safety, onboarding, e2e,
growth-logic scoring), ruff clean, ESLint clean, production build green,
110+ pSEO pages per product, 3 products with measurably distinct output.

**Speaker notes:** These aren't aspirational -- they're the actual `pytest`,
`ruff`, `npm run lint`, `npm run build` output from this build (see the
engineering report).

## 11. Business impact

**Slide:** A founder running 3 products currently needs 3x the growth
tooling and headcount to keep pace on lead-finding, content, and outreach.
MAGNET's bet is that a single profile-driven engine gets most of the way
there for a fraction of the manual effort, with a human still gating
everything that leaves the building.

**Speaker notes:** Frame it as leverage, not replacement -- every module's
output is a first draft a human still reviews.

## 12. Roadmap / close

**Slide:** Next: real connector implementations behind the existing
Connector SDK interface, LLM-assisted pSEO/VOC in live mode, multi-user
roles on top of the existing workspace model.

**Speaker notes:** Close on the invariant: whatever ships next, it still
has to go through the same `WorkspaceContext` and the same Approval Inbox --
that's the part of the architecture that doesn't change.
