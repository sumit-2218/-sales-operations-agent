# Sales Operations Agent

A standalone, locally-run sales operations app: import leads from CSV, define an Ideal Customer Profile (ICP), score leads with **transparent rules**, get **AI-written explanations and outreach drafts from a local model**, track a lightweight pipeline and follow-ups, and administer users.

* Frontend: React + TypeScript + Vite + Tailwind CSS
* Backend: Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic
* Database: MySQL 8.x (SQLite is used only by automated tests)
* AI: Ollama running `qwen2.5:3b-instruct` on your own machine. **No cloud AI is used; there is no fallback to one.**
* All sample data is **fictional** (`sample_data/`).

> ## ⚠️ Verification status — read this first
> This project was written in an environment **without network access, MySQL, or Ollama**, so the dependencies could not be installed and the app **has never been started**.
> * ✅ Actually executed and passing: 27 stdlib unit tests (scoring engine, CSV parser/validation, AI-output guard) and a syntax check of every Python file.
> * ❌ Written but **not executed**: the 64 backend pytest tests (API, auth, DB, mocked Ollama, end-to-end workflow), the 25 frontend tests, the TypeScript build, Alembic migrations, MySQL, and the real model.
> Expect to fix a few small issues on first run. See [docs/testing.md](docs/testing.md) for exactly what was and wasn't verified, and the steps to verify it on your Mac.

## Features
Dashboard (live DB statistics) · lead CRUD with search/filter/sort/pagination · CSV import with column mapping, preview, per-row errors, in-page corrections, duplicate detection, transactional commit · ICP editor with explanations · deterministic 0–100 scoring with per-criterion breakdown, exclusion rules and a "review required" state for thin data · AI explanation of a score (cannot change the score) · AI outreach drafts (email / LinkedIn / follow-up; editable, regenerate keeps history; never sent) · pipeline statuses with validated transitions · follow-up tasks with overdue calculation · activity log · admin panel (users, statistics, system status, activity) · role-based authorization enforced on the backend.

## Prerequisites (macOS, Apple Silicon)
Install [Homebrew](https://brew.sh) first, then:
```bash
brew install python@3.12 node git
brew install --cask ollama            # or: brew install ollama
# MySQL 8.x - choose ONE:
brew install mysql@8.4 && brew services start mysql@8.4
echo 'export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
#   ...or use Docker Desktop (see "MySQL via Docker" below)
```
Python 3.11+ and Node 20+ are required.

## 1. Database
```bash
# edit database/init.sql first: replace CHANGE_ME_DB_PASSWORD with your own password
mysql -u root -p < database/init.sql         # creates DB `sales_agent` and the dedicated user `salesagent`
```
The app never uses the root account. **MySQL via Docker (alternative):**
`MYSQL_ROOT_PASSWORD=... MYSQL_APP_PASSWORD=... docker compose up -d db`

## 2. Configuration
```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # paste the output as JWT_SECRET
```
Edit `.env`: set `DATABASE_URL` (same password as step 1) and `JWT_SECRET`. The backend refuses to start with a placeholder secret. `.env` is git-ignored.

## 3. Local AI (Ollama)
```bash
ollama pull qwen2.5:3b-instruct              # one-time download (~2 GB); the app never downloads models itself
curl http://localhost:11434/api/tags         # if this answers, Ollama is already running - do NOT start a second server
ollama serve                                 # only if the curl above failed (the Ollama desktop app also starts it)
ollama list                                  # confirm qwen2.5:3b-instruct is listed
```

## 4. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                         # creates all tables
python -m app.seed --admin --demo            # prompts for an admin email/password; loads default ICP + 20 fictional leads
uvicorn app.main:app --reload --port 8000
```
API docs (Swagger): http://localhost:8000/docs · health: http://localhost:8000/api/v1/health
`--admin` and `--demo` are repeatable and never create duplicates. For non-interactive use set `ADMIN_EMAIL`/`ADMIN_PASSWORD` in the environment. There are **no built-in credentials**.

## 5. Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev                                  # http://localhost:5173
```
Sign in with the admin you created. New self-registered users are Sales Representatives; promote them in **Admin → Users**. Set `ALLOW_REGISTRATION=false` to disable self-registration.

## Start order
MySQL → Ollama (optional; only AI features need it) → backend → frontend.

## Tests
```bash
cd backend && source .venv/bin/activate && pytest -q          # 64 pytest tests + the 27 stdlib tests (all with mocked Ollama)
cd frontend && npm test                                       # 25 Vitest cases
cd frontend && npm run build                                  # type-checks + builds
```
Backend tests use an in-memory SQLite database and never touch your MySQL data. See [docs/testing.md](docs/testing.md) for the **manual real-model test procedure**.

## Roles
| Role | Access |
|---|---|
| Sales rep | Own leads, imports, scoring, AI, outreach, follow-ups, own ICPs |
| Manager | Everything a rep can do, across all leads; can reassign leads and assign follow-ups |
| Admin | Manager rights + user management, statistics, system status, global activity log |

## Troubleshooting
| Problem | Fix |
|---|---|
| `JWT_SECRET must be set…` / validation error on start | Fill in `.env` (project root). Secrets starting with `CHANGE_ME` are rejected. |
| `Can't connect to MySQL` / `Access denied` | Is MySQL running (`brew services list`)? Does `DATABASE_URL` match the user/password from `init.sql`? Use `127.0.0.1` not `localhost` if you get socket errors. |
| `cryptography` / `caching_sha2_password` error | `pip install cryptography` (already in requirements). |
| `alembic upgrade head` fails | Check `DATABASE_URL`; the DB must exist and the user needs privileges on it. Re-run after fixing — it is safe to repeat. |
| Port 8000 / 5173 in use | `lsof -i :8000`, stop the process, or `uvicorn … --port 8001` and set `VITE_API_BASE_URL` in `frontend/.env`. |
| Browser shows CORS error | Add your frontend origin to `CORS_ORIGINS` in `.env` and restart the backend. |
| `pip install` fails building a wheel | Use Python 3.12 from Homebrew; `pip install --upgrade pip`. |
| `npm install` fails | Use Node 20+; delete `node_modules` and retry. |
| AI actions say "Ollama is not running" | `curl http://localhost:11434/api/tags`; if it fails start the Ollama app or `ollama serve`. Scoring, leads, imports and follow-ups still work. |
| AI says model is missing | `ollama pull qwen2.5:3b-instruct` (or change `OLLAMA_MODEL`). |
| AI is slow / times out | The first call loads the model into memory (slow). Raise `OLLAMA_TIMEOUT_SECONDS`, close other heavy apps, or lower `OLLAMA_NUM_PREDICT`. Real latency has **not** been measured. |
| "The model's answer did not pass validation" | The guard rejects invented numbers/emails/URLs and fake-history phrases. Retry; small models sometimes need 2 attempts. |

## Project layout
`backend/app` (api/routes, services, models, schemas, core) · `backend/alembic` · `backend/tests` · `frontend/src` · `database/` · `sample_data/` · `docs/`. Architecture: [docs/architecture.md](docs/architecture.md). API reference: [docs/api.md](docs/api.md).

## Optional integrations: Google sign-in and email
See [`docs/GOOGLE_EMAIL_SETUP.md`](docs/GOOGLE_EMAIL_SETUP.md) for Google Identity Services and SMTP configuration. Google sign-in verifies the ID token on the backend. Outreach email sending is an explicit user action after reviewing the draft. Automatically replying to inbound lead responses is not enabled by this update because it requires a connected inbox and inbound-event handling; see the guide before designing that workflow.
