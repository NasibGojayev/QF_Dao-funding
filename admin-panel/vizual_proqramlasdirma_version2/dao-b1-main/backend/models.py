"""SQLAlchemy models aligned to a SDF1-like ERD for transactions, users, projects, tags.

Normalized to avoid multivalued dependencies. Primary keys and FKs included.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Numeric,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    wallet = Column(String(66), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=False, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship('User')


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    tx_hash = Column(String(66), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    amount = Column(Numeric(20, 8), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, default=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=True, index=True)

    user = relationship('User')
    project = relationship('Project')
    tag = relationship('Tag')


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class Milestone(Base):
    __tablename__ = 'milestones'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship('Project')


# Join table to allow many-to-many project <-> tag if needed without multivalued fields
class ProjectTag(Base):
    __tablename__ = 'project_tags'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('project_id', 'tag_id', name='_project_tag_uc'),)


# Hot-path indexes for dashboard queries
Index('ix_transactions_user_created', Transaction.user_id, Transaction.created_at)
Index('ix_transactions_project_created', Transaction.project_id, Transaction.created_at)
Index('ix_transactions_txhash', Transaction.tx_hash)
