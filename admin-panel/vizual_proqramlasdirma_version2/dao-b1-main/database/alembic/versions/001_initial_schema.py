"""001_initial_schema - Create all core tables

Revision ID: 001
Revises: None
Create Date: 2025-12-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # USERS TABLE
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet', sa.String(66), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('wallet'),
        sa.CheckConstraint("wallet ~ '^0x[a-fA-F0-9]{40}$'", name='valid_wallet_format')
    )
    op.create_index('ix_users_wallet', 'users', ['wallet'])

    # PROJECTS TABLE
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])

    # TAGS TABLE
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # TRANSACTIONS TABLE
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tx_hash', sa.String(66), nullable=False),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(36, 18), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('event_type', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='SET NULL'),
        sa.CheckConstraint("tx_hash ~ '^0x[a-fA-F0-9]{64}$'", name='valid_tx_hash_format')
    )

    # MILESTONES TABLE
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Numeric(36, 18), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_tx_hash', sa.String(66), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE')
    )
    op.create_index('ix_milestones_project_id', 'milestones', ['project_id'])

    # PROJECT_TAGS TABLE (Junction)
    op.create_table(
        'project_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'tag_id', name='uq_project_tag')
    )
    op.create_index('ix_project_tags_project_id', 'project_tags', ['project_id'])
    op.create_index('ix_project_tags_tag_id', 'project_tags', ['tag_id'])

    # INDEXER_STATE TABLE
    op.create_table(
        'indexer_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contract_address', sa.String(66), nullable=False),
        sa.Column('last_block_processed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_address', name='uq_indexer_contract')
    )

    # EVENT_LOGS TABLE
    op.create_table(
        'event_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tx_hash', sa.String(66), nullable=False),
        sa.Column('block_number', sa.Integer(), nullable=False),
        sa.Column('log_index', sa.Integer(), nullable=False),
        sa.Column('contract_address', sa.String(66), nullable=False),
        sa.Column('event_name', sa.String(100), nullable=False),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash', 'log_index', name='uq_event_log')
    )
    op.create_index('ix_event_logs_block_number', 'event_logs', ['block_number'])
    op.create_index('ix_event_logs_event_name', 'event_logs', ['event_name'])


def downgrade() -> None:
    op.drop_table('event_logs')
    op.drop_table('indexer_state')
    op.drop_table('project_tags')
    op.drop_table('milestones')
    op.drop_table('transactions')
    op.drop_table('tags')
    op.drop_table('projects')
    op.drop_table('users')
