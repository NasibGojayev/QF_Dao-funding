# Generated migration for materialized views
from django.db import migrations


class Migration(migrations.Migration):
    """
    Creates a materialized view for dashboard summaries.
    This view aggregates donation volume by proposal, round, and time period.
    """

    dependencies = [
        ('base', '0002_proposal_on_chain_id'),
    ]

    operations = [
        # Create materialized view for transaction volume summary
        migrations.RunSQL(
            sql="""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_donation_summary AS
                SELECT 
                    p.proposal_id,
                    p.title AS proposal_title,
                    p.status AS proposal_status,
                    r.round_id,
                    r.status AS round_status,
                    COUNT(d.donation_id) AS donation_count,
                    COALESCE(SUM(d.amount), 0) AS total_amount,
                    MIN(d.created_at) AS first_donation,
                    MAX(d.created_at) AS last_donation,
                    DATE_TRUNC('day', d.created_at) AS donation_date
                FROM base_proposal p
                LEFT JOIN base_donation d ON d.proposal_id = p.proposal_id
                LEFT JOIN base_round r ON r.round_id = p.round_id
                GROUP BY 
                    p.proposal_id, 
                    p.title, 
                    p.status,
                    r.round_id, 
                    r.status,
                    DATE_TRUNC('day', d.created_at)
                ORDER BY total_amount DESC;
                
                -- Create index for fast lookups
                CREATE UNIQUE INDEX IF NOT EXISTS mv_donation_summary_idx 
                ON mv_donation_summary (proposal_id, round_id, donation_date);
            """,
            reverse_sql="""
                DROP MATERIALIZED VIEW IF EXISTS mv_donation_summary;
            """,
        ),
        
        # Create materialized view for round performance summary
        migrations.RunSQL(
            sql="""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_round_performance AS
                SELECT 
                    r.round_id,
                    r.status AS round_status,
                    r.start_date,
                    r.end_date,
                    mp.pool_id,
                    mp.total_funds AS pool_total,
                    COUNT(DISTINCT p.proposal_id) AS proposal_count,
                    COUNT(DISTINCT d.donation_id) AS total_donations,
                    COALESCE(SUM(d.amount), 0) AS total_donation_amount,
                    COALESCE(SUM(m.matched_amount), 0) AS total_matched_amount
                FROM base_round r
                LEFT JOIN base_matchingpool mp ON mp.pool_id = r.matching_pool_id
                LEFT JOIN base_proposal p ON p.round_id = r.round_id
                LEFT JOIN base_donation d ON d.proposal_id = p.proposal_id
                LEFT JOIN base_match m ON m.round_id = r.round_id AND m.proposal_id = p.proposal_id
                GROUP BY 
                    r.round_id, 
                    r.status, 
                    r.start_date, 
                    r.end_date, 
                    mp.pool_id, 
                    mp.total_funds
                ORDER BY r.start_date DESC;
                
                CREATE UNIQUE INDEX IF NOT EXISTS mv_round_performance_idx 
                ON mv_round_performance (round_id);
            """,
            reverse_sql="""
                DROP MATERIALIZED VIEW IF EXISTS mv_round_performance;
            """,
        ),
    ]
