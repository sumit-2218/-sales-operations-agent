import httpx
from conftest import GOOD_EXPLANATION, GOOD_OUTREACH, chat_reply
from helpers import LEAD


def lead(client, h):
    return client.post("/api/v1/leads", json=LEAD, headers=h).json()


def test_analyze_persists_validated_explanation(client, rep, mock_ollama):
    mock_ollama(lambda req: chat_reply(GOOD_EXPLANATION))
    l = lead(client, rep)
    r = client.post(f"/api/v1/leads/{l['id']}/analyze", headers=rep)
    assert r.status_code == 200
    j = r.json()
    assert j["ai_status"] == "completed" and j["ai_explanation"]["summary"] and j["model_name"] == "qwen2.5:3b-instruct"
    assert j["score"] == l["score"]  # AI never changes the deterministic score
    stored = client.get(f"/api/v1/leads/{l['id']}/analyses", headers=rep).json()["items"][0]
    assert stored["ai_explanation"] == j["ai_explanation"]
    assert client.get(f"/api/v1/leads/{l['id']}", headers=rep).json()["score"] == l["score"]


def test_analyze_when_ollama_down_keeps_score_and_allows_retry(client, rep, mock_ollama):
    def down(req): raise httpx.ConnectError("refused")
    mock_ollama(down)
    l = lead(client, rep)
    r = client.post(f"/api/v1/leads/{l['id']}/analyze", headers=rep)
    assert r.status_code == 503 and r.json()["detail"]["code"] == "unavailable" and r.json()["detail"]["hint"]
    a = client.get(f"/api/v1/leads/{l['id']}/analyses", headers=rep).json()["items"][0]
    assert a["ai_status"] == "failed" and a["score"] == l["score"] and a["ai_error"]
    # non-AI functionality still works
    assert client.post(f"/api/v1/leads/{l['id']}/score", headers=rep).status_code == 201
    assert client.get("/api/v1/dashboard/summary", headers=rep).status_code == 200
    # retry once Ollama is back
    mock_ollama(lambda req: chat_reply(GOOD_EXPLANATION))
    r = client.post(f"/api/v1/leads/{l['id']}/analyze", json={"analysis_id": a["id"]}, headers=rep)
    assert r.status_code == 200 and r.json()["ai_status"] == "completed" and r.json()["id"] == a["id"]


def test_analyze_model_missing_message(client, rep, mock_ollama):
    mock_ollama(lambda req: httpx.Response(404, json={"error": "not found"}))
    l = lead(client, rep)
    r = client.post(f"/api/v1/leads/{l['id']}/analyze", headers=rep)
    assert r.status_code == 503 and r.json()["detail"]["code"] == "model_missing"


def test_outreach_create_edit_regenerate_history(client, rep, mock_ollama):
    mock_ollama(lambda req: chat_reply(GOOD_OUTREACH))
    l = lead(client, rep)
    r = client.post(f"/api/v1/leads/{l['id']}/outreach", json={"channel": "email", "tone": "friendly", "length": "short"}, headers=rep)
    assert r.status_code == 201
    d = r.json()
    assert d["status"] == "draft" and d["subject"] and "review" in d["review_notice"].lower()
    e = client.patch(f"/api/v1/outreach/{d['id']}", json={"body": "My edited text for the message."}, headers=rep)
    assert e.status_code == 200 and e.json()["body"] == "My edited text for the message."
    assert client.patch(f"/api/v1/outreach/{d['id']}", json={"body": " "}, headers=rep).status_code in (422,)
    g = client.post(f"/api/v1/outreach/{d['id']}/regenerate", json={"tone": "concise"}, headers=rep)
    assert g.status_code == 201 and g.json()["parent_id"] == d["id"] and g.json()["tone"] == "concise"
    drafts = client.get(f"/api/v1/leads/{l['id']}/outreach", headers=rep).json()
    assert drafts["total"] == 2 and {x["status"] for x in drafts["items"]} == {"draft", "superseded"}
    assert client.patch(f"/api/v1/outreach/{d['id']}", json={"body": "again text here"}, headers=rep).status_code == 409


def test_outreach_failure_saves_nothing(client, rep, mock_ollama):
    def down(req): raise httpx.ConnectError("x")
    mock_ollama(down)
    l = lead(client, rep)
    assert client.post(f"/api/v1/leads/{l['id']}/outreach", json={}, headers=rep).status_code == 503
    assert client.get(f"/api/v1/leads/{l['id']}/outreach", headers=rep).json()["total"] == 0


def test_outreach_access_control(client, user_headers, mock_ollama):
    mock_ollama(lambda req: chat_reply(GOOD_OUTREACH))
    a, _ = user_headers("sales_rep"); b, _ = user_headers("sales_rep")
    l = lead(client, a)
    d = client.post(f"/api/v1/leads/{l['id']}/outreach", json={}, headers=a).json()
    assert client.post(f"/api/v1/leads/{l['id']}/outreach", json={}, headers=b).status_code == 404
    assert client.patch(f"/api/v1/outreach/{d['id']}", json={"body": "hacked body text"}, headers=b).status_code == 404
    assert client.patch("/api/v1/outreach/999", json={"body": "x y z"}, headers=a).status_code == 404
