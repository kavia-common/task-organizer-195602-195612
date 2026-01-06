import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE = None
_SessionLocal: Optional[sessionmaker] = None


def _get_database_url_from_env() -> Optional[str]:
    """Resolve the DB connection URL from environment variables.

    The platform environment commonly provides POSTGRES_URL, while some setups use DATABASE_URL.
    We support both for compatibility.
    """
    return (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip() or None


# PUBLIC_INTERFACE
def get_engine():
    """Create (if needed) and return the global SQLAlchemy engine.

    Environment variables:
      - DATABASE_URL (preferred, standard)
      - POSTGRES_URL (fallback used by this deployment platform)

    This function is intentionally *lazy* and should not be called during app import.
    """
    global _ENGINE, _SessionLocal

    if _ENGINE is not None:
        return _ENGINE

    database_url = _get_database_url_from_env()
    if not database_url:
        # Do not crash the app at import-time/startup. Raise only when DB is actually accessed.
        raise RuntimeError(
            "Database URL is not configured. Set DATABASE_URL (preferred) or POSTGRES_URL "
            "in backend_api/.env (see backend_api/.env.example)."
        )

    # For a basic CRUD API, a sync engine is sufficient and keeps dependencies minimal.
    _ENGINE = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)
    return _ENGINE


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLAlchemy Session and ensures cleanup.

    If the DB is not configured, this dependency raises a RuntimeError with an actionable message.
    """
    if _SessionLocal is None:
        get_engine()

    db = _SessionLocal()  # type: ignore[misc]
    try:
        yield db
    finally:
        db.close()
