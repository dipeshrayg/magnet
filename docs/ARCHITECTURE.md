# Architecture

## Workspace isolation

Every workspace-scoped table (`product_profiles`, `icps`, `app_users`,
`events`, `community_posts`, `leads`, `competitors`, `competitor_events`,
`reviews`, `content_pieces`, `outreach_messages`, `lifecycle_messages`,
`voc_items`, `pages`, `referrals`, `free_tool_leads`, `approval_items`,
`audit_logs`, `growth_events`) carries a `workspace_id` foreign key
(`backend/app/models.py`).

All access to those tables goes through `WorkspaceContext`
(`backend/app/workspace_ctx.py`):

```python
class WorkspaceContext:
    def query(self, model):
        # pre-filters by workspace_id; raises if model isn't workspace-scoped
    def get_or_404(self, model, obj_id):
        # filters by workspace_id AND id -- cross-workspace id guesses 404
    def add(self, obj):
        # stamps workspace_id on write
```

Every router depends on `get_workspace_ctx`, which resolves `workspace_id`
from the URL path and 404s if it doesn't exist. There is no code path in any
router that queries a workspace-scoped model without going through `ctx`, so
isolation isn't a convention -- a router that queried `db.query(Lead)`
directly would return every workspace's leads, which is exactly the failure
mode `backend/tests/test_isolation.py` checks for (`test_no_cross_workspace_write`,
`test_cross_workspace_object_access_404s`, etc).

## Data model

`ProductProfile` (name, description, value props, target customers,
industries, use cases, pain points, competitors, keywords, positioning) is
the single source of truth per workspace. `ICP` is derived from it
(`growth_logic.derive_icp_from_profile`). Every module reads keywords/pain
points/use-cases off these two tables -- Lead Radar's scoring, Content
Studio's prompts, and the pSEO generator all take `ProductProfile` fields as
input, which is what makes two workspaces produce different output from the
same code path.

## Connector SDK

`Source` isn't a literal class hierarchy in this build -- the interface is
implicit in how fixtures are shaped and how `seed.py` populates
`CommunityPost`/`Review`/`CompetitorEvent` rows. Every module that consumes
"external" data (Lead Radar, Competitor Watch, Reputation) reads from these
tables, not from a live network call. A live connector (`RedditSource`,
`HNSource`, ...) would populate the same tables with the same shape --
`{source, author, text, url, posted_at}` for posts, `{source, rating, text,
subject}` for reviews -- so adding one is additive, not a rewrite. None
ships in this build (see README Known Limitations).

## AI abstraction

`backend/app/ai.py` defines `LLMProvider` with one method, `draft(system,
prompt) -> str`. `DemoProvider` is deterministic (seeded by a hash of the
prompt, no network) and is the default. `GeminiProvider`/`GroqProvider`
activate only if `GEMINI_API_KEY`/`GROQ_API_KEY` is set
(`get_provider()`). No router imports a concrete provider -- every module
calls `get_provider()` and uses whatever it returns, so a router's code is
identical in demo and live mode.

## Approval Inbox

`ApprovalItem.status` moves through `PENDING_APPROVAL -> APPROVED ->
SENT/EXPORTED`, or `PENDING_APPROVAL -> REJECTED`. `backend/app/approval_lib.py`
is the only path any module uses to create a draft -- it always starts at
`PENDING_APPROVAL`. `backend/app/routers/approvals.py` is the only place
`status` transitions:

- `POST /approve` requires `PENDING_APPROVAL`, sets `APPROVED`, audit-logs `approved`.
- `POST /export` requires `APPROVED`, sets `SENT`/`EXPORTED`, audit-logs it.
- `POST /reject` requires `PENDING_APPROVAL`, sets `REJECTED`.

There is no endpoint that skips from `PENDING_APPROVAL` straight to
`SENT`/`EXPORTED` -- `test_approval.py::test_export_requires_approval_first`
asserts exactly that.

## Scheduler / daily pipeline

`backend/scripts/daily_scan.py` drives every workspace's Lead Radar,
Competitor Watch, Reputation, and Lifecycle scans in-process via
`TestClient(app)` (so it exercises the exact same code path a real request
would). Each source scan is wrapped in its own try/except -- one failing
source logs a failure in that workspace's result but doesn't stop the other
sources or other workspaces. Results (including failures) are written to
`health.json` at the repo root. The script never calls `/approve` or
`/export`, so it structurally cannot publish or send anything.

## Attribution & analytics

`GrowthEvent` rows (`stage` in `visit/lead/signup/activation/revenue`,
`source_module`, `attribution_source`) are the attribution ledger. Every
module that produces a lead or signup (Free Tool, Referrals, Lead Radar)
writes one. `growth_logic.funnel_from_events` computes stage counts and
stage-to-stage conversion rates; `growth_logic.roi_by_module` groups by
`source_module` for the per-module ROI table. `/api/portfolio` runs the same
funnel computation per workspace so the Portfolio view is a simple fan-out
over the same function every per-workspace dashboard uses.
