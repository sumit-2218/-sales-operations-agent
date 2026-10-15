import csv
import io
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.models import ActivityLog, Lead, User
from ...schemas.schemas import ActivityOut, LeadCreate, LeadOut, LeadUpdate, Page
from ...services.access import get_lead_or_404, is_privileged, lead_scope
from ...services.activity_service import log_activity
from ...services.csv_parser import FIELDS, csv_safe
from ...services.import_service import find_duplicate
from ...services.qualification_service import rescore_lead
from ..deps import PageParams, get_current_user, paginate

router = APIRouter(prefix="/leads", tags=["leads"])

TRANSITIONS = {
    "new": {"qualified", "contacted", "unqualified"},
    "qualified": {"new", "contacted", "unqualified"},
    "contacted": {"interested", "meeting_scheduled", "follow_up_required", "unqualified"},
    "interested": {"contacted", "meeting_scheduled", "follow_up_required", "converted", "unqualified"},
    "meeting_scheduled": {"interested", "follow_up_required", "converted", "unqualified"},
    "follow_up_required": {"contacted", "interested", "meeting_scheduled", "converted", "unqualified"},
    "converted": {"follow_up_required"},
    "unqualified": {"new", "qualified"},
}
SORTABLE = {"created_at", "updated_at", "company_name", "score", "status", "industry", "location"}
SCORING_FIELDS = {"industry", "employee_count", "location", "annual_revenue", "description", "company_name"}


def _filtered(user: User, q, status, category, industry, location, min_score, max_score, owner_id):
    stmt = lead_scope(select(Lead), user)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Lead.company_name.ilike(like), Lead.contact_name.ilike(like), Lead.email.ilike(like),
                              Lead.industry.ilike(like), Lead.location.ilike(like)))
    if status:
        stmt = stmt.where(Lead.status == status)
    if category:
        stmt = stmt.where(Lead.qualification_category == category)
    if industry:
        stmt = stmt.where(Lead.industry.ilike(f"%{industry.strip()}%"))
    if location:
        stmt = stmt.where(Lead.location.ilike(f"%{location.strip()}%"))
    if min_score is not None:
        stmt = stmt.where(Lead.score >= min_score)
    if max_score is not None:
        stmt = stmt.where(Lead.score <= max_score)
    if owner_id is not None and is_privileged(user):
        stmt = stmt.where(Lead.owner_id == owner_id)
    return stmt


@router.get("", response_model=Page[LeadOut])
def list_leads(q: str | None = None, status: str | None = None, category: str | None = None,
               industry: str | None = None, location: str | None = None,
               min_score: int | None = Query(None, ge=0, le=100), max_score: int | None = Query(None, ge=0, le=100),
               owner_id: int | None = None, sort_by: str = "created_at", sort_dir: Literal["asc", "desc"] = "desc",
               p: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if sort_by not in SORTABLE:
        raise HTTPException(422, f"sort_by must be one of {sorted(SORTABLE)}")
    stmt = _filtered(user, q, status, category, industry, location, min_score, max_score, owner_id)
    col = getattr(Lead, sort_by)
    order = col.asc() if sort_dir == "asc" else col.desc()
    stmt = stmt.order_by(col.is_(None), order, Lead.id.desc())  # NULLs last on MySQL and SQLite
    return paginate(db, stmt, p)


@router.get("/export.csv")
def export_csv(q: str | None = None, status: str | None = None, category: str | None = None,
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = _filtered(user, q, status, category, None, None, None, None, None).order_by(Lead.id).limit(10000)
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["id", *FIELDS, "status", "qualification_category", "score"]
    w.writerow(cols)
    for lead in db.scalars(stmt):
        w.writerow([csv_safe(getattr(lead, c)) for c in cols])  # formula-injection safe
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="leads_export.csv"'})


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(body: LeadCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump()
    owner_id = data.pop("owner_id")
    source = data.pop("source", None) or "manual"
    if owner_id is not None and owner_id != user.id:
        if not is_privileged(user):
            raise HTTPException(403, "Only managers and administrators can assign leads to other users")
        if not db.get(User, owner_id):
            raise HTTPException(422, "owner_id does not refer to an existing user")
    if find_duplicate(db, data["company_name"], data.get("email")):
        raise HTTPException(409, "A lead with the same company name and email already exists")
    lead = Lead(**data, owner_id=owner_id or user.id, status="new", source=source)
    rescore_lead(db, lead, user)
    db.add(lead)
    db.flush()
    log_activity(db, user, "lead.created", "lead", lead.id, lead.id, {"company": lead.company_name})
    db.commit()
    return lead


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_lead_or_404(db, lead_id, user)


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, body: LeadUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id, user)
    changes = body.model_dump(exclude_unset=True)
    if "company_name" in changes and changes["company_name"] is None:
        raise HTTPException(422, "company_name cannot be empty")
    if "owner_id" in changes:
        if not is_privileged(user):
            raise HTTPException(403, "Only managers and administrators can reassign leads")
        if changes["owner_id"] is not None and not db.get(User, changes["owner_id"]):
            raise HTTPException(422, "owner_id does not refer to an existing user")
    new_status = changes.pop("status", None)
    if new_status and new_status != lead.status:
        if new_status not in TRANSITIONS[lead.status]:
            allowed = ", ".join(sorted(TRANSITIONS[lead.status]))
            raise HTTPException(409, f"Cannot move a lead from '{lead.status}' to '{new_status}'. Allowed: {allowed}")
        log_activity(db, user, "lead.status_changed", "lead", lead.id, lead.id, {"from": lead.status, "to": new_status})
        lead.status = new_status
    if {"company_name", "email"} & changes.keys():
        name = changes.get("company_name", lead.company_name)
        email = changes["email"] if "email" in changes else lead.email
        if find_duplicate(db, name, email, exclude_id=lead.id):
            raise HTTPException(409, "Another lead with the same company name and email already exists")
    for k, v in changes.items():
        setattr(lead, k, v)
    if SCORING_FIELDS & changes.keys():
        rescore_lead(db, lead, user)  # deterministic recalculation
    if changes:
        log_activity(db, user, "lead.updated", "lead", lead.id, lead.id, {"fields": sorted(changes.keys())})
    db.commit()
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id, user)
    log_activity(db, user, "lead.deleted", "lead", lead.id, lead.id, {"company": lead.company_name})
    db.delete(lead)  # analyses, drafts and follow-ups are removed with it (FK cascade)
    db.commit()
    return Response(status_code=204)


@router.get("/{lead_id}/activity", response_model=Page[ActivityOut])
def lead_activity(lead_id: int, p: PageParams = Depends(), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    get_lead_or_404(db, lead_id, user)
    stmt = select(ActivityLog).where(ActivityLog.lead_id == lead_id).order_by(ActivityLog.id.desc())
    return paginate(db, stmt, p)
