import httpx
from sqlalchemy import create_engine

from app.api.routes import health
from app.database import SessionLocal
from app.models.models import ActivityLog
from conftest import PASSWORD


def test_admin_routes_blocked_for_non_admins(client, user_headers):
    for role in ("sales_rep", "manager"):
        h, _ = user_headers(role)
        for path in ("/admin/users", "/admin/system-status", "/admin/statistics", "/admin/activity"):
            assert client.get(f"/api/v1{path}", headers=h).status_code == 403, (role, path)
        assert client.patch("/api/v1/admin/users/1", json={"role": "admin"}, headers=h).status_code == 403
    for path in ("/admin/users", "/admin/system-status"):
        assert client.get(f"/api/v1{path}").status_code == 401


def test_admin_user_management(client, admin, user_headers):
    _, uid = user_headers("sales_rep")
    users = client.get("/api/v1/admin/users", headers=admin).json()
    assert users["total"] == 2 and "password_hash" not in str(users)
    r = client.patch(f"/api/v1/admin/users/{uid}", json={"role": "manager"}, headers=admin)
    assert r.status_code == 200 and r.json()["role"] == "manager"
    assert client.patch("/api/v1/admin/users/999", json={"role": "manager"}, headers=admin).status_code == 404
    assert client.patch(f"/api/v1/admin/users/{uid}", json={"role": "superuser"}, headers=admin).status_code == 422
    me = client.get("/api/v1/auth/me", headers=admin).json()["id"]
    assert client.patch(f"/api/v1/admin/users/{me}", json={"is_active": False}, headers=admin).status_code == 409
    acts = client.get("/api/v1/admin/activity", headers=admin).json()["items"]
    assert any(a["action"] == "admin.user_updated" for a in acts)


def test_system_status_distinguishes_app_db_and_ai(client, admin, mock_ollama):
    def down(req): raise httpx.ConnectError("x")
    mock_ollama(down)
    s = client.get("/api/v1/admin/system-status", headers=admin).json()
    assert s["application"]["status"] == "ok" and s["database"]["status"] == "ok"
    assert s["ai"]["reachable"] is False and s["config"]["model"] == "qwen2.5:3b-instruct"
    assert "jwt" not in str(s).lower() and "password" not in str(s).lower()


def test_health_endpoints(client, mock_ollama):
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    assert client.get("/api/v1/health/database").status_code == 200
    def down(req): raise httpx.ConnectError("x")
    mock_ollama(down)
    r = client.get("/api/v1/health/ai")
    assert r.status_code == 200 and r.json()["reachable"] is False  # AI down != application down


def test_database_unavailable_is_reported_not_leaked(client, monkeypatch):
    monkeypatch.setattr(health, "engine", create_engine("sqlite:////nonexistent_dir_xyz/db.sqlite"))
    r = client.get("/api/v1/health/database")
    assert r.status_code == 503 and "nonexistent" not in r.text


def test_activity_log_has_no_secrets_and_no_write_api(client, rep):
    client.post("/api/v1/auth/login", json={"email": "sales_rep1@example.com", "password": PASSWORD})
    with SessionLocal() as db:
        text = " ".join(str(r.meta) for r in db.query(ActivityLog))
    assert PASSWORD not in text and "token" not in text.lower()
    for method in (client.put, client.patch, client.delete):
        assert method("/api/v1/admin/activity/1", headers=rep).status_code in (404, 405)
