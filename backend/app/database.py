import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    """
    Create a SQLAlchemy engine.

    SQLite is supported for automated tests.
    MySQL connections use the CA certificate for secure TLS.
    """
    if url.startswith("sqlite"):
        kw = {"connect_args": {"check_same_thread": False}}

        if ":memory:" in url or url.rstrip("/") in ("sqlite:", "sqlite://"):
            kw["poolclass"] = StaticPool

        return create_engine(url, **kw)

    connect_args = {}

    if url.startswith("mysql"):
        ca_path = os.getenv("MYSQL_SSL_CA")

        # Default CA certificate path for Aiven on Render.
        if not ca_path and "aivencloud.com" in url:
            ca_path = "/etc/secrets/ca.pem"

        if ca_path:
            if not os.path.isfile(ca_path):
                raise RuntimeError(
                    f"MySQL CA certificate not found at: {ca_path}"
                )

            connect_args["ssl"] = {"ca": ca_path}

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
    )


engine = _make_engine(get_settings().database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()