"""Database engine, session factory and connectivity check."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session():
    """FastAPI dependency that yields a database session and always closes it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_database() -> bool:
    """Return True if a trivial query succeeds against PostgreSQL."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - health check must never raise
        logger.warning("Database connectivity check failed: %s", exc)
        return False
