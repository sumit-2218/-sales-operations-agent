from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.models import FollowUp, Lead, User, utcnow
from ...schemas.schemas import FollowUpIn, FollowUpOut, FollowUpPatch, Page, _to_utc_naive
from ...services.access import follow_up_scope, get_lead_or_404, is_privileged
from ...services.activity_service import log_activity
from ..deps import PageParams, get_current_user, paginate

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


def _get(db: Session, fid: int, user: User) -> FollowUp:
    f = db.scalars(follow_up_scope(select(FollowUp).join(Lead, Lead.id == FollowUp.lead_id), user)
                   .where(FollowUp.id == fid)).first()
    if not f:
        raise HTTPException(404, "Follow-up not found")
    return f


def _check_assignee(db: Session, user: User, assignee_id: int):
    if assignee_id != user.id:
        if not is_privileged(user):
            raise HTTPException(403, "You can only assign follow-ups to yourself")
        target = db.get(User, assignee_id)
        if not target or not target.is_active:
            raise HTTPException(422, "assigned_user_id does not refer to an active user")


@router.get("", response_model=Page[FollowUpOut])
def list_follow_ups(status: Literal["open", "completed", "cancelled"] | None = None,
                    priority: Literal["low", "medium", "high"] | None = None, assigned_user_id: int | None = None,
                    lead_id: int | None = None, due_before: datetime | None = None, due_after: datetime | None = None,
                    overdue: bool | None = None, sort_dir: Literal["asc", "desc"] = "asc",
                    p: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = follow_up_scope(select(FollowUp).join(Lead, Lead.id == FollowUp.lead_id), user)
    if status:
        stmt = stmt.where(FollowUp.status == status)
    if priority:
        stmt = stmt.where(FollowUp.priority == priority)
    if assigned_user_id is not None:
        stmt = stmt.where(FollowUp.assigned_user_id == assigned_user_id)
    if lead_id is not None:
        stmt = stmt.where(FollowUp.lead_id == lead_id)
    if due_before:
        stmt = stmt.where(FollowUp.due_at <= _to_utc_naive(due_before))
    if due_after:
        stmt = stmt.where(FollowUp.due_at >= _to_utc_naive(due_after))
    if overdue is True:
        stmt = stmt.where(FollowUp.status == "open", FollowUp.due_at < utcnow())
    elif overdue is False:
        stmt = stmt.where(~((FollowUp.status == "open") & (FollowUp.due_at < utcnow())))
    stmt = stmt.order_by(FollowUp.due_at.asc() if sort_dir == "asc" else FollowUp.due_at.desc(), FollowUp.id)
    return paginate(db, stmt, p)


@router.post("", response_model=FollowUpOut, status_code=201)
def create_follow_up(body: FollowUpIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, body.lead_id, user)
    assignee = body.assigned_user_id or user.id
    _check_assignee(db, user, assignee)
    f = FollowUp(lead_id=lead.id, assigned_user_id=assignee, title=body.title.strip(), description=body.description,
                 due_at=body.due_at, priority=body.priority, status="open")
    db.add(f)
    db.flush()
    log_activity(db, user, "followup.created", "follow_up", f.id, lead.id, {"title": f.title})
    db.commit()
    return f


@router.get("/{follow_up_id}", response_model=FollowUpOut)
def get_follow_up(follow_up_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get(db, follow_up_id, user)


@router.patch("/{follow_up_id}", response_model=FollowUpOut)
def update_follow_up(follow_up_id: int, body: FollowUpPatch, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    f = _get(db, follow_up_id, user)
    changes = body.model_dump(exclude_unset=True)
    for required in ("title", "due_at"):
        if required in changes and changes[required] is None:
            raise HTTPException(422, f"{required} cannot be empty")
    if changes.get("assigned_user_id") is not None:
        _check_assignee(db, user, changes["assigned_user_id"])
    new_status = changes.pop("status", None)
    for k, v in changes.items():
        setattr(f, k, v)
    action = "followup.updated"
    if new_status and new_status != f.status:
        f.status = new_status
        f.completed_at = utcnow() if new_status == "completed" else None
        action = {"completed": "followup.completed", "cancelled": "followup.cancelled", "open": "followup.reopened"}[new_status]
    log_activity(db, user, action, "follow_up", f.id, f.lead_id, {"title": f.title})
    db.commit()
    return f


@router.delete("/{follow_up_id}", status_code=204)
def delete_follow_up(follow_up_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = _get(db, follow_up_id, user)
    log_activity(db, user, "followup.deleted", "follow_up", f.id, f.lead_id, {"title": f.title})
    db.delete(f)
    db.commit()
    return Response(status_code=204)
