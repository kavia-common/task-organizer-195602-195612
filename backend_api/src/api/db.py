import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_ENGINE = None
_SessionLocal: Optional[sessionmaker] = None


# PUBLIC_INTERFACE
def get_engine():
    """Create (if needed) and return the global SQLAlchemy engine.

    Uses DATABASE_URL from environment. This must be configured via backend_api/.env.
    """
    global _ENGINE, _SessionLocal

    if _ENGINE is not None:
        return _ENGINE

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Please configure it in backend_api/.env "
            "(see backend_api/.env.example)."
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
    """FastAPI dependency that provides a SQLAlchemy Session and ensures cleanup."""
    if _SessionLocal is None:
        get_engine()

    db = _SessionLocal()  # type: ignore[misc]
    try:
        yield db
    finally:
        db.close()
