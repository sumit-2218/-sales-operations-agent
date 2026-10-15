# REST API (prefix `/api/v1`)
Interactive docs: http://localhost:8000/docs. Auth: `Authorization: Bearer <token>` from `POST /auth/login`. Lists return `{items,total,page,page_size}` (`page`, `page_size≤100`). Errors: `{"detail": "..."}`; validation errors: array; AI errors: `{"detail": {"code","message","hint"}}` with HTTP 503.

| Group | Endpoint | Roles |
|---|---|---|
| Health | `GET /health`, `/health/database` (503 if down), `/health/ai` | public |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/logout`; `GET/PATCH /auth/me` | public / any |
| Dashboard | `GET /dashboard/summary`, `/dashboard/activity` | any (scoped) |
| Leads | `GET/POST /leads`, `GET /leads/export.csv`, `GET/PATCH/DELETE /leads/{id}`, `GET /leads/{id}/activity` | any (own; mgr/admin all) |
| Import | `GET /imports/template`, `POST /imports/preview`, `POST /imports/confirm` (multipart: `file`, `mapping`, `corrections`, `exclude_rows`, `skip_duplicates`) | any |
| ICP | `GET/POST /icp`, `GET /icp/default-config`, `GET/PATCH/DELETE /icp/{id}` | owner |
| Qualification | `POST /leads/{id}/score`, `GET /leads/{id}/analyses`, `POST /leads/{id}/analyze` (`{analysis_id}` retries the AI step) | any |
| Outreach | `POST/GET /leads/{id}/outreach`, `PATCH /outreach/{id}`, `POST /outreach/{id}/regenerate` | any |
| Follow-ups | `GET/POST /follow-ups`, `GET/PATCH/DELETE /follow-ups/{id}` | any (scoped) |
| Admin | `GET /admin/users`, `PATCH /admin/users/{id}`, `GET /admin/system-status`, `/admin/statistics`, `/admin/activity` | admin only |

Lead list filters: `q, status, category, industry, location, min_score, max_score, owner_id, sort_by (created_at|updated_at|company_name|score|status|industry|location), sort_dir`. Follow-up filters: `status, priority, assigned_user_id, lead_id, due_before, due_after, overdue`.
Statuses: new, qualified, contacted, interested, meeting_scheduled, follow_up_required, converted, unqualified (invalid transitions → 409). Qualification categories: strong_match, potential_match, weak_match, excluded, review_required.
This is the final route set; it differs from the BRD's suggestion only by the additions `GET /leads/export.csv`, `GET /leads/{id}/activity`, `GET /icp/default-config`, `PATCH /auth/me`.
