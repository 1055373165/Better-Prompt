"""Database connection, initialization, and WAL configuration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

_engine = None
_SessionFactory = None


def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode and busy timeout for every connection."""
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine(db_path: Path):
    """Get or create the SQLAlchemy engine for the given DB path."""
    global _engine
    if _engine is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path}"
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
        event.listen(_engine, "connect", _set_sqlite_pragma)
    return _engine


def get_session_factory(db_path: Path) -> sessionmaker[Session]:
    """Get or create a session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine(db_path)
        _SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    return _SessionFactory


def get_session(db_path: Path) -> Session:
    """Create a new session."""
    factory = get_session_factory(db_path)
    return factory()


def init_db(db_path: Path) -> None:
    """Create all tables if they don't exist."""
    from src.state.models import Base

    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def reset_connection() -> None:
    """Reset the global engine and session factory (for testing)."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
