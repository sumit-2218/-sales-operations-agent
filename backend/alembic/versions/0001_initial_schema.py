"""Initial schema: users, leads, ICP profiles, analyses, outreach, follow-ups, activity logs.

NOTE: this baseline revision creates the tables from the model metadata as it exists at
this release. All FUTURE schema changes must be written as explicit op.* operations
(or generated with `alembic revision --autogenerate`) so history stays reproducible.

Revision ID: 0001
Revises:
"""
from alembic import op

from app import models  # noqa: F401
from app.database import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
