from .conftest import add_high_intent_post, make_workspace


def test_draft_is_not_an_outward_action(client):
    ws = make_workspace(client, "Gate1")
    add_high_intent_post(ws["id"])
    client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    items = client.get(f"/api/workspaces/{ws['id']}/approvals").json()
    assert all(i["status"] == "PENDING_APPROVAL" for i in items)


def test_export_requires_approval_first(client):
    ws = make_workspace(client, "Gate2")
    add_high_intent_post(ws["id"])
    client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    items = client.get(f"/api/workspaces/{ws['id']}/approvals").json()
    assert len(items) > 0, "seed text should produce at least one high-intent draft"
    item = items[0]

    r = client.post(f"/api/workspaces/{ws['id']}/approvals/{item['id']}/export")
    assert r.status_code == 400, "exporting a non-approved item must be rejected"


def test_approve_then_export_creates_audit_trail(client):
    ws = make_workspace(client, "Gate3")
    add_high_intent_post(ws["id"])
    client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    item = client.get(f"/api/workspaces/{ws['id']}/approvals").json()[0]

    r = client.post(f"/api/workspaces/{ws['id']}/approvals/{item['id']}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    r = client.post(f"/api/workspaces/{ws['id']}/approvals/{item['id']}/export")
    assert r.status_code == 200
    assert r.json()["status"] in ("SENT", "EXPORTED")

    audit = client.get(f"/api/workspaces/{ws['id']}/audit").json()
    actions = [a["action"] for a in audit]
    assert "approved" in actions
    assert any(a in actions for a in ("sent", "exported"))


def test_reject_prevents_export(client):
    ws = make_workspace(client, "Gate4")
    add_high_intent_post(ws["id"])
    client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    item = client.get(f"/api/workspaces/{ws['id']}/approvals").json()[0]

    client.post(f"/api/workspaces/{ws['id']}/approvals/{item['id']}/reject")
    r = client.post(f"/api/workspaces/{ws['id']}/approvals/{item['id']}/export")
    assert r.status_code == 400


def test_content_studio_generates_drafts_only(client):
    ws = make_workspace(client, "Gate5")
    r = client.post(f"/api/workspaces/{ws['id']}/content/generate", json={"idea": "test idea"})
    pieces = r.json()
    assert all(p["status"] == "draft" for p in pieces)
    # scheduling creates an approval-gated export action, not a direct post
    r2 = client.post(f"/api/workspaces/{ws['id']}/content/{pieces[0]['id']}/schedule")
    assert r2.json()["status"] == "PENDING_APPROVAL"
