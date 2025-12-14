"""003_materialized_views - Create materialized views for analytics

Revision ID: 003
Revises: 002
Create Date: 2025-12-09
"""
from typing import Sequence, Union
from alembic import op

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Transaction Summary by Tag and Day
    op.execute("""
        CREATE MATERIALIZED VIEW mv_tx_summary_by_tag AS
        SELECT
            DATE(t.created_at) AS day,
            COALESCE(tg.name, 'untagged') AS tag_name,
            COUNT(*) AS tx_count,
            SUM(t.amount) AS total_amount,
            COUNT(DISTINCT t.user_id) AS unique_users,
            AVG(t.amount) AS avg_amount
        FROM transactions t
        LEFT JOIN tags tg ON tg.id = t.tag_id
        WHERE t.success = TRUE
        GROUP BY DATE(t.created_at), tg.name
        ORDER BY day DESC, tag_name
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_tx_summary_day_tag 
        ON mv_tx_summary_by_tag(day, tag_name)
    """)
    op.execute("""
        CREATE INDEX ix_mv_tx_summary_day 
        ON mv_tx_summary_by_tag(day DESC)
    """)

    # Project Funding Summary
    op.execute("""
        CREATE MATERIALIZED VIEW mv_project_funding AS
        SELECT
            p.id AS project_id,
            p.title AS project_title,
            p.owner_id,
            u.wallet AS owner_wallet,
            COUNT(t.id) AS donation_count,
            COALESCE(SUM(t.amount), 0) AS total_raised,
            COUNT(DISTINCT t.user_id) AS unique_donors,
            MIN(t.created_at) AS first_donation,
            MAX(t.created_at) AS last_donation,
            p.created_at AS project_created,
            p.is_active
        FROM projects p
        LEFT JOIN transactions t ON t.project_id = p.id AND t.success = TRUE
        LEFT JOIN users u ON u.id = p.owner_id
        GROUP BY p.id, p.title, p.owner_id, u.wallet, p.created_at, p.is_active
        ORDER BY total_raised DESC
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_project_funding_id 
        ON mv_project_funding(project_id)
    """)
    op.execute("""
        CREATE INDEX ix_mv_project_funding_raised 
        ON mv_project_funding(total_raised DESC)
    """)

    # User Activity Summary
    op.execute("""
        CREATE MATERIALIZED VIEW mv_user_activity AS
        SELECT
            u.id AS user_id,
            u.wallet,
            COUNT(DISTINCT t.id) AS tx_count,
            COUNT(DISTINCT t.project_id) AS projects_funded,
            COALESCE(SUM(t.amount), 0) AS total_donated,
            COUNT(DISTINCT p.id) AS projects_created,
            MIN(t.created_at) AS first_activity,
            MAX(t.created_at) AS last_activity
        FROM users u
        LEFT JOIN transactions t ON t.user_id = u.id AND t.success = TRUE
        LEFT JOIN projects p ON p.owner_id = u.id
        GROUP BY u.id, u.wallet
        ORDER BY total_donated DESC
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_user_activity_id 
        ON mv_user_activity(user_id)
    """)
    op.execute("""
        CREATE INDEX ix_mv_user_activity_wallet 
        ON mv_user_activity(wallet)
    """)

    # Create refresh function
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary_by_tag;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_funding;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_activity;
        END;
        $$ LANGUAGE plpgsql
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS refresh_all_materialized_views()")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_user_activity")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_project_funding")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_tx_summary_by_tag")
