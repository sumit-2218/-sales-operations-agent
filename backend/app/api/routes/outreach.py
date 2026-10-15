from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...database import get_db
from ...models.models import Lead, OutreachDraft, User
from ...schemas.schemas import OutreachIn, OutreachOut, OutreachPatch, OutreachRegenerateIn, Page
from ...services import ai_service, outreach_service
from ...services.email_service import send_email, EmailDeliveryError
from ...services.access import get_lead_or_404, is_privileged
from ...services.activity_service import log_activity
from ...services.qualification_service import lead_to_dict
from ..deps import PageParams, get_current_user, paginate

router = APIRouter(tags=["outreach"])


def _generate(db, user, lead, channel, tone, length, objective, parent=None) -> OutreachDraft:
    try:
        out = outreach_service.generate_draft(lead_to_dict(lead), user.name, channel, tone, length, objective)
    except ai_service.AIError as e:
        log_activity(db, user, "ai.outreach_failed", "outreach", None, lead.id, {"code": e.code})
        db.commit()
        raise HTTPException(503, detail=e.to_detail())
    draft = OutreachDraft(lead_id=lead.id, creator_id=user.id, parent_id=parent.id if parent else None,
                          channel=channel, tone=tone, length=length, objective=objective, subject=out.subject,
                          body=out.body.strip(), personalization_note=out.personalization_note,
                          status="draft", model_name=get_settings().ollama_model)
    db.add(draft)
    db.flush()
    return draft


def _get_draft(db: Session, draft_id: int, user: User) -> tuple[OutreachDraft, Lead]:
    draft = db.get(OutreachDraft, draft_id)
    if not draft:
        raise HTTPException(404, "Draft not found")
    return draft, get_lead_or_404(db, draft.lead_id, user)


@router.post("/leads/{lead_id}/outreach", response_model=OutreachOut, status_code=201)
def create_outreach(lead_id: int, body: OutreachIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id, user)
    draft = _generate(db, user, lead, body.channel, body.tone, body.length, body.objective)
    log_activity(db, user, "outreach.created", "outreach", draft.id, lead.id, {"channel": draft.channel})
    db.commit()
    return draft


@router.get("/leads/{lead_id}/outreach", response_model=Page[OutreachOut])
def list_outreach(lead_id: int, p: PageParams = Depends(), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    get_lead_or_404(db, lead_id, user)
    stmt = select(OutreachDraft).where(OutreachDraft.lead_id == lead_id).order_by(OutreachDraft.id.desc())
    return paginate(db, stmt, p)


@router.patch("/outreach/{draft_id}", response_model=OutreachOut)
def edit_outreach(draft_id: int, body: OutreachPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft, lead = _get_draft(db, draft_id, user)
    if draft.status == "superseded":
        raise HTTPException(409, "This draft was replaced by a regenerated version and can no longer be edited")
    changes = body.model_dump(exclude_unset=True)
    if "body" in changes and not (changes["body"] or "").strip():
        raise HTTPException(422, "Message body cannot be empty")
    for k, v in changes.items():
        setattr(draft, k, v)
    log_activity(db, user, "outreach.edited", "outreach", draft.id, lead.id, {"fields": sorted(changes)})
    db.commit()
    return draft


@router.post("/outreach/{draft_id}/regenerate", response_model=OutreachOut, status_code=201)
def regenerate(draft_id: int, body: OutreachRegenerateIn | None = None, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    old, lead = _get_draft(db, draft_id, user)
    b = body or OutreachRegenerateIn()
    new = _generate(db, user, lead, b.channel or old.channel, b.tone or old.tone, b.length or old.length,
                    b.objective or old.objective, parent=old)
    old.status = "superseded"  # history is preserved: old draft stays readable, linked via parent_id
    log_activity(db, user, "outreach.regenerated", "outreach", new.id, lead.id, {"replaces": old.id})
    db.commit()
    return new


@router.post("/outreach/{draft_id}/send")
def send_outreach_email(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send only after a user explicitly clicks Send; no background auto-send."""
    draft, lead = _get_draft(db, draft_id, user)
    if draft.channel != "email":
        raise HTTPException(422, "Only email drafts can be sent")
    if not lead.email:
        raise HTTPException(422, "This lead has no email address")
    if not draft.body.strip():
        raise HTTPException(422, "Email body cannot be empty")
    try:
        send_email(lead.email, draft.subject or "Hello", draft.body)
    except EmailDeliveryError as exc:
        raise HTTPException(503, str(exc))
    log_activity(db, user, "outreach.email_sent", "outreach", draft.id, lead.id,
                 {"to": lead.email, "subject": draft.subject or "Hello"})
    db.commit()
    return {"status": "sent", "to": lead.email, "draft_id": draft.id,
            "message": "Email accepted by the configured SMTP server."}
