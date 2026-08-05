"""SENTINEL AI - database session & bootstrap.

SQLite by default (zero-config on any laptop), PostgreSQL supported by
swapping DATABASE_URL in .env.
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.models.entities import Base


@lru_cache
def _make_engine():
    url = settings.database_url
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def get_db_engine():
    return _make_engine()


def create_tables() -> None:
    engine = get_db_engine()
    Base.metadata.create_all(engine)


def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_db_engine(), expire_on_commit=False)


def get_db():
    """FastAPI dependency that yields a session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
