"""DB side of CSV import (parsing/validation lives in csv_parser.py)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.models import Lead, User
from . import csv_parser
from .qualification_service import apply_score, resolve_icp, score_with_config
from .activity_service import log_activity


def existing_keys(db: Session, rows: list[dict]) -> set[str]:
    names = list({(r["raw"].get("company_name") or "").strip().lower() for r in rows if r["raw"].get("company_name")})
    keys: set[str] = set()
    for i in range(0, len(names), 500):
        chunk = names[i:i + 500]
        q = select(func.lower(Lead.company_name), func.lower(Lead.email)).where(func.lower(Lead.company_name).in_(chunk))
        for name, email in db.execute(q):
            keys.add(csv_parser.dedupe_key(name, email))
    return keys


def find_duplicate(db: Session, company_name: str, email: str | None, exclude_id: int | None = None) -> Lead | None:
    q = select(Lead).where(func.lower(Lead.company_name) == company_name.strip().lower())
    q = q.where(Lead.email.is_(None) if not email else func.lower(Lead.email) == email.strip().lower())
    if exclude_id:
        q = q.where(Lead.id != exclude_id)
    return db.scalars(q).first()


def insert_leads(db: Session, user: User, valid_rows: list[dict], source: str = "csv_import") -> list[Lead]:
    """Adds scored leads to the session (caller commits, so the whole import is one transaction)."""
    config, _ = resolve_icp(db, user)
    leads = []
    for r in valid_rows:
        d = {k: v for k, v in r["data"].items()}
        lead = Lead(**d, owner_id=user.id, source=source, status="new")
        apply_score(lead, score_with_config(lead, config))
        leads.append(lead)
    db.add_all(leads)
    return leads
