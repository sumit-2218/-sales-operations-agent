import os

# Must be set before the app is imported: tests always use an isolated in-memory SQLite database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-test-secret-123456"
os.environ["OLLAMA_BASE_URL"] = "http://ollama.test"

import json  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import User  # noqa: E402
from app.services import ai_service  # noqa: E402

PASSWORD = "Password123"


@pytest.fixture(autouse=True)
def _tables():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def user_headers(client):
    """user_headers(role) -> (auth headers, user id). Creates the user directly in the DB, then logs in."""
    counter = {"n": 0}

    def make(role="sales_rep"):
        counter["n"] += 1
        email = f"{role}{counter['n']}@example.com"
        with SessionLocal() as db:
            u = User(name=f"{role} {counter['n']}", email=email, password_hash=hash_password(PASSWORD), role=role)
            db.add(u)
            db.commit()
            uid = u.id
        r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}, uid

    return make


@pytest.fixture
def rep(user_headers):
    return user_headers("sales_rep")[0]


@pytest.fixture
def admin(user_headers):
    return user_headers("admin")[0]


from helpers import LEAD  # noqa: E402


@pytest.fixture
def lead_payload():
    return dict(LEAD)


@pytest.fixture
def mock_ollama(monkeypatch):
    """install(handler) routes all Ollama HTTP traffic to `handler(request) -> httpx.Response`."""
    def install(handler):
        monkeypatch.setattr(ai_service, "_client",
                            lambda timeout=None: httpx.Client(base_url="http://ollama.test",
                                                              transport=httpx.MockTransport(handler), timeout=5))
    return install


def chat_reply(obj) -> httpx.Response:
    content = obj if isinstance(obj, str) else json.dumps(obj)
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


GOOD_EXPLANATION = {
    "summary": "Acme Automation matches the target industry and location of the profile.",
    "positive_factors": ["Industry is a target industry"], "negative_factors": [],
    "missing_information": ["Website not provided"], "recommended_next_steps": ["Confirm the buying contact"],
    "data_limitations": ["Only fields in the lead record were considered"]}
GOOD_OUTREACH = {"subject": "Introduction", "channel": "email",
                 "body": "Hello Lena,\n\nI'm reaching out to introduce myself. Would you be open to a short intro call?\n\nBest regards,\nSam",
                 "personalization_note": "Used the company name and industry from the lead record."}
