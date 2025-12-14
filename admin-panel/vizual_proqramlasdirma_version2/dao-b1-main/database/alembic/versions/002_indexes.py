"""002_indexes - Create all hot-path indexes

Revision ID: 002
Revises: 001
Create Date: 2025-12-09
"""
from typing import Sequence, Union
from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TRANSACTIONS INDEXES
    op.create_index('ix_transactions_tx_hash', 'transactions', ['tx_hash'], unique=True)
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_project_id', 'transactions', ['project_id'])
    op.create_index('ix_transactions_tag_id', 'transactions', ['tag_id'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('ix_transactions_block_number', 'transactions', ['block_number'])
    op.create_index('ix_transactions_event_type', 'transactions', ['event_type'])
    
    # COMPOSITE INDEXES (Hot Path)
    op.create_index(
        'ix_transactions_user_created', 
        'transactions', 
        ['user_id', 'created_at']
    )
    op.create_index(
        'ix_transactions_project_created', 
        'transactions', 
        ['project_id', 'created_at']
    )
    
    # PARTIAL INDEXES
    op.execute("""
        CREATE INDEX ix_transactions_success 
        ON transactions(user_id, created_at DESC) 
        WHERE success = TRUE
    """)
    
    op.execute("""
        CREATE INDEX ix_projects_active 
        ON projects(created_at DESC) 
        WHERE is_active = TRUE
    """)
    
    op.execute("""
        CREATE INDEX ix_milestones_unresolved 
        ON milestones(project_id) 
        WHERE resolved = FALSE
    """)
    
    op.execute("""
        CREATE INDEX ix_event_logs_unprocessed 
        ON event_logs(created_at) 
        WHERE processed = FALSE
    """)


def downgrade() -> None:
    op.drop_index('ix_event_logs_unprocessed', 'event_logs')
    op.drop_index('ix_milestones_unresolved', 'milestones')
    op.drop_index('ix_projects_active', 'projects')
    op.drop_index('ix_transactions_success', 'transactions')
    op.drop_index('ix_transactions_project_created', 'transactions')
    op.drop_index('ix_transactions_user_created', 'transactions')
    op.drop_index('ix_transactions_event_type', 'transactions')
    op.drop_index('ix_transactions_block_number', 'transactions')
    op.drop_index('ix_transactions_created_at', 'transactions')
    op.drop_index('ix_transactions_tag_id', 'transactions')
    op.drop_index('ix_transactions_project_id', 'transactions')
    op.drop_index('ix_transactions_user_id', 'transactions')
    op.drop_index('ix_transactions_tx_hash', 'transactions')
