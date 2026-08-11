import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai import is_live_mode
from .db import Base, engine
from .routers import analytics, approvals, content, growth, pseo, referrals, workspace

app = FastAPI(title="MAGNET", description="Autonomous multi-product growth engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_if_empty()
    mode = "LIVE" if is_live_mode() else "DEMO"
    write_health({"status": "ok", "started_at": datetime.now(timezone.utc).isoformat(), "mode": mode})


def _seed_if_empty():
    """First boot on a fresh DB (fresh clone / fresh container) auto-seeds the
    three demo products, so the dashboard has data with zero extra commands.
    Opt-in via MAGNET_AUTO_SEED so the test suite (which resets the schema
    before every test) doesn't pay for a full reseed each time."""
    if os.environ.get("MAGNET_AUTO_SEED") != "1":
        return
    from .db import SessionLocal
    from .models import Workspace
    db = SessionLocal()
    try:
        if db.query(Workspace).count() == 0:
            from .seed import run_seed
            run_seed()
    finally:
        db.close()


def write_health(data: dict):
    path = os.environ.get("MAGNET_HEALTH_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "health.json"))
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


app.include_router(workspace.router, prefix="/api")
app.include_router(growth.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(pseo.router, prefix="/api")
app.include_router(referrals.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "LIVE" if is_live_mode() else "DEMO"}
