"""AI service tests. Ollama is MOCKED (httpx.MockTransport): they prove error handling and validation,
NOT that the real qwen2.5:3b-instruct model works. See docs/testing.md for the manual real-model procedure."""
import httpx
import pytest

from app.services import ai_service
from conftest import GOOD_EXPLANATION, GOOD_OUTREACH, chat_reply

LEAD = {"company_name": "Acme", "industry": "Software", "employee_count": 120}
BREAKDOWN = {"score": 90, "category": "strong_match", "factors": []}


def explain():
    return ai_service.explain_lead(LEAD, BREAKDOWN, {"target_industries": ["Software"]})


def test_success_validates_and_returns_model(mock_ollama):
    mock_ollama(lambda req: chat_reply(GOOD_EXPLANATION))
    out = explain()
    assert out.summary.startswith("Acme") and out.missing_information == ["Website not provided"]


def test_request_uses_configured_model_and_json_format(mock_ollama):
    seen = {}
    def handler(req):
        import json
        seen.update(json.loads(req.content)); return chat_reply(GOOD_EXPLANATION)
    mock_ollama(handler)
    explain()
    assert seen["model"] == "qwen2.5:3b-instruct" and seen["format"] == "json" and seen["stream"] is False


def test_connection_failure(mock_ollama):
    def boom(req): raise httpx.ConnectError("refused")
    mock_ollama(boom)
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "unavailable" and "ollama serve" in e.value.hint


def test_timeout(mock_ollama):
    def slow(req): raise httpx.ReadTimeout("slow")
    mock_ollama(slow)
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "timeout"


def test_model_missing(mock_ollama):
    mock_ollama(lambda req: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "model_missing" and "ollama pull qwen2.5:3b-instruct" in e.value.hint


def test_malformed_http_body(mock_ollama):
    mock_ollama(lambda req: httpx.Response(200, text="<html>not json</html>"))
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "bad_response"


def test_malformed_model_json_is_retried_then_fails(mock_ollama):
    calls = []
    def handler(req): calls.append(1); return chat_reply("this is not json")
    mock_ollama(handler)
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "invalid_output" and len(calls) == 2  # 1 try + AI_MAX_RETRIES(1)


def test_retry_can_recover(mock_ollama):
    replies = iter(["garbage", GOOD_EXPLANATION])
    mock_ollama(lambda req: chat_reply(next(replies)))
    assert explain().summary


def test_invalid_structure_rejected(mock_ollama):
    mock_ollama(lambda req: chat_reply({"summary": "short"}))  # summary too short
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "invalid_output"


def test_invented_numbers_are_rejected(mock_ollama):
    bad = {**GOOD_EXPLANATION, "summary": "Acme raised 45 million dollars last year and is growing fast."}
    mock_ollama(lambda req: chat_reply(bad))
    with pytest.raises(ai_service.AIError) as e: explain()
    assert e.value.code == "invalid_output" and "45" in e.value.hint


def test_string_lists_are_coerced(mock_ollama):
    mock_ollama(lambda req: chat_reply({**GOOD_EXPLANATION, "positive_factors": "Single string"}))
    assert explain().positive_factors == ["Single string"]


def test_check_status_variants(mock_ollama):
    mock_ollama(lambda req: httpx.Response(200, json={"models": [{"name": "qwen2.5:3b-instruct"}]}))
    s = ai_service.check_status(); assert s["reachable"] and s["model_available"]
    mock_ollama(lambda req: httpx.Response(200, json={"models": [{"name": "llama3:8b"}]}))
    s = ai_service.check_status(); assert s["reachable"] and not s["model_available"] and "ollama pull" in s["message"]
    def down(req): raise httpx.ConnectError("x")
    mock_ollama(down)
    s = ai_service.check_status(); assert not s["reachable"] and "not reachable" in s["message"]


def test_outreach_rejects_fabricated_history(mock_ollama):
    from app.services import outreach_service
    bad = {**GOOD_OUTREACH, "body": "Hello, as we discussed last week I researched your company and loved it. Let's talk?"}
    mock_ollama(lambda req: chat_reply(bad))
    with pytest.raises(ai_service.AIError) as e:
        outreach_service.generate_draft(LEAD, "Sam", "email", "friendly", "short", "intro call")
    assert e.value.code == "invalid_output"


def test_outreach_ok_sets_channel_and_subject_rules(mock_ollama):
    from app.services import outreach_service
    mock_ollama(lambda req: chat_reply({**GOOD_OUTREACH, "channel": "whatever"}))
    out = outreach_service.generate_draft(LEAD, "Sam", "linkedin", "concise", "short", "intro call")
    assert out.channel == "linkedin" and out.subject is None
