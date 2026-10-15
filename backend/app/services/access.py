"""Ownership / visibility rules. Sales reps see only their own records; managers and admins see all."""
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.models import FollowUp, Lead, Role, User


def is_privileged(user: User) -> bool:
    return user.role in (Role.ADMIN, Role.MANAGER)


def lead_scope(stmt, user: User):
    return stmt if is_privileged(user) else stmt.where(Lead.owner_id == user.id)


def follow_up_scope(stmt, user: User):
    """`stmt` must already join Lead."""
    if is_privileged(user):
        return stmt
    return stmt.where(or_(FollowUp.assigned_user_id == user.id, Lead.owner_id == user.id))


def get_lead_or_404(db: Session, lead_id: int, user: User) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead or (not is_privileged(user) and lead.owner_id != user.id):
        raise HTTPException(404, "Lead not found")  # 404 (not 403) so other users' ids are not revealed
    return lead
