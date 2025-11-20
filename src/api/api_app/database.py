"""Database connection and session management."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.

    Creates a new database session for each request and ensures it is
    properly closed afterward, even if an exception occurs.

    Yields:
        SQLAlchemy database session
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
