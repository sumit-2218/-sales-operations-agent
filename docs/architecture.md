# Architecture

```
React SPA ──HTTP/JSON (JWT)──▶ FastAPI ──SQLAlchemy──▶ MySQL
                                  │
                                  └──httpx (localhost only)──▶ Ollama (qwen2.5:3b-instruct)
```

## Backend layers (`backend/app`)
* `api/routes/*` – thin HTTP handlers: auth, leads, imports, icp, qualification, outreach, follow_ups, dashboard, admin, health. `api/deps.py` holds authentication, role guards, pagination.
* `services/` – business logic, no HTTP concerns:
  * `lead_scoring_service.py` – **pure, deterministic** scoring (source of truth for scores). No I/O, no AI.
  * `icp_service.py` – default ICP, ICP→scoring conversion, human-readable explanations.
  * `csv_parser.py` – CSV parsing/validation/dedupe/export-safety (stdlib only).
  * `import_service.py`, `qualification_service.py`, `access.py`, `activity_service.py` – DB glue, ownership rules, audit log.
  * `ai_service.py` – the only module that talks to Ollama (health, chat, timeouts, retries, schema validation).
  * `ai_guard.py` – rejects unsupported numbers/emails/URLs and fabricated-history phrases in model output.
  * `outreach_service.py` – prompts + validation for outreach drafts.
* `models/models.py` – SQLAlchemy models; `schemas/` – Pydantic request/response and AI-output schemas; `core/` – settings and security (bcrypt, JWT).

## Key decisions
* **Deterministic vs AI.** The score, category and breakdown come only from Python rules. The model receives them as read-only context to *explain*; AI output is stored in `lead_analyses.ai_explanation` and never writes to the lead. Missing data is excluded from scoring (not a mismatch); too little evaluable data → `review_required`; exclusions override any score.
* **Grounding.** Prompts contain only the lead fields, ICP and scoring result, wrapped as untrusted data. Output must be valid JSON matching a Pydantic schema, and is rejected (bounded retry, then a clear error) if it contains numbers/emails/URLs not present in the supplied data or phrases claiming prior contact/research. This is a heuristic guard, not a proof of truthfulness – drafts are labelled "requires human review".
* **No cloud fallback.** If Ollama is down, AI endpoints return HTTP 503 `{code, message, hint}`; everything else keeps working. The deterministic analysis row is still saved with `ai_status=failed` so the user can retry (`analysis_id`).
* **AuthZ on the server.** Reps see only leads they own (others return 404); managers/admins see all; admin routes require the admin role. Tokens are stateless JWTs (HS256, 8 h default, `sub`/`iat`/`exp` required); disabled users are rejected on every request.
* **ICP ownership.** ICPs are private to their owner; each user has at most one *active* ICP (explicit "Make active"); without one the built-in default is used. Changing/activating/deleting an ICP rescores the user's visible leads.
* **Audit log.** Append-only table written in the same transaction as the change; sensitive keys are stripped; no API can modify or delete entries. `lead_id` has no FK so history survives lead deletion.
* **Deletion.** Deleting a lead cascades (DB-level `ON DELETE CASCADE`) to analyses, drafts and follow-ups; users are never deleted (disable instead).
* **Imports** are two-step and stateless: `preview` (no writes) then `confirm` (re-uploads the file with mapping/corrections/exclusions) inside one transaction.
* **Time.** All timestamps are naive UTC in the DB and serialised with a trailing `Z`.
* **Migrations.** `0001` creates the baseline schema from the model metadata; later changes must be explicit Alembic operations.
