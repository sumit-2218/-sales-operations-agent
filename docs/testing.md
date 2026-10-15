# Testing

## What was ACTUALLY executed (in the authoring sandbox: no network, no MySQL, no Ollama)
| Check | Result |
|---|---|
| `python -m unittest` – `test_lead_scoring.py` (10), `test_csv_parser.py` (11), `test_ai_guard.py` (6) = **27 tests** | ✅ all passed |
| `py_compile` on every backend Python file | ✅ no syntax errors |
| ZIP integrity + clean-directory extraction, then the 27 tests re-run from the extracted copy | ✅ |

## Written but NOT executed (dependencies could not be installed)
| Suite | Count | Covers |
|---|---|---|
| `backend/tests/test_auth.py` | 8 | register/login, duplicate email, disabled registration, bad credentials, expired/forged token, disabled user, password change |
| `test_leads.py` | 9 | CRUD, validation, duplicates, ownership isolation, search/filter/sort/pagination, status transitions, export formula-safety |
| `test_import.py` | 8 | template, preview, confirm, duplicates, corrections/exclusions, empty/malformed/oversized files |
| `test_icp_scoring.py` | 7 | ICP CRUD/validation/ownership, reproducible scores, exclusion beats score, rescoring |
| `test_ai_service.py` | 14 | **Mocked** Ollama: success, timeout, connection failure, missing model, malformed HTTP/JSON, retries, schema violations, invented numbers, fake-history phrases, status check |
| `test_ai_endpoints.py` | 6 | analyze/outreach persistence, AI-down behaviour, retry, history, access control |
| `test_followups_dashboard.py` | 5 | follow-up CRUD/overdue/filters/access, dashboard numbers vs DB |
| `test_admin_health.py` | 6 | admin protection, user management, system status, DB-down handling, audit-log hygiene |
| `test_e2e_workflow.py` | 1 | the 16-step principal workflow through the real API (Ollama mocked, SQLite) |
| Frontend (Vitest) | 25 | login validation, lead list/empty/error states, lead form validation, CSV import states, qualification breakdown & AI-error display, outreach editing, follow-up status updates, error mapping |

These must be run by you: `cd backend && pytest -q` and `cd frontend && npm test && npm run build`.

**Mocked AI tests prove error handling and validation logic only – NOT that the real model works.**

## Never verified (needs your Mac)
Real MySQL connection · `alembic upgrade head` on MySQL · real `qwen2.5:3b-instruct` output quality/format compliance/latency · TypeScript compilation · browser behaviour · the MySQL-down scenario against a real server (a SQLite-based simulation is in `test_admin_health.py`).

## Manual test procedure – real local model
1. `ollama pull qwen2.5:3b-instruct`; `curl http://localhost:11434/api/tags` shows it.
2. Start backend + frontend; log in; **Admin → System status** should show Database ✔ and Local AI ✔ with the model name.
3. Open a seeded lead (e.g. *Northwind Automation GmbH*) → **Qualification → Generate AI explanation**. Expect: a summary, factors and next steps; the score shown must be unchanged. Time it – the first call includes model load.
4. Read the explanation critically: every number/fact must come from the lead record. Anything invented is a failure; report it.
5. **Outreach → Generate draft** (email, then LinkedIn). Check: no claims of prior conversations or research, greeting uses the contact name only if present, call to action present, "AI-generated draft" notice visible. Edit, save, reload the page: edits persist. Click **Regenerate**: old draft becomes "superseded" and stays readable.
6. Failure drills: stop Ollama (`pkill ollama` / quit the app) → AI buttons show a clear message with the start hint while scoring/leads/follow-ups still work; restart Ollama and use **Retry**. Then `ollama rm qwen2.5:3b-instruct` (re-pull afterwards) → "model is not installed" message.
7. Optional API check: `curl -s localhost:11434/api/chat -d '{"model":"qwen2.5:3b-instruct","messages":[{"role":"user","content":"Reply with JSON {\"ok\":true}"}],"stream":false,"format":"json"}'`.
8. MySQL drill: stop MySQL → `GET /api/v1/health/database` returns 503 and the UI shows "database is unavailable"; start it again and the app recovers without restart.
