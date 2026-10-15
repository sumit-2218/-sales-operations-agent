from helpers import LEAD


def make(client, h, **kw):
    return client.post("/api/v1/leads", json={**LEAD, **kw}, headers=h)


def test_create_get_update_delete(client, rep):
    r = make(client, rep)
    assert r.status_code == 201
    lead = r.json()
    assert lead["status"] == "new" and lead["score"] is not None and lead["qualification_category"]
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=rep).json()["company_name"] == "Acme Automation"
    r = client.patch(f"/api/v1/leads/{lead['id']}", json={"notes": "hello", "employee_count": 5}, headers=rep)
    assert r.status_code == 200 and r.json()["notes"] == "hello"
    assert r.json()["score"] < lead["score"]  # rescored deterministically after the change
    assert client.delete(f"/api/v1/leads/{lead['id']}", headers=rep).status_code == 204
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=rep).status_code == 404


def test_validation_and_missing_data_allowed(client, rep):
    assert client.post("/api/v1/leads", json={"company_name": ""}, headers=rep).status_code == 422
    assert client.post("/api/v1/leads", json={"company_name": "X", "email": "nope"}, headers=rep).status_code == 422
    assert client.post("/api/v1/leads", json={"company_name": "X", "employee_count": -1}, headers=rep).status_code == 422
    r = client.post("/api/v1/leads", json={"company_name": "Only Name"}, headers=rep)
    assert r.status_code == 201 and r.json()["qualification_category"] == "review_required"


def test_duplicate_prevented(client, rep):
    assert make(client, rep).status_code == 201
    assert make(client, rep, company_name="ACME automation", email="LENA@acme.example").status_code == 409


def test_not_found(client, rep):
    assert client.get("/api/v1/leads/999", headers=rep).status_code == 404
    assert client.patch("/api/v1/leads/999", json={"notes": "x"}, headers=rep).status_code == 404
    assert client.delete("/api/v1/leads/999", headers=rep).status_code == 404


def test_reps_cannot_see_each_others_leads_but_managers_can(client, user_headers):
    a, _ = user_headers("sales_rep")
    b, _ = user_headers("sales_rep")
    m, _ = user_headers("manager")
    lead = make(client, a).json()
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/leads/{lead['id']}", headers=b).status_code == 404
    assert client.get("/api/v1/leads", headers=b).json()["total"] == 0
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=m).status_code == 200
    assert client.get("/api/v1/leads", headers=m).json()["total"] == 1


def test_search_filter_sort_paginate(client, rep):
    make(client, rep)
    make(client, rep, company_name="Beta Logistics", email=None, industry="Logistics", employee_count=300, location="Vienna, Austria")
    make(client, rep, company_name="Gamma Retail", email=None, industry="Retail", employee_count=3, location="Rome, Italy")
    g = lambda **p: client.get("/api/v1/leads", params=p, headers=rep).json()
    assert g()["total"] == 3
    assert [x["company_name"] for x in g(q="beta")["items"]] == ["Beta Logistics"]
    assert g(industry="retail")["total"] == 1 and g(location="austria")["total"] == 1
    assert g(status="contacted")["total"] == 0
    assert g(sort_by="company_name", sort_dir="asc")["items"][0]["company_name"] == "Acme Automation"
    p = g(page=2, page_size=2)
    assert len(p["items"]) == 1 and p["total"] == 3
    assert client.get("/api/v1/leads", params={"sort_by": "password"}, headers=rep).status_code == 422
    assert g(min_score=90)["total"] >= 1


def test_status_transitions_and_history(client, rep):
    lead = make(client, rep).json()
    url = f"/api/v1/leads/{lead['id']}"
    assert client.patch(url, json={"status": "converted"}, headers=rep).status_code == 409
    assert client.patch(url, json={"status": "contacted"}, headers=rep).json()["status"] == "contacted"
    acts = client.get(url + "/activity", headers=rep).json()["items"]
    assert any(a["action"] == "lead.status_changed" for a in acts)


def test_only_privileged_can_reassign(client, user_headers):
    a, _ = user_headers("sales_rep")
    m, mid = user_headers("manager")
    lead = make(client, a).json()
    assert client.patch(f"/api/v1/leads/{lead['id']}", json={"owner_id": mid}, headers=a).status_code == 403
    assert client.patch(f"/api/v1/leads/{lead['id']}", json={"owner_id": mid}, headers=m).status_code == 200


def test_export_neutralises_formulas(client, rep):
    make(client, rep, company_name="=HYPERLINK(\"http://x\")", email=None)
    r = client.get("/api/v1/leads/export.csv", headers=rep)
    assert r.status_code == 200 and "'=HYPERLINK" in r.text
