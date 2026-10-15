import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from ...database import engine
from ...services import ai_service

router = APIRouter(prefix="/health", tags=["health"])
log = logging.getLogger(__name__)


def db_status() -> dict:
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Connected"}
    except Exception as e:  # noqa: BLE001 - report, never leak connection strings
        log.warning("Database health check failed: %s", type(e).__name__)
        return {"status": "error", "message": "Cannot connect to the database. Check DATABASE_URL and that MySQL is running."}


@router.get("")
def health():
    """Application liveness only; independent of MySQL and Ollama."""
    return {"status": "ok"}


@router.get("/database")
def health_db(response: Response):
    r = db_status()
    if r["status"] != "ok":
        response.status_code = 503
    return r


@router.get("/ai")
def health_ai():
    """Always 200: AI being down is a degraded feature, not an application failure."""
    return ai_service.check_status()
