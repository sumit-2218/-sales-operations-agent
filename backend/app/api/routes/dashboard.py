from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ...database import get_db
from ...models.models import ActivityLog, FollowUp, Lead, OutreachDraft, User, utcnow
from ...schemas.schemas import ActivityOut
from ..deps import get_current_user
from ...services.access import follow_up_scope, is_privileged, lead_scope

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Every number is computed from database rows, scoped to what the caller may see."""
    now = utcnow()
    count_leads = lambda *conds: db.scalar(lead_scope(select(func.count(Lead.id)), user).where(*conds)) or 0
    by_category = dict(db.execute(lead_scope(select(Lead.qualification_category, func.count(Lead.id)), user)
                                  .group_by(Lead.qualification_category)).all())
    by_status = dict(db.execute(lead_scope(select(Lead.status, func.count(Lead.id)), user).group_by(Lead.status)).all())
    drafts = db.scalar(lead_scope(select(func.count(OutreachDraft.id)).join(Lead, Lead.id == OutreachDraft.lead_id), user)
                       .where(OutreachDraft.status != "superseded")) or 0

    def fu_count(*conds):
        return db.scalar(follow_up_scope(select(func.count(FollowUp.id)).join(Lead, Lead.id == FollowUp.lead_id), user)
                         .where(*conds)) or 0

    upcoming = db.execute(follow_up_scope(select(FollowUp, Lead.company_name).join(Lead, Lead.id == FollowUp.lead_id), user)
                          .where(FollowUp.status == "open").order_by(FollowUp.due_at).limit(5)).all()
    cat = lambda *names: sum(by_category.get(n, 0) for n in names)
    return {
        "total_leads": count_leads(),
        "new_imported_leads": count_leads(Lead.source.in_(["csv_import", "sample_data"]), Lead.created_at >= now - timedelta(days=7)),
        "qualified_leads": cat("strong_match", "potential_match"),
        "review_required_leads": cat("review_required"),
        "unqualified_leads": cat("weak_match", "excluded"),
        "unscored_leads": by_category.get(None, 0),
        "by_category": {(k or "unscored"): v for k, v in by_category.items()},
        "by_status": by_status,
        "outreach_drafts": drafts,
        "pending_follow_ups": fu_count(FollowUp.status == "open"),
        "overdue_follow_ups": fu_count(FollowUp.status == "open", FollowUp.due_at < now),
        "upcoming_follow_ups": [{"id": f.id, "title": f.title, "lead_id": f.lead_id, "company_name": name,
                                 "due_at": f.due_at.isoformat() + "Z", "priority": f.priority,
                                 "is_overdue": f.due_at < now} for f, name in upcoming],
    }


@router.get("/activity", response_model=list[ActivityOut])
def activity(limit: int = 15, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(ActivityLog).options(selectinload(ActivityLog.actor)).order_by(ActivityLog.id.desc())
    if not is_privileged(user):
        stmt = stmt.where(ActivityLog.actor_id == user.id)
    return db.scalars(stmt.limit(max(1, min(limit, 50)))).all()
