import csv
import io
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...database import get_db
from ...models.models import User
from ...services import csv_parser as cp
from ...services.activity_service import log_activity
from ...services.import_service import existing_keys, insert_leads
from ..deps import get_current_user

router = APIRouter(prefix="/imports", tags=["imports"])


async def _read(file: UploadFile) -> bytes:
    limit = get_settings().max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"File is too large. The limit is {get_settings().max_upload_mb} MB.")
    return data


def _json(value: str | None, what: str):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(422, f"{what} must be valid JSON")


def _prepare(db: Session, content: bytes, mapping, corrections):
    try:
        parsed = cp.parse_csv(content, mapping, get_settings().max_import_rows)
    except cp.CsvFileError as e:
        raise HTTPException(422, str(e))
    cp.apply_corrections(parsed["rows"], corrections)
    classified = cp.classify(parsed["rows"], existing_keys(db, parsed["rows"]))
    return parsed, classified


@router.get("/template")
def template():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cp.FIELDS)
    w.writerow(["Example Co (fictional)", "Alex Example", "alex@example.com", "Head of Operations", "Software",
                "120", "Berlin, Germany", "20000000", "B2B SaaS automation platform", ""])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="lead_import_template.csv"'})


@router.post("/preview")
async def preview(file: UploadFile = File(...), mapping: str | None = Form(None), corrections: str | None = Form(None),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = await _read(file)
    parsed, rows = _prepare(db, content, _json(mapping, "mapping"), _json(corrections, "corrections"))
    count = lambda s: sum(1 for r in rows if r["status"] == s)
    return {"headers": parsed["headers"], "mapping": parsed["mapping"], "fields": cp.FIELDS,
            "total_rows": len(rows), "valid_count": count("valid"), "invalid_count": count("invalid"),
            "duplicate_count": count("duplicate"), "rows": rows}


@router.post("/confirm")
async def confirm(file: UploadFile = File(...), mapping: str | None = Form(None), corrections: str | None = Form(None),
                  exclude_rows: str | None = Form(None), skip_duplicates: bool = Form(True),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = await _read(file)
    _, rows = _prepare(db, content, _json(mapping, "mapping"), _json(corrections, "corrections"))
    excluded = set(_json(exclude_rows, "exclude_rows") or [])
    to_import, invalid, dups, skipped = [], 0, 0, 0
    for r in rows:
        if r["row_number"] in excluded:
            skipped += 1
        elif r["status"] == "invalid":
            invalid += 1
        elif r["status"] == "duplicate" and skip_duplicates:
            dups += 1
        else:
            to_import.append(r)
    try:
        leads = insert_leads(db, user, to_import)
        db.flush()
        log_activity(db, user, "import.completed", "import", None, None,
                     {"filename": file.filename, "imported": len(leads), "invalid": invalid, "duplicates": dups})
        db.commit()  # single transaction: all-or-nothing
    except Exception:
        db.rollback()
        raise
    return {"imported": len(leads), "skipped_invalid": invalid, "skipped_duplicates": dups, "excluded_by_user": skipped}
