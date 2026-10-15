"""Safe, repeatable seeding.  Run from the backend/ directory:

    python -m app.seed --admin            # create the first administrator (prompts for password)
    python -m app.seed --demo             # default ICP + fictional sample leads for the admin
    python -m app.seed --admin --demo

Admin credentials come from ADMIN_EMAIL / ADMIN_PASSWORD env vars or an interactive prompt;
nothing is hardcoded. Re-running never creates duplicates.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

from sqlalchemy import func, select

from .core.security import hash_password
from .database import SessionLocal
from .models.models import IcpProfile, Role, User
from .schemas.schemas import RegisterIn
from .services import csv_parser as cp
from .services.icp_service import DEFAULT_ICP_CONFIG
from .services.import_service import existing_keys, insert_leads

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "sample_leads.csv"


def create_admin(db) -> User:
    email = (os.environ.get("ADMIN_EMAIL") or input("Admin email: ")).strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == email))
    if existing:
        print(f"Admin/user {email} already exists; nothing changed.")
        return existing
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Admin password (min 8 chars): ")
    name = os.environ.get("ADMIN_NAME", "Administrator")
    RegisterIn(name=name, email=email, password=password)  # reuse validation
    user = User(name=name, email=email, password_hash=hash_password(password), role=Role.ADMIN)
    db.add(user)
    db.commit()
    print(f"Created administrator {email}")
    return user


def load_demo(db) -> None:
    admin = db.scalar(select(User).where(User.role == Role.ADMIN).order_by(User.id))
    if not admin:
        sys.exit("Create an administrator first: python -m app.seed --admin")
    if not db.scalar(select(IcpProfile.id).where(IcpProfile.owner_id == admin.id)):
        db.add(IcpProfile(name="Demo ICP (DACH software & logistics)", owner_id=admin.id,
                          config=DEFAULT_ICP_CONFIG, is_active=True))
        db.commit()
        print("Created default demo ICP")
    parsed = cp.parse_csv(SAMPLE.read_bytes())
    rows = cp.classify(parsed["rows"], existing_keys(db, parsed["rows"]))
    valid = [r for r in rows if r["status"] == "valid"]
    insert_leads(db, admin, valid, source="sample_data")
    db.commit()
    print(f"Imported {len(valid)} fictional sample leads ({len(rows) - len(valid)} skipped as duplicates/invalid)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if not (a.admin or a.demo):
        ap.print_help()
    with SessionLocal() as session:
        if a.admin:
            create_admin(session)
        if a.demo:
            load_demo(session)
