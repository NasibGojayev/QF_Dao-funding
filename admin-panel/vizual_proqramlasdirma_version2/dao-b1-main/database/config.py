"""
Database Configuration for PostgreSQL

Provides SQLAlchemy engine and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/dao_db"
)

# SQLAlchemy engine with PostgreSQL-specific settings
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    echo=False,  # Set True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


@contextmanager
def get_session():
    """Context manager for database sessions with auto-commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables():
    """Create all tables from ORM models."""
    from models import Base
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables (use with caution!)."""
    from models import Base
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    # Test connection
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        print(f"Connected to: {result.fetchone()[0]}")
