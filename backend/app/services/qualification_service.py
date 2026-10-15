"""Glue between DB records and the deterministic scoring engine."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.models import IcpProfile, Lead, User
from .access import lead_scope
from .icp_service import DEFAULT_ICP_CONFIG, to_icp
from .lead_scoring_service import ScoreResult, score_lead


def lead_to_dict(lead: Lead) -> dict:
    return {k: getattr(lead, k) for k in ("company_name", "contact_name", "job_title", "industry", "employee_count",
                                          "location", "annual_revenue", "website", "description")}


def resolve_icp(db: Session, user: User, icp_id: int | None = None) -> tuple[dict, int | None]:
    """Explicit icp_id > the user's active ICP > built-in default. Returns (config, icp_id)."""
    if icp_id is not None:
        icp = db.get(IcpProfile, icp_id)
        if not icp or icp.owner_id != user.id:
            return None, None  # caller turns this into a 404
        return icp.config, icp.id
    icp = db.scalars(select(IcpProfile).where(IcpProfile.owner_id == user.id, IcpProfile.is_active.is_(True))).first()
    if icp:
        return icp.config, icp.id
    return DEFAULT_ICP_CONFIG, None


def apply_score(lead: Lead, result: ScoreResult) -> None:
    lead.score = result.score
    lead.qualification_category = result.category


def score_with_config(lead: Lead, config: dict) -> ScoreResult:
    return score_lead(lead_to_dict(lead), to_icp(config))


def rescore_lead(db: Session, lead: Lead, user: User) -> None:
    config, _ = resolve_icp(db, user)
    apply_score(lead, score_with_config(lead, config))


def rescore_all(db: Session, user: User) -> int:
    """Recalculate cached score/category for every lead the user can see (after an ICP change)."""
    config, _ = resolve_icp(db, user)
    icp = to_icp(config)
    n = 0
    for lead in db.scalars(lead_scope(select(Lead), user)):
        apply_score(lead, score_lead(lead_to_dict(lead), icp))
        n += 1
    return n
