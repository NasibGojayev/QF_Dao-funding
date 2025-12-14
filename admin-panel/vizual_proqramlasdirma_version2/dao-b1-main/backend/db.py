"""Database engine and session helper for Sprint 2.

Uses SQLAlchemy for ORM and provides a simple create_all convenience
for local development. Production should use Alembic migrations.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use environment variable or fallback to sqlite for local dev
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./db.sqlite3')

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_session():
    return SessionLocal()

def create_tables(Base):
    Base.metadata.create_all(bind=engine)
