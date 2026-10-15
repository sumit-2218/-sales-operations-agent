import jwt
from app.core.config import get_settings


def test_register_login_me(client):
    r = client.post("/api/v1/auth/register", json={"name": "Ann", "email": "Ann@Example.com", "password": "Password123"})
    assert r.status_code == 201 and r.json()["role"] == "sales_rep" and "password" not in r.text
    r = client.post("/api/v1/auth/login", json={"email": "ann@example.com", "password": "Password123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "ann@example.com"


def test_register_validation_and_duplicates(client):
    assert client.post("/api/v1/auth/register", json={"name": "A", "email": "bad", "password": "Password123"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={"name": "A", "email": "a@b.co", "password": "short"}).status_code == 422
    ok = {"name": "A", "email": "a@b.co", "password": "Password123"}
    assert client.post("/api/v1/auth/register", json=ok).status_code == 201
    assert client.post("/api/v1/auth/register", json=ok).status_code == 409


def test_registration_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "allow_registration", False)
    r = client.post("/api/v1/auth/register", json={"name": "A", "email": "a@b.co", "password": "Password123"})
    assert r.status_code == 403


def test_invalid_credentials(client):
    client.post("/api/v1/auth/register", json={"name": "A", "email": "a@b.co", "password": "Password123"})
    assert client.post("/api/v1/auth/login", json={"email": "a@b.co", "password": "wrongpass1"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "nobody@b.co", "password": "Password123"}).status_code == 401


def test_protected_endpoint_requires_token(client):
    assert client.get("/api/v1/leads").status_code == 401
    assert client.get("/api/v1/leads", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_expired_and_forged_tokens_rejected(client):
    s = get_settings()
    expired = jwt.encode({"sub": "1", "iat": 1, "exp": 2}, s.jwt_secret, algorithm="HS256")
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()
    forged = jwt.encode({"sub": "1", "iat": 1, "exp": 9999999999}, "another-secret-another-secret", algorithm="HS256")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_disabled_user_cannot_use_existing_token(client, user_headers, admin):
    h, uid = user_headers("sales_rep")
    assert client.patch(f"/api/v1/admin/users/{uid}", json={"is_active": False}, headers=admin).status_code == 200
    assert client.get("/api/v1/auth/me", headers=h).status_code == 403


def test_change_password(client, rep):
    r = client.patch("/api/v1/auth/me", json={"current_password": "nope", "new_password": "NewPassword1"}, headers=rep)
    assert r.status_code == 400
    r = client.patch("/api/v1/auth/me", json={"current_password": "Password123", "new_password": "NewPassword1"}, headers=rep)
    assert r.status_code == 200
