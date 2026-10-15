from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ...core.config import get_settings
from ...database import get_db
from ...models.models import (ActivityLog, FollowUp, Lead, LeadAnalysis, OutreachDraft, Role, User)
from ...schemas.schemas import ActivityOut, AdminUserPatch, Page, UserOut
from ...services import ai_service
from ...services.activity_service import log_activity
from ..deps import PageParams, paginate, require_roles
from .health import db_status

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(Role.ADMIN))])


@router.get("/users", response_model=Page[UserOut])
def users(p: PageParams = Depends(), db: Session = Depends(get_db)):
    return paginate(db, select(User).order_by(User.id), p)


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(user_id: int, body: AdminUserPatch, admin: User = Depends(require_roles(Role.ADMIN)),
               db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    changes = body.model_dump(exclude_unset=True)
    if target.id == admin.id and (changes.get("is_active") is False or ("role" in changes and changes["role"] != Role.ADMIN)):
        raise HTTPException(409, "You cannot disable or demote your own account")
    for k, v in changes.items():
        if v is not None:
            setattr(target, k, v)
    log_activity(db, admin, "admin.user_updated", "user", target.id, meta={k: v for k, v in changes.items()})
    db.commit()
    return target


@router.get("/system-status")
def system_status():
    s = get_settings()
    return {"application": {"status": "ok"}, "database": db_status(), "ai": ai_service.check_status(),
            "config": {"model": s.ollama_model, "ollama_base_url": s.ollama_base_url,
                       "registration_enabled": s.allow_registration, "max_upload_mb": s.max_upload_mb}}


@router.get("/statistics")
def statistics(db: Session = Depends(get_db)):
    count = lambda col: db.scalar(select(func.count(col))) or 0
    grouped = lambda col: {k or "none": v for k, v in db.execute(select(col, func.count()).group_by(col)).all()}
    return {"users": {"total": count(User.id), "active": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
                      "by_role": grouped(User.role)},
            "leads": {"total": count(Lead.id), "by_status": grouped(Lead.status), "by_category": grouped(Lead.qualification_category)},
            "analyses": {"total": count(LeadAnalysis.id), "by_ai_status": grouped(LeadAnalysis.ai_status)},
            "outreach_drafts": count(OutreachDraft.id), "follow_ups": {"total": count(FollowUp.id), "by_status": grouped(FollowUp.status)}}


@router.get("/activity", response_model=Page[ActivityOut])
def activity(action: str | None = None, p: PageParams = Depends(), db: Session = Depends(get_db)):
    stmt = select(ActivityLog).options(selectinload(ActivityLog.actor)).order_by(ActivityLog.id.desc())
    if action:
        stmt = stmt.where(ActivityLog.action.like(f"{action}%"))
    return paginate(db, stmt, p)
