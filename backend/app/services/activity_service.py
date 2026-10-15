from sqlalchemy.orm import Session

from ..models.models import ActivityLog, User

_SENSITIVE = ("password", "token", "secret", "authorization", "api_key")


def _clean(meta: dict | None) -> dict | None:
    if not meta:
        return None
    out = {}
    for k, v in meta.items():
        if any(x in k.lower() for x in _SENSITIVE):
            continue
        out[k] = v[:200] if isinstance(v, str) else v
    return out or None


def log_activity(db: Session, actor: User | None, action: str, entity_type: str,
                 entity_id: int | None = None, lead_id: int | None = None, meta: dict | None = None) -> None:
    """Adds an audit row to the session; the caller commits (so it is atomic with the business change)."""
    db.add(ActivityLog(actor_id=actor.id if actor else None, action=action, entity_type=entity_type,
                       entity_id=entity_id, lead_id=lead_id, meta=_clean(meta)))
