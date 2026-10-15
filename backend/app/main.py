import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from .api.routes import (admin, auth, dashboard, follow_ups, health, icp, imports, leads, outreach,
                         qualification)
from .core.config import get_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = FastAPI(title="Sales Operations Agent API", version="1.0.0",
              description="Standalone sales CRM with deterministic lead scoring and local-AI assistance.")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origin_list, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

PREFIX = "/api/v1"
for r in (health.router, auth.router, dashboard.router, leads.router, qualification.router, imports.router,
          icp.router, outreach.router, follow_ups.router, admin.router):
    app.include_router(r, prefix=PREFIX)


@app.exception_handler(OperationalError)
async def db_unavailable(request: Request, exc: OperationalError):
    log.error("Database error: %s", type(exc.orig).__name__ if exc.orig else "unknown")
    return JSONResponse(status_code=503, content={"detail": "The database is unavailable. Please try again shortly."})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})
