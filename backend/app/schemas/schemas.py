"""Pydantic request/response schemas."""
import re
from datetime import datetime, timezone
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import (BaseModel, ConfigDict, Field, PlainSerializer, computed_field,
                      field_validator, model_validator)

from ..models.models import utcnow

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Output datetimes are naive UTC in the DB; serialise with a trailing Z so browsers parse them correctly.
OutDt = Annotated[datetime, PlainSerializer(lambda d: d.isoformat() + "Z", return_type=str)]
T = TypeVar("T")


def _clean_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v) or len(v) > 255:
        raise ValueError("Enter a valid email address")
    return v


def _to_utc_naive(v: datetime) -> datetime:
    return v.astimezone(timezone.utc).replace(tzinfo=None) if v.tzinfo else v


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


# ---- auth / users ----
class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return _clean_email(v)

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        if not v.strip():
            raise ValueError("Name is required")
        return v.strip()


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: OutDt


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfilePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=72)


class AdminUserPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Literal["admin", "manager", "sales_rep"] | None = None
    is_active: bool | None = None


# ---- leads ----
LEAD_STATUSES = ("new", "qualified", "contacted", "interested", "meeting_scheduled",
                 "follow_up_required", "converted", "unqualified")
LeadStatus = Literal["new", "qualified", "contacted", "interested", "meeting_scheduled",
                     "follow_up_required", "converted", "unqualified"]


class LeadFields(BaseModel):
    contact_name: str | None = Field(default=None, max_length=255)
    email: str | None = None
    job_title: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    employee_count: int | None = Field(default=None, ge=0, le=10_000_000)
    location: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    annual_revenue: int | None = Field(default=None, ge=0, le=10**13)
    description: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("*", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else (v.strip() if isinstance(v, str) else v)

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return _clean_email(v) if v else v


class LeadCreate(LeadFields):
    company_name: str = Field(min_length=1, max_length=255)
    owner_id: int | None = None


class LeadUpdate(LeadFields):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    owner_id: int | None = None
    status: LeadStatus | None = None


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_name: str
    contact_name: str | None
    email: str | None
    job_title: str | None
    industry: str | None
    employee_count: int | None
    location: str | None
    website: str | None
    annual_revenue: int | None
    description: str | None
    source: str | None
    owner_id: int | None
    status: str
    qualification_category: str | None
    score: int | None
    notes: str | None
    created_at: OutDt
    updated_at: OutDt


# ---- ICP ----
WEIGHT_KEYS = {"industry", "company_size", "location", "revenue", "keywords"}


class IcpConfig(BaseModel):
    target_industries: list[str] = []
    excluded_industries: list[str] = []
    min_employees: int | None = Field(default=None, ge=0)
    max_employees: int | None = Field(default=None, ge=0)
    target_locations: list[str] = []
    min_revenue: float | None = Field(default=None, ge=0)
    max_revenue: float | None = Field(default=None, ge=0)
    keywords: list[str] = []
    excluded_keywords: list[str] = []
    weights: dict[str, float] = {"industry": 30, "company_size": 25, "location": 15, "revenue": 10, "keywords": 20}
    strong_threshold: int = Field(default=80, ge=0, le=100)
    potential_threshold: int = Field(default=60, ge=0, le=100)
    min_evaluable_weight_pct: float = Field(default=50.0, ge=0, le=100)

    @field_validator("target_industries", "excluded_industries", "target_locations", "keywords", "excluded_keywords")
    @classmethod
    def _strip_lists(cls, v):
        return [x.strip() for x in v if x and x.strip()][:100]

    @field_validator("weights")
    @classmethod
    def _weights(cls, v):
        if not set(v) <= WEIGHT_KEYS:
            raise ValueError(f"Unknown weight(s): {sorted(set(v) - WEIGHT_KEYS)}")
        if any(x < 0 or x > 1000 for x in v.values()):
            raise ValueError("Weights must be between 0 and 1000")
        if sum(v.values()) <= 0:
            raise ValueError("At least one weight must be greater than 0")
        return v

    @model_validator(mode="after")
    def _ranges(self):
        if None not in (self.min_employees, self.max_employees) and self.min_employees > self.max_employees:
            raise ValueError("Minimum employees cannot exceed maximum employees")
        if None not in (self.min_revenue, self.max_revenue) and self.min_revenue > self.max_revenue:
            raise ValueError("Minimum revenue cannot exceed maximum revenue")
        if self.potential_threshold > self.strong_threshold:
            raise ValueError("Potential threshold cannot exceed strong threshold")
        return self


class IcpIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    config: IcpConfig
    is_active: bool = False


class IcpPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    config: IcpConfig | None = None
    is_active: bool | None = None


class IcpOut(BaseModel):
    id: int
    name: str
    owner_id: int
    is_active: bool
    config: dict[str, Any]
    explanations: list[str]
    created_at: OutDt
    updated_at: OutDt


# ---- qualification ----
class ScoreIn(BaseModel):
    icp_id: int | None = None


class AnalyzeIn(BaseModel):
    icp_id: int | None = None
    analysis_id: int | None = None  # retry the AI step of an existing analysis


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    icp_id: int | None
    score: int
    category: str
    breakdown: dict[str, Any]
    ai_status: str
    ai_explanation: dict[str, Any] | None
    ai_error: str | None
    model_name: str | None
    created_at: OutDt


# ---- outreach ----
Channel = Literal["email", "linkedin", "follow_up"]
Tone = Literal["professional", "friendly", "concise"]
Length = Literal["short", "medium", "long"]


class OutreachIn(BaseModel):
    channel: Channel = "email"
    tone: Tone = "professional"
    length: Length = "short"
    objective: str = Field(default="Introduce myself and ask whether a short introductory conversation would be useful",
                           min_length=3, max_length=300)


class OutreachRegenerateIn(BaseModel):
    channel: Channel | None = None
    tone: Tone | None = None
    length: Length | None = None
    objective: str | None = Field(default=None, min_length=3, max_length=300)


class OutreachPatch(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, min_length=1, max_length=5000)
    status: Literal["draft", "approved"] | None = None


class OutreachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    creator_id: int | None
    parent_id: int | None
    channel: str
    tone: str
    length: str
    objective: str
    subject: str | None
    body: str
    personalization_note: str | None
    status: str
    model_name: str | None
    created_at: OutDt
    updated_at: OutDt
    review_notice: str = "AI-generated draft. Review and edit before use; nothing is sent automatically."


# ---- follow-ups ----
Priority = Literal["low", "medium", "high"]
FuStatus = Literal["open", "completed", "cancelled"]


class FollowUpIn(BaseModel):
    lead_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    due_at: datetime
    assigned_user_id: int | None = None
    priority: Priority = "medium"

    @field_validator("due_at")
    @classmethod
    def _due(cls, v):
        return _to_utc_naive(v)


class FollowUpPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    due_at: datetime | None = None
    assigned_user_id: int | None = None
    priority: Priority | None = None
    status: FuStatus | None = None

    @field_validator("due_at")
    @classmethod
    def _d(cls, v):
        return _to_utc_naive(v) if v else v


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    assigned_user_id: int | None
    title: str
    description: str | None
    due_at: OutDt
    priority: str
    status: str
    completed_at: OutDt | None
    created_at: OutDt
    updated_at: OutDt

    @computed_field  # type: ignore[misc]
    @property
    def is_overdue(self) -> bool:
        return self.status == "open" and self.due_at < utcnow()


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int | None
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: int | None
    lead_id: int | None
    meta: dict[str, Any] | None
    created_at: OutDt
