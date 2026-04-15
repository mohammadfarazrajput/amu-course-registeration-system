"""
Database Configuration and Session Management
SQLAlchemy setup for SQLite database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os
from pathlib import Path

try:
    from models import Base
except ImportError:
    from backend.models import Base

# Database configuration
# Primary location: backend/database.db (ships with the repo)
# Falls back to ../data/database.db if the backend-local file doesn't exist
_LOCAL_DB = Path(__file__).parent / "database.db"
_DATA_DB  = Path(__file__).parent.parent / "data" / "database.db"

if _LOCAL_DB.exists():
    DATABASE_PATH = _LOCAL_DB
else:
    _DATA_DB.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH = _DATA_DB
# Ensure path string is compatible with SQLAlchemy on Windows
if os.name == 'nt':
    path_str = str(DATABASE_PATH).replace('\\', '/')
    DATABASE_URL = f"sqlite:///{path_str}"
else:
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=StaticPool,  # Better for SQLite
    echo=False  # Set True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DATABASE_PATH}")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions
    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db():
    """Drop all tables and recreate (DANGEROUS - use only in development)"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print(f"⚠️  Database reset at: {DATABASE_PATH}")


# Initialize database on import (optional - can be called explicitly)
if not DATABASE_PATH.exists():
    init_db()


if __name__ == "__main__":
    # Test database connection
    init_db()
    print(f"Database URL: {DATABASE_URL}")
    print(f"Database Path: {DATABASE_PATH}")
    print(f"Tables created: {Base.metadata.tables.keys()}")