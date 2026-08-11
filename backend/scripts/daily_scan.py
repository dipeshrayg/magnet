"""Daily pipeline: (re)seed if needed, scan every workspace's community/competitor/
reputation/lifecycle sources, and refresh health.json. Every draft this produces
lands in the Approval Inbox as PENDING_APPROVAL -- this script never calls
approve/export, so it can never send or publish anything."""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Workspace  # noqa: E402


def main():
    results = {"started_at": datetime.now(timezone.utc).isoformat(), "workspaces": {}}
    with TestClient(app) as client:
        db = SessionLocal()
        try:
            workspaces = db.query(Workspace).all()
        finally:
            db.close()

        for ws in workspaces:
            ws_result = {}
            for name, path in [
                ("leads", f"/api/workspaces/{ws.id}/leads/scan"),
                ("competitors", f"/api/workspaces/{ws.id}/competitors/scan"),
                ("reputation", f"/api/workspaces/{ws.id}/reputation/scan"),
                ("lifecycle", f"/api/workspaces/{ws.id}/lifecycle/scan"),
            ]:
                try:
                    r = client.post(path)
                    ws_result[name] = {"ok": r.status_code == 200, "detail": r.json() if r.status_code == 200 else r.text}
                except Exception as e:  # a failed source must not crash the pipeline
                    ws_result[name] = {"ok": False, "detail": str(e)}
            results["workspaces"][ws.name] = ws_result

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    results["note"] = "No send/publish/approve actions performed. All drafts require human approval."
    health_path = os.path.join(os.path.dirname(__file__), "..", "..", "health.json")
    with open(health_path, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
