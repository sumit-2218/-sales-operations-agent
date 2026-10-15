from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...database import get_db
from ...models.models import LeadAnalysis, User
from ...schemas.schemas import AnalysisOut, AnalyzeIn, Page, ScoreIn
from ...services import ai_service
from ...services.access import get_lead_or_404
from ...services.activity_service import log_activity
from ...services.qualification_service import apply_score, lead_to_dict, resolve_icp, score_with_config
from ..deps import PageParams, get_current_user, paginate

router = APIRouter(prefix="/leads", tags=["qualification"])


def _new_analysis(db, lead, user, icp_id):
    config, resolved_id = resolve_icp(db, user, icp_id)
    if config is None:
        raise HTTPException(404, "ICP not found")
    result = score_with_config(lead, config)
    apply_score(lead, result)  # deterministic score is the source of truth for the lead's cached score
    analysis = LeadAnalysis(lead_id=lead.id, icp_id=resolved_id, icp_snapshot=config, score=result.score,
                            category=result.category, breakdown=result.to_dict(), created_by=user.id)
    db.add(analysis)
    db.flush()
    return analysis


@router.post("/{lead_id}/score", response_model=AnalysisOut, status_code=201)
def score(lead_id: int, body: ScoreIn | None = None, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id, user)
    analysis = _new_analysis(db, lead, user, body.icp_id if body else None)
    log_activity(db, user, "lead.scored", "lead", lead.id, lead.id,
                 {"score": analysis.score, "category": analysis.category, "analysis_id": analysis.id})
    db.commit()
    return analysis


@router.get("/{lead_id}/analyses", response_model=Page[AnalysisOut])
def analyses(lead_id: int, p: PageParams = Depends(), user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    get_lead_or_404(db, lead_id, user)
    stmt = select(LeadAnalysis).where(LeadAnalysis.lead_id == lead_id).order_by(LeadAnalysis.id.desc())
    return paginate(db, stmt, p)


@router.post("/{lead_id}/analyze", response_model=AnalysisOut)
def analyze(lead_id: int, body: AnalyzeIn | None = None, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    """Score deterministically, then ask the local model to explain. Retry by passing analysis_id."""
    body = body or AnalyzeIn()
    lead = get_lead_or_404(db, lead_id, user)
    if body.analysis_id:
        analysis = db.get(LeadAnalysis, body.analysis_id)
        if not analysis or analysis.lead_id != lead.id:
            raise HTTPException(404, "Analysis not found")
    else:
        analysis = _new_analysis(db, lead, user, body.icp_id)
        log_activity(db, user, "lead.scored", "lead", lead.id, lead.id,
                     {"score": analysis.score, "category": analysis.category, "analysis_id": analysis.id})
    log_activity(db, user, "ai.analysis_requested", "analysis", analysis.id, lead.id)
    try:
        explanation = ai_service.explain_lead(lead_to_dict(lead), analysis.breakdown, analysis.icp_snapshot)
    except ai_service.AIError as e:
        analysis.ai_status, analysis.ai_error = "failed", e.message
        log_activity(db, user, "ai.analysis_failed", "analysis", analysis.id, lead.id, {"code": e.code})
        db.commit()  # keep the deterministic result even though the AI step failed
        raise HTTPException(503, detail=e.to_detail())
    analysis.ai_explanation = explanation.model_dump()
    analysis.ai_status, analysis.ai_error = "completed", None
    analysis.model_name = get_settings().ollama_model
    log_activity(db, user, "ai.analysis_completed", "analysis", analysis.id, lead.id, {"model": analysis.model_name})
    db.commit()
    return analysis
