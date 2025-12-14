-- ============================================================
-- DAO Database Materialized Views - PostgreSQL
-- ============================================================
-- Pre-computed views for dashboard and analytics queries
-- ============================================================

-- ============================================================
-- 1. TRANSACTION SUMMARY BY TAG AND DAY
-- ============================================================
-- Purpose: Dashboard chart showing transaction volume over time by category

DROP MATERIALIZED VIEW IF EXISTS mv_tx_summary_by_tag;

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
ORDER BY day DESC, tag_name;

-- Index for fast date range queries
CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_tx_summary_day_tag 
    ON mv_tx_summary_by_tag(day, tag_name);

CREATE INDEX IF NOT EXISTS ix_mv_tx_summary_day 
    ON mv_tx_summary_by_tag(day DESC);

COMMENT ON MATERIALIZED VIEW mv_tx_summary_by_tag IS 
    'Daily transaction summary grouped by tag for dashboard analytics';

-- ============================================================
-- 2. PROJECT FUNDING SUMMARY
-- ============================================================
-- Purpose: Project leaderboard and funding status

DROP MATERIALIZED VIEW IF EXISTS mv_project_funding;

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
ORDER BY total_raised DESC;

-- Index for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_project_funding_id 
    ON mv_project_funding(project_id);

CREATE INDEX IF NOT EXISTS ix_mv_project_funding_raised 
    ON mv_project_funding(total_raised DESC);

COMMENT ON MATERIALIZED VIEW mv_project_funding IS 
    'Project funding summary for leaderboards and project pages';

-- ============================================================
-- 3. USER ACTIVITY SUMMARY
-- ============================================================
-- Purpose: User profile stats and activity tracking

DROP MATERIALIZED VIEW IF EXISTS mv_user_activity;

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
ORDER BY total_donated DESC;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_user_activity_id 
    ON mv_user_activity(user_id);

CREATE INDEX IF NOT EXISTS ix_mv_user_activity_wallet 
    ON mv_user_activity(wallet);

COMMENT ON MATERIALIZED VIEW mv_user_activity IS 
    'User activity summary for profiles and leaderboards';

-- ============================================================
-- REFRESH FUNCTIONS
-- ============================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary_by_tag;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_funding;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_activity;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh with timing
CREATE OR REPLACE FUNCTION refresh_materialized_views_with_log()
RETURNS TABLE(view_name TEXT, duration_ms NUMERIC) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- mv_tx_summary_by_tag
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary_by_tag;
    end_time := clock_timestamp();
    view_name := 'mv_tx_summary_by_tag';
    duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
    -- mv_project_funding
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_funding;
    end_time := clock_timestamp();
    view_name := 'mv_project_funding';
    duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
    -- mv_user_activity
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_activity;
    end_time := clock_timestamp();
    view_name := 'mv_user_activity';
    duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views IS 
    'Refresh all materialized views concurrently';
COMMENT ON FUNCTION refresh_materialized_views_with_log IS 
    'Refresh all materialized views and return timing for each';

-- ============================================================
-- REFRESH STRATEGY
-- ============================================================
-- 
-- Option 1: Scheduled refresh via pg_cron (recommended for production)
--   SELECT cron.schedule('refresh-mv', '*/15 * * * *', 'SELECT refresh_all_materialized_views()');
--
-- Option 2: Manual refresh
--   SELECT refresh_all_materialized_views();
--
-- Option 3: Refresh with logging
--   SELECT * FROM refresh_materialized_views_with_log();
--
-- Option 4: Refresh specific view
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary_by_tag;
--
-- Note: CONCURRENTLY requires a unique index on the materialized view
-- ============================================================
