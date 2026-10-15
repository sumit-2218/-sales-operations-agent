from helpers import LEAD

CONFIG = {"target_industries": ["Software"], "excluded_industries": ["Retail"], "min_employees": 10, "max_employees": 200,
          "target_locations": ["Germany"], "keywords": ["saas"], "weights": {"industry": 50, "company_size": 50}}


def mk_lead(client, h, **kw):
    return client.post("/api/v1/leads", json={**LEAD, **kw}, headers=h).json()


def test_icp_crud_and_activation(client, rep):
    r = client.post("/api/v1/icp", json={"name": "Mine", "config": CONFIG}, headers=rep)
    assert r.status_code == 201 and r.json()["is_active"] is True and r.json()["explanations"]
    second = client.post("/api/v1/icp", json={"name": "Second", "config": CONFIG}, headers=rep).json()
    assert second["is_active"] is False
    client.patch(f"/api/v1/icp/{second['id']}", json={"is_active": True}, headers=rep)
    listing = client.get("/api/v1/icp", headers=rep).json()
    assert [i["is_active"] for i in listing] == [False, True]
    assert client.delete(f"/api/v1/icp/{second['id']}", headers=rep).status_code == 204


def test_icp_validation(client, rep):
    bad = [{**CONFIG, "min_employees": 500, "max_employees": 10}, {**CONFIG, "weights": {"industry": -1}},
           {**CONFIG, "weights": {"bogus": 5}}, {**CONFIG, "weights": {"industry": 0}},
           {**CONFIG, "strong_threshold": 50, "potential_threshold": 60}]
    for cfg in bad:
        assert client.post("/api/v1/icp", json={"name": "x", "config": cfg}, headers=rep).status_code == 422


def test_icp_is_private_to_owner(client, user_headers):
    a, _ = user_headers("sales_rep")
    b, _ = user_headers("sales_rep")
    icp = client.post("/api/v1/icp", json={"name": "A", "config": CONFIG}, headers=a).json()
    assert client.get(f"/api/v1/icp/{icp['id']}", headers=b).status_code == 404
    assert client.patch(f"/api/v1/icp/{icp['id']}", json={"name": "hack"}, headers=b).status_code == 404


def test_score_endpoint_breakdown_and_reproducibility(client, rep):
    client.post("/api/v1/icp", json={"name": "Mine", "config": CONFIG}, headers=rep)
    lead = mk_lead(client, rep)
    a = client.post(f"/api/v1/leads/{lead['id']}/score", headers=rep).json()
    b = client.post(f"/api/v1/leads/{lead['id']}/score", headers=rep).json()
    assert a["score"] == b["score"] == 100 and a["category"] == "strong_match"
    names = {f["name"]: f["status"] for f in a["breakdown"]["factors"]}
    assert names["industry"] == "match" and names["revenue"] == "missing"
    assert a["ai_status"] == "not_requested"
    assert client.get(f"/api/v1/leads/{lead['id']}/analyses", headers=rep).json()["total"] == 2


def test_exclusion_beats_high_score(client, rep):
    client.post("/api/v1/icp", json={"name": "Mine", "config": {**CONFIG, "excluded_industries": ["Software"]}}, headers=rep)
    lead = mk_lead(client, rep)
    assert lead["qualification_category"] == "excluded"


def test_changing_icp_rescores_existing_leads(client, rep):
    lead = mk_lead(client, rep)
    before = lead["score"]
    client.post("/api/v1/icp", json={"name": "Strict", "config": {**CONFIG, "target_industries": ["Mining"], "weights": {"industry": 100}}}, headers=rep)
    assert client.get(f"/api/v1/leads/{lead['id']}", headers=rep).json()["score"] != before


def test_score_with_unknown_icp_and_lead(client, rep):
    lead = mk_lead(client, rep)
    assert client.post(f"/api/v1/leads/{lead['id']}/score", json={"icp_id": 999}, headers=rep).status_code == 404
    assert client.post("/api/v1/leads/999/score", headers=rep).status_code == 404
