from .conftest import make_workspace


def test_manual_onboarding_derives_profile_and_icp(client):
    ws = make_workspace(client, "OnboardCo", raw_text=(
        "OnboardCo helps fintech companies reduce fraud losses. Teams struggle with "
        "manual review queues and false positives. Built for compliance teams and risk analysts."
    ))
    profile = client.get(f"/api/workspaces/{ws['id']}/profile").json()
    assert profile["name"] == "OnboardCo"
    assert len(profile["keywords"]) > 0
    assert len(profile["value_props"]) > 0

    icp = client.get(f"/api/workspaces/{ws['id']}/icp").json()
    assert len(icp) == 1
    assert icp[0]["segment_name"]


def test_manual_onboarding_works_with_zero_api_keys(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    r = client.get("/api/system/mode")
    assert r.json()["mode"] == "DEMO"
    ws = make_workspace(client, "NoKeyCo")
    assert ws["id"] is not None


def test_profile_is_editable(client):
    ws = make_workspace(client, "EditCo")
    r = client.put(f"/api/workspaces/{ws['id']}/profile", json={"positioning": "Updated positioning"})
    assert r.json()["positioning"] == "Updated positioning"
