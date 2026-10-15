"""SQLAlchemy models. All timestamps are naive UTC."""
from datetime import datetime, timezone

from sqlalchemy import (JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Index,
                        Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role:
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    ALL = (ADMIN, MANAGER, SALES_REP)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.SALES_REP)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (Index("ix_leads_owner_status", "owner_id", "status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    job_title: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(255))
    annual_revenue: Mapped[int | None] = mapped_column(BigInteger)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(80))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)  # pipeline stage
    qualification_category: Mapped[str | None] = mapped_column(String(30), index=True)
    score: Mapped[int | None] = mapped_column(Integer, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", foreign_keys=[owner_id])
    analyses = relationship("LeadAnalysis", cascade="all, delete-orphan", passive_deletes=True)
    outreach_drafts = relationship("OutreachDraft", cascade="all, delete-orphan", passive_deletes=True)
    follow_ups = relationship("FollowUp", cascade="all, delete-orphan", passive_deletes=True)


class IcpProfile(Base):
    __tablename__ = "icp_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    config: Mapped[dict] = mapped_column(JSON)  # criteria, weights, exclusions, thresholds
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class LeadAnalysis(Base):
    __tablename__ = "lead_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    icp_id: Mapped[int | None] = mapped_column(ForeignKey("icp_profiles.id", ondelete="SET NULL"))
    icp_snapshot: Mapped[dict] = mapped_column(JSON)  # ICP config used, for reproducibility
    score: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30))
    breakdown: Mapped[dict] = mapped_column(JSON)
    ai_status: Mapped[str] = mapped_column(String(20), default="not_requested")  # not_requested|completed|failed
    ai_explanation: Mapped[dict | None] = mapped_column(JSON)
    ai_error: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(120))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("outreach_drafts.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(20))
    tone: Mapped[str] = mapped_column(String(20))
    length: Mapped[str] = mapped_column(String(20))
    objective: Mapped[str] = mapped_column(String(300))
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    personalization_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|approved|superseded
    model_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class FollowUp(Base):
    __tablename__ = "follow_ups"
    __table_args__ = (Index("ix_followups_assignee_status_due", "assigned_user_id", "status", "due_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    status: Mapped[str] = mapped_column(String(15), default="open")  # open|completed|cancelled
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ActivityLog(Base):
    """Append-only audit trail. No API exists to modify or delete rows."""
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    lead_id: Mapped[int | None] = mapped_column(Integer, index=True)  # no FK: survives lead deletion
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

    @property
    def actor_email(self) -> str | None:
        return self.actor.email if self.actor else None
