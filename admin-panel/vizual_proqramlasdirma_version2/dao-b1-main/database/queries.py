"""
Common Query Functions for DAO Database

Pre-built queries for common data access patterns.
"""
from sqlalchemy import select, func, desc, and_, text
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from models import User, Project, Transaction, Tag, Milestone, ProjectTag


# ============================================================
# USER QUERIES
# ============================================================

def get_user_by_wallet(session: Session, wallet: str) -> Optional[User]:
    """Find user by wallet address. Uses ix_users_wallet index."""
    return session.query(User).filter(User.wallet == wallet).first()


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Find user by ID."""
    return session.get(User, user_id)


# ============================================================
# TRANSACTION QUERIES (Hot Path)
# ============================================================

def get_user_transactions(
    session: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    success_only: bool = True
) -> List[Transaction]:
    """
    Get user's recent transactions.
    Uses: ix_transactions_user_created composite index
    """
    query = session.query(Transaction).filter(Transaction.user_id == user_id)
    if success_only:
        query = query.filter(Transaction.success == True)
    return query.order_by(desc(Transaction.created_at)).limit(limit).offset(offset).all()


def get_project_transactions(
    session: Session,
    project_id: int,
    limit: int = 50
) -> List[Transaction]:
    """
    Get project's recent donations.
    Uses: ix_transactions_project_created composite index
    """
    return (
        session.query(Transaction)
        .filter(Transaction.project_id == project_id)
        .filter(Transaction.success == True)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
        .all()
    )


def get_transaction_by_hash(session: Session, tx_hash: str) -> Optional[Transaction]:
    """
    Find transaction by hash (idempotent check).
    Uses: ix_transactions_tx_hash unique index
    """
    return session.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()


def transaction_exists(session: Session, tx_hash: str) -> bool:
    """Check if transaction already exists (for idempotent inserts)."""
    return session.query(
        session.query(Transaction).filter(Transaction.tx_hash == tx_hash).exists()
    ).scalar()


# ============================================================
# PROJECT QUERIES
# ============================================================

def get_user_projects(session: Session, user_id: int) -> List[Project]:
    """Get all projects owned by user. Uses: ix_projects_owner_id"""
    return (
        session.query(Project)
        .filter(Project.owner_id == user_id)
        .order_by(desc(Project.created_at))
        .all()
    )


def get_active_projects(session: Session, limit: int = 20) -> List[Project]:
    """Get active projects. Uses: ix_projects_active partial index"""
    return (
        session.query(Project)
        .filter(Project.is_active == True)
        .order_by(desc(Project.created_at))
        .limit(limit)
        .all()
    )


def get_project_with_funding(session: Session, project_id: int) -> Dict[str, Any]:
    """Get project with aggregated funding stats."""
    project = session.get(Project, project_id)
    if not project:
        return None
    
    stats = (
        session.query(
            func.count(Transaction.id).label('donation_count'),
            func.sum(Transaction.amount).label('total_raised'),
            func.count(func.distinct(Transaction.user_id)).label('unique_donors')
        )
        .filter(Transaction.project_id == project_id)
        .filter(Transaction.success == True)
        .first()
    )
    
    return {
        'project': project,
        'donation_count': stats.donation_count or 0,
        'total_raised': stats.total_raised or Decimal('0'),
        'unique_donors': stats.unique_donors or 0
    }


# ============================================================
# ANALYTICS QUERIES (Use Materialized Views)
# ============================================================

def get_daily_summary(session: Session, days: int = 30) -> List[Dict]:
    """
    Get daily transaction summary.
    Uses: mv_tx_summary_by_tag materialized view
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    result = session.execute(text("""
        SELECT day, tag_name, tx_count, total_amount, unique_users
        FROM mv_tx_summary_by_tag
        WHERE day >= :start_date
        ORDER BY day DESC, tag_name
    """), {"start_date": start_date})
    
    return [dict(row._mapping) for row in result]


def get_project_leaderboard(session: Session, limit: int = 10) -> List[Dict]:
    """
    Get top funded projects.
    Uses: mv_project_funding materialized view
    """
    result = session.execute(text("""
        SELECT project_id, project_title, total_raised, donation_count, unique_donors
        FROM mv_project_funding
        WHERE is_active = true
        ORDER BY total_raised DESC
        LIMIT :limit
    """), {"limit": limit})
    
    return [dict(row._mapping) for row in result]


def get_user_stats(session: Session, user_id: int) -> Optional[Dict]:
    """
    Get user activity stats.
    Uses: mv_user_activity materialized view
    """
    result = session.execute(text("""
        SELECT user_id, wallet, tx_count, projects_funded, total_donated, projects_created
        FROM mv_user_activity
        WHERE user_id = :user_id
    """), {"user_id": user_id}).first()
    
    return dict(result._mapping) if result else None


# ============================================================
# INDEXER / ETL QUERIES
# ============================================================

def get_indexer_state(session: Session, contract_address: str) -> Optional[int]:
    """Get last processed block for contract."""
    from models import IndexerState
    state = session.query(IndexerState).filter(
        IndexerState.contract_address == contract_address
    ).first()
    return state.last_block_processed if state else None


def update_indexer_state(session: Session, contract_address: str, block_number: int):
    """Update last processed block."""
    from models import IndexerState
    state = session.query(IndexerState).filter(
        IndexerState.contract_address == contract_address
    ).first()
    
    if state:
        state.last_block_processed = block_number
    else:
        state = IndexerState(
            contract_address=contract_address,
            last_block_processed=block_number
        )
        session.add(state)


def get_unprocessed_events(session: Session, limit: int = 100) -> List:
    """Get unprocessed event logs for ETL."""
    from models import EventLog
    return (
        session.query(EventLog)
        .filter(EventLog.processed == False)
        .order_by(EventLog.block_number, EventLog.log_index)
        .limit(limit)
        .all()
    )
