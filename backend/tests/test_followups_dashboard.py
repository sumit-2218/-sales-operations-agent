from datetime import datetime, timedelta, timezone

from helpers import LEAD


def iso(delta_hours):
    return (datetime.now(timezone.utc) + timedelta(hours=delta_hours)).isoformat()


def lead(client, h, **kw):
    return client.post("/api/v1/leads", json={**LEAD, **kw}, headers=h).json()


def test_follow_up_crud_complete_cancel(client, rep):
    l = lead(client, rep)
    r = client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "Call", "due_at": iso(24), "priority": "high"}, headers=rep)
    assert r.status_code == 201 and r.json()["status"] == "open" and r.json()["is_overdue"] is False
    fid = r.json()["id"]
    assert client.patch(f"/api/v1/follow-ups/{fid}", json={"title": "Call Lena"}, headers=rep).json()["title"] == "Call Lena"
    c = client.patch(f"/api/v1/follow-ups/{fid}", json={"status": "completed"}, headers=rep).json()
    assert c["status"] == "completed" and c["completed_at"]
    r2 = client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "Email", "due_at": iso(5)}, headers=rep).json()
    x = client.patch(f"/api/v1/follow-ups/{r2['id']}", json={"status": "cancelled"}, headers=rep).json()
    assert x["status"] == "cancelled" and x["completed_at"] is None
    assert client.delete(f"/api/v1/follow-ups/{r2['id']}", headers=rep).status_code == 204


def test_overdue_calculation_and_filters(client, rep):
    l = lead(client, rep)
    mk = lambda t, h, **kw: client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": t, "due_at": iso(h), **kw}, headers=rep).json()
    late = mk("late", -48); mk("soon", 48, priority="low"); done = mk("done", -10)
    client.patch(f"/api/v1/follow-ups/{done['id']}", json={"status": "completed"}, headers=rep)
    assert late["is_overdue"] is True
    g = lambda **p: client.get("/api/v1/follow-ups", params=p, headers=rep).json()
    assert [f["title"] for f in g(overdue="true")["items"]] == ["late"]  # completed items are never overdue
    assert g(status="completed")["total"] == 1 and g(priority="low")["total"] == 1 and g()["total"] == 3
    assert g()["items"][0]["title"] == "late"  # ordered by due date


def test_validation_and_access(client, user_headers):
    a, aid = user_headers("sales_rep"); b, bid = user_headers("sales_rep"); m, _ = user_headers("manager")
    l = lead(client, a)
    assert client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "", "due_at": iso(1)}, headers=a).status_code == 422
    assert client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "x", "due_at": "not a date"}, headers=a).status_code == 422
    assert client.post("/api/v1/follow-ups", json={"lead_id": 999, "title": "x", "due_at": iso(1)}, headers=a).status_code == 404
    assert client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "x", "due_at": iso(1)}, headers=b).status_code == 404
    assert client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "x", "due_at": iso(1), "assigned_user_id": bid}, headers=a).status_code == 403
    ok = client.post("/api/v1/follow-ups", json={"lead_id": l["id"], "title": "x", "due_at": iso(1), "assigned_user_id": bid}, headers=m)
    assert ok.status_code == 201 and ok.json()["assigned_user_id"] == bid
    assert client.get("/api/v1/follow-ups/999", headers=a).status_code == 404


def test_dashboard_reflects_database(client, rep, mock_ollama):
    from conftest import GOOD_OUTREACH, chat_reply
    mock_ollama(lambda req: chat_reply(GOOD_OUTREACH))
    s0 = client.get("/api/v1/dashboard/summary", headers=rep).json()
    assert s0["total_leads"] == 0 and s0["pending_follow_ups"] == 0
    a = lead(client, rep)                                    # strong match with default ICP
    lead(client, rep, company_name="Nameless", email=None, industry=None, employee_count=None, location=None,
         annual_revenue=None, description=None)               # review required
    client.post(f"/api/v1/leads/{a['id']}/outreach", json={}, headers=rep)
    f1 = client.post("/api/v1/follow-ups", json={"lead_id": a["id"], "title": "a", "due_at": iso(-5)}, headers=rep).json()
    client.post("/api/v1/follow-ups", json={"lead_id": a["id"], "title": "b", "due_at": iso(30)}, headers=rep)
    s = client.get("/api/v1/dashboard/summary", headers=rep).json()
    assert s["total_leads"] == 2 and s["qualified_leads"] == 1 and s["review_required_leads"] == 1
    assert s["outreach_drafts"] == 1 and s["pending_follow_ups"] == 2 and s["overdue_follow_ups"] == 1
    assert s["by_status"] == {"new": 2} and len(s["upcoming_follow_ups"]) == 2
    client.patch(f"/api/v1/follow-ups/{f1['id']}", json={"status": "completed"}, headers=rep)
    s = client.get("/api/v1/dashboard/summary", headers=rep).json()
    assert s["pending_follow_ups"] == 1 and s["overdue_follow_ups"] == 0
    acts = client.get("/api/v1/dashboard/activity", headers=rep).json()
    assert {x["action"] for x in acts} >= {"lead.created", "followup.completed", "outreach.created"}


def test_dashboard_scoped_per_role(client, user_headers):
    a, _ = user_headers("sales_rep"); b, _ = user_headers("sales_rep"); m, _ = user_headers("manager")
    lead(client, a)
    assert client.get("/api/v1/dashboard/summary", headers=b).json()["total_leads"] == 0
    assert client.get("/api/v1/dashboard/summary", headers=m).json()["total_leads"] == 1
