import logging

import jwt
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.security import decode_access_token
from ..database import get_db
from ..models.models import User

bearer = HTTPBearer(auto_error=False)
log = logging.getLogger(__name__)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    hdr = {"WWW-Authenticate": "Bearer"}
    if not creds:
        raise HTTPException(401, "Not authenticated", headers=hdr)
    try:
        payload = decode_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired. Please sign in again.", headers=hdr)
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid authentication token", headers=hdr)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Invalid authentication token", headers=hdr)
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled")
    return user


def require_roles(*roles: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You do not have permission to perform this action")
        return user
    return dep


class PageParams:
    def __init__(self, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        self.page, self.page_size = page, page_size


def paginate(db: Session, stmt, p: PageParams):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.limit(p.page_size).offset((p.page - 1) * p.page_size)).all()
    return {"items": items, "total": total, "page": p.page, "page_size": p.page_size}
