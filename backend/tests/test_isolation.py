from .conftest import make_workspace


def test_cross_workspace_read_blocked(client):
    ws_a = make_workspace(client, "Alpha")
    ws_b = make_workspace(client, "Beta")

    client.post(f"/api/workspaces/{ws_a['id']}/content/generate", json={"idea": "alpha-only-idea"})
    client.post(f"/api/workspaces/{ws_b['id']}/content/generate", json={"idea": "beta-only-idea"})

    content_a = client.get(f"/api/workspaces/{ws_a['id']}/content").json()
    content_b = client.get(f"/api/workspaces/{ws_b['id']}/content").json()

    assert all(c["idea"] == "alpha-only-idea" for c in content_a)
    assert all(c["idea"] == "beta-only-idea" for c in content_b)
    assert len(content_a) > 0 and len(content_b) > 0


def test_cross_workspace_object_access_404s(client):
    ws_a = make_workspace(client, "Alpha2")
    ws_b = make_workspace(client, "Beta2")

    r = client.post(f"/api/workspaces/{ws_a['id']}/content/generate", json={"idea": "secret"})
    content_id = r.json()[0]["id"]

    # The content piece belongs to workspace A; requesting it scoped under workspace B must 404.
    r = client.post(f"/api/workspaces/{ws_b['id']}/content/{content_id}/schedule")
    assert r.status_code == 404


def test_no_cross_workspace_write(client):
    ws_a = make_workspace(client, "Alpha3")
    ws_b = make_workspace(client, "Beta3")

    client.post(f"/api/workspaces/{ws_a['id']}/leads/scan")
    leads_b_before = client.get(f"/api/workspaces/{ws_b['id']}/leads").json()
    assert leads_b_before == []


def test_analytics_are_workspace_scoped(client):
    ws_a = make_workspace(client, "Alpha4")
    ws_b = make_workspace(client, "Beta4")
    client.post(f"/api/workspaces/{ws_a['id']}/freetool/run",
               json={"email": "a@x.com", "input_value": "manual busywork"})

    funnel_a = client.get(f"/api/workspaces/{ws_a['id']}/analytics/funnel").json()
    funnel_b = client.get(f"/api/workspaces/{ws_b['id']}/analytics/funnel").json()
    assert funnel_a["counts"]["lead"] >= 1
    assert funnel_b["counts"]["lead"] == 0


def test_unknown_workspace_404s(client):
    r = client.get("/api/workspaces/99999/leads")
    assert r.status_code == 404
