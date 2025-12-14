"""Initial migration - create core tables

Revision ID: 0001
Revises: 
Create Date: 2025-12-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('wallet', sa.String(length=66), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
    )
    op.create_index(op.f('ix_users_wallet'), 'users', ['wallet'], unique=False)

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tx_hash', sa.String(length=66), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
    )
    op.create_index(op.f('ix_transactions_txhash'), 'transactions', ['tx_hash'], unique=False)

    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'project_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
    )

def downgrade():
    op.drop_table('project_tags')
    op.drop_table('milestones')
    op.drop_table('transactions')
    op.drop_table('tags')
    op.drop_table('projects')
    op.drop_table('users')
