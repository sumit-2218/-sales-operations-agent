from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from ...core.config import get_settings
from ...core.security import create_access_token, hash_password, verify_password
from ...database import get_db
from ...models.models import Role, User
from ...schemas.schemas import LoginIn, ProfilePatch, RegisterIn, TokenOut, UserOut
from ...services.activity_service import log_activity
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not get_settings().allow_registration:
        raise HTTPException(403, "Self-registration is disabled. Ask an administrator to create your account.")
    if db.scalar(select(User.id).where(func.lower(User.email) == body.email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=body.name, email=body.email, password_hash=hash_password(body.password), role=Role.SALES_REP)
    db.add(user)
    db.flush()
    log_activity(db, user, "user.registered", "user", user.id)
    db.commit()
    return user


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled")
    log_activity(db, user, "user.login", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.post("/logout", status_code=204)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tokens are stateless; the client discards its token. This endpoint records the event."""
    log_activity(db, user, "user.logout", "user", user.id)
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: ProfilePatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.name:
        user.name = body.name.strip()
    if body.new_password:
        if not body.current_password or not verify_password(body.current_password, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        user.password_hash = hash_password(body.new_password)
    log_activity(db, user, "user.profile_updated", "user", user.id, meta={"password_changed": bool(body.new_password)})
    db.commit()
    return user


class GoogleCredentialIn(BaseModel):
    credential: str = Field(min_length=20, max_length=10000)


@router.post("/google", response_model=TokenOut)
def google_login(body: GoogleCredentialIn, db: Session = Depends(get_db)):
    """Verify a Google Identity Services ID token server-side before creating a session."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in is not configured. Set GOOGLE_CLIENT_ID first.")
    try:
        claims = google_id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), settings.google_client_id
        )
    except Exception:
        raise HTTPException(401, "Google credential is invalid or expired")
    email = str(claims.get("email", "")).strip().lower()
    if not email or claims.get("email_verified") is not True:
        raise HTTPException(403, "Use a Google account with a verified email address")
    name = str(claims.get("name") or email.split("@")[0])[:120]
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        if not settings.allow_registration:
            raise HTTPException(403, "Self-registration is disabled. Ask an administrator to create your account.")
        user = User(name=name, email=email, password_hash=hash_password(__import__("secrets").token_urlsafe(32)), role=Role.SALES_REP)
        db.add(user)
        db.flush()
        log_activity(db, user, "user.google_registered", "user", user.id)
    elif not user.is_active:
        raise HTTPException(403, "This account has been disabled")
    else:
        log_activity(db, user, "user.google_login", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_access_token(user.id), user=user)
