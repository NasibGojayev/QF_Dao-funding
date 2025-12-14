"""
SQLAlchemy ORM Models for DAO Database

Schema normalized to 4NF/5NF - no multivalued dependencies.
All tables have proper PKs, FKs, indexes, and constraints.
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Boolean, Numeric, Text, UniqueConstraint, Index,
    CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    Users table - stores wallet addresses and metadata.
    
    Normalization:
    - 1NF: All atomic values
    - 2NF: Single PK, no partial dependencies
    - 3NF: No transitive dependencies
    - 4NF: No multivalued dependencies
    - 5NF: Cannot decompose further
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet = Column(String(66), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    transactions = relationship("Transaction", back_populates="user")
    
    __table_args__ = (
        CheckConstraint("wallet ~ '^0x[a-fA-F0-9]{40}$'", name='valid_wallet_format'),
    )


class Project(Base):
    """
    Projects table - funding projects created by users.
    
    Normalization: 5NF - single owner, no arrays.
    """
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    transactions = relationship("Transaction", back_populates="project")
    milestones = relationship("Milestone", back_populates="project")
    project_tags = relationship("ProjectTag", back_populates="project")
    
    __table_args__ = (
        Index('ix_projects_owner_id', 'owner_id'),
        Index('ix_projects_created_at', 'created_at'),
    )


class Tag(Base):
    """
    Tags table - categorization labels.
    
    Normalization: 5NF - trivially (only 2 columns).
    """
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="tag")
    project_tags = relationship("ProjectTag", back_populates="tag")


class Transaction(Base):
    """
    Transactions table - blockchain transaction records.
    
    Normalization: 5NF
    - Each transaction has ONE user, ONE project, ONE tag
    - No multivalued dependencies
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), unique=True, nullable=False)
    block_number = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='SET NULL'), nullable=True)
    amount = Column(Numeric(36, 18), nullable=False)  # Support for wei precision
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    event_type = Column(String(50), nullable=True)  # TransactionCreated, MilestoneResolved, etc.
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    project = relationship("Project", back_populates="transactions")
    tag = relationship("Tag", back_populates="transactions")
    
    __table_args__ = (
        Index('ix_transactions_tx_hash', 'tx_hash'),
        Index('ix_transactions_user_id', 'user_id'),
        Index('ix_transactions_project_id', 'project_id'),
        Index('ix_transactions_tag_id', 'tag_id'),
        Index('ix_transactions_created_at', 'created_at'),
        Index('ix_transactions_block_number', 'block_number'),
        # Composite indexes for hot-path queries
        Index('ix_transactions_user_created', 'user_id', 'created_at'),
        Index('ix_transactions_project_created', 'project_id', 'created_at'),
        CheckConstraint("tx_hash ~ '^0x[a-fA-F0-9]{64}$'", name='valid_tx_hash_format'),
    )


class Milestone(Base):
    """
    Milestones table - project milestones for funding release.
    
    Normalization: 5NF - each milestone belongs to ONE project.
    """
    __tablename__ = 'milestones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Numeric(36, 18), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_tx_hash = Column(String(66), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
    
    __table_args__ = (
        Index('ix_milestones_project_id', 'project_id'),
        Index('ix_milestones_resolved', 'resolved'),
    )


class ProjectTag(Base):
    """
    ProjectTag junction table - many-to-many relationship.
    
    Normalization: 5NF
    - Eliminates multivalued dependency between projects and tags
    - Composite candidate key (project_id, tag_id)
    """
    __tablename__ = 'project_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="project_tags")
    tag = relationship("Tag", back_populates="project_tags")
    
    __table_args__ = (
        UniqueConstraint('project_id', 'tag_id', name='uq_project_tag'),
        Index('ix_project_tags_project_id', 'project_id'),
        Index('ix_project_tags_tag_id', 'tag_id'),
    )


class IndexerState(Base):
    """
    IndexerState table - tracks ETL/indexer progress.
    
    Used for batch backfill and resumption.
    """
    __tablename__ = 'indexer_state'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_address = Column(String(66), nullable=False)
    last_block_processed = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('contract_address', name='uq_indexer_contract'),
    )


class EventLog(Base):
    """
    EventLog table - raw event logs for auditing/SIEM.
    
    Stores raw event data before transformation.
    """
    __tablename__ = 'event_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), nullable=False)
    block_number = Column(Integer, nullable=False)
    log_index = Column(Integer, nullable=False)
    contract_address = Column(String(66), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_data = Column(Text, nullable=True)  # JSON string
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('tx_hash', 'log_index', name='uq_event_log'),
        Index('ix_event_logs_block_number', 'block_number'),
        Index('ix_event_logs_processed', 'processed'),
        Index('ix_event_logs_event_name', 'event_name'),
    )
