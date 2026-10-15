import io
import json

CSV = (b"company_name,email,industry,employee_count,location,description\n"
       b"Alpha GmbH,a@alpha.example,Software,100,Berlin Germany,B2B SaaS\n"
       b"Beta AG,,Logistics,200,Vienna Austria,automation\n"
       b",bad,Retail,x,Rome,\n")


def upload(client, h, path, content=CSV, **data):
    return client.post(f"/api/v1/imports/{path}", headers=h, data=data,
                       files={"file": ("leads.csv", io.BytesIO(content), "text/csv")})


def test_template_download(client, rep):
    r = client.get("/api/v1/imports/template", headers=rep)
    assert r.status_code == 200 and r.text.startswith("company_name,")


def test_preview_reports_valid_invalid(client, rep):
    r = upload(client, rep, "preview")
    j = r.json()
    assert r.status_code == 200 and (j["valid_count"], j["invalid_count"], j["duplicate_count"]) == (2, 1, 0)
    bad = [x for x in j["rows"] if x["status"] == "invalid"][0]
    assert any("company_name" in e for e in bad["errors"])
    assert client.get("/api/v1/leads", headers=rep).json()["total"] == 0  # preview never writes


def test_confirm_imports_valid_rows_and_scores_them(client, rep):
    r = upload(client, rep, "confirm")
    assert r.status_code == 200 and r.json()["imported"] == 2 and r.json()["skipped_invalid"] == 1
    items = client.get("/api/v1/leads", headers=rep).json()["items"]
    assert len(items) == 2 and all(i["score"] is not None and i["source"] == "csv_import" for i in items)


def test_reimport_detects_duplicates(client, rep):
    upload(client, rep, "confirm")
    j = upload(client, rep, "preview").json()
    assert j["duplicate_count"] == 2
    r = upload(client, rep, "confirm").json()
    assert r["imported"] == 0 and r["skipped_duplicates"] == 2


def test_corrections_and_exclusions(client, rep):
    j = upload(client, rep, "preview").json()
    bad_row = [x for x in j["rows"] if x["status"] == "invalid"][0]["row_number"]
    fix = {str(bad_row): {"company_name": "Fixed Co", "email": "f@fixed.example", "employee_count": "10"}}
    r = upload(client, rep, "confirm", corrections=json.dumps(fix), exclude_rows=json.dumps([j["rows"][0]["row_number"]]))
    assert r.json()["imported"] == 2 and r.json()["excluded_by_user"] == 1


def test_bad_files_rejected_with_clear_errors(client, rep):
    for content, needle in [(b"", "empty"), (b"email,industry\na@b.co,x\n", "company_name"), (b"company_name\n", "no data rows"),
                            (b"\x00\x01\x02", "text CSV")]:
        r = upload(client, rep, "preview", content=content)
        assert r.status_code == 422 and needle in r.json()["detail"], (content, r.text)


def test_oversized_upload_rejected(client, rep, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    assert upload(client, rep, "preview").status_code == 413


def test_import_requires_auth(client):
    r = client.post("/api/v1/imports/preview", files={"file": ("a.csv", b"company_name\nA\n")})
    assert r.status_code == 401
