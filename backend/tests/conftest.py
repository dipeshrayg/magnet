import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["MAGNET_DB"] = os.path.join(tempfile.gettempdir(), "magnet_test.db")
os.environ["MAGNET_HEALTH_PATH"] = os.path.join(tempfile.gettempdir(), "magnet_test_health.json")

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def add_high_intent_post(ws_id, text=(
    "Looking for scheduling recommendations? Any alternative for automate workflows worth it? "
    "Tired of manual busywork with no-shows, ready to switch teams and saas tools?"
)):
    from app.db import SessionLocal
    from app.models import CommunityPost
    db = SessionLocal()
    try:
        post = CommunityPost(workspace_id=ws_id, source="reddit", author="tester", text=text)
        db.add(post)
        db.commit()
    finally:
        db.close()


def make_workspace(client, name="Acme", raw_text=None):
    raw_text = raw_text or (
        f"{name} helps startups automate scheduling and reduce no-shows for saas teams. "
        "Great for remote teams and agencies dealing with manual busywork."
    )
    r = client.post("/api/workspaces/onboard/manual", json={"name": name, "raw_text": raw_text})
    assert r.status_code == 200, r.text
    return r.json()["workspace"]
