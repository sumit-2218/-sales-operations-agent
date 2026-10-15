"""Principal workflow through the real API + (SQLite) database, with Ollama mocked."""
import io
import os
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.models import Role, User
from conftest import GOOD_EXPLANATION, GOOD_OUTREACH, PASSWORD, chat_reply

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sample_leads.csv")


def test_full_sales_workflow(client, mock_ollama):
    with SessionLocal() as db:  # 3. administrator bootstrap (what `python -m app.seed --admin` does)
        db.add(User(name="Admin", email="admin@example.com", password_hash=hash_password(PASSWORD), role=Role.ADMIN)); db.commit()
    tok = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": PASSWORD}).json()["access_token"]  # 4
    h = {"Authorization": f"Bearer {tok}"}
    content = open(SAMPLE, "rb").read()
    r = client.post("/api/v1/imports/confirm", headers=h, files={"file": ("sample_leads.csv", io.BytesIO(content))})  # 5
    assert r.json()["imported"] == 20
    leads = client.get("/api/v1/leads", params={"page_size": 100}, headers=h).json()  # 6
    assert leads["total"] == 20
    icp = client.post("/api/v1/icp", json={"name": "Demo", "config": {"target_industries": ["Software", "Logistics"], "excluded_industries": ["Gambling"],
        "min_employees": 50, "max_employees": 500, "target_locations": ["Germany", "Austria"], "keywords": ["saas", "automation"]}}, headers=h)  # 7
    assert icp.status_code == 201
    cats = {x["company_name"]: x["qualification_category"] for x in client.get("/api/v1/leads", params={"page_size": 100}, headers=h).json()["items"]}
    assert cats["LuckyStar Casino Group"] == "excluded" and cats["Mystery Corp"] == "review_required"
    northwind = next(x for x in leads["items"] if x["company_name"].startswith("Northwind"))
    s = client.post(f"/api/v1/leads/{northwind['id']}/score", headers=h).json()  # 8, 9
    assert s["category"] == "strong_match" and s["breakdown"]["factors"]
    mock_ollama(lambda req: chat_reply(GOOD_EXPLANATION))
    assert client.post(f"/api/v1/leads/{northwind['id']}/analyze", headers=h).json()["ai_status"] == "completed"  # 10
    mock_ollama(lambda req: chat_reply(GOOD_OUTREACH))
    d = client.post(f"/api/v1/leads/{northwind['id']}/outreach", json={}, headers=h).json()  # 11
    assert client.get(f"/api/v1/leads/{northwind['id']}/outreach", headers=h).json()["items"][0]["id"] == d["id"]  # 12
    due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    f = client.post("/api/v1/follow-ups", json={"lead_id": northwind["id"], "title": "Call", "due_at": due}, headers=h).json()  # 13
    assert client.get("/api/v1/dashboard/summary", headers=h).json()["pending_follow_ups"] == 1
    client.patch(f"/api/v1/follow-ups/{f['id']}", json={"status": "completed"}, headers=h)  # 14
    summary = client.get("/api/v1/dashboard/summary", headers=h).json()  # 15
    assert summary["pending_follow_ups"] == 0 and summary["outreach_drafts"] == 1 and summary["total_leads"] == 20
    # 16. a rep cannot reach admin functions
    client.post("/api/v1/auth/register", json={"name": "Rep", "email": "rep@example.com", "password": PASSWORD})
    rt = client.post("/api/v1/auth/login", json={"email": "rep@example.com", "password": PASSWORD}).json()["access_token"]
    assert client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {rt}"}).status_code == 403
