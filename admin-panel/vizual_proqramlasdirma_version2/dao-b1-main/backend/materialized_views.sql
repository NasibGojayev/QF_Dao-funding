-- ============================================================
-- Materialized View: Transaction Summary by Tag per Day
-- ============================================================
-- Purpose: Pre-compute dashboard summary to avoid expensive
-- GROUP BY operations at query time.
--
-- Used by: Dashboard analytics, transaction volume charts
-- ============================================================

-- ============================================================
-- SQLite Version (using regular table as pseudo-materialized view)
-- ============================================================

DROP TABLE IF EXISTS mv_tx_summary;

CREATE TABLE mv_tx_summary AS
SELECT
    DATE(t.created_at) AS day,
    COALESCE(tags.name, 'untagged') AS tag,
    COUNT(*) AS tx_count,
    SUM(t.amount) AS total_amount,
    COUNT(DISTINCT t.user_id) AS unique_users
FROM transactions t
LEFT JOIN tags ON tags.id = t.tag_id
GROUP BY DATE(t.created_at), tags.name;

-- Index for time-range queries on the summary
CREATE INDEX IF NOT EXISTS ix_mv_tx_summary_day ON mv_tx_summary(day);

-- ============================================================
-- PostgreSQL Version (true materialized view)
-- ============================================================

/*
-- Drop if exists
DROP MATERIALIZED VIEW IF EXISTS mv_tx_summary;

-- Create materialized view
CREATE MATERIALIZED VIEW mv_tx_summary AS
SELECT
    DATE(t.created_at) AS day,
    COALESCE(tags.name, 'untagged') AS tag,
    COUNT(*) AS tx_count,
    SUM(t.amount) AS total_amount,
    COUNT(DISTINCT t.user_id) AS unique_users
FROM transactions t
LEFT JOIN tags ON tags.id = t.tag_id
GROUP BY DATE(t.created_at), tags.name
WITH NO DATA;  -- Don't populate immediately

-- Create index on materialized view
CREATE INDEX ix_mv_tx_summary_day ON mv_tx_summary(day);

-- Initial population
REFRESH MATERIALIZED VIEW mv_tx_summary;
*/

-- ============================================================
-- REFRESH STRATEGY
-- ============================================================
--
-- Option 1: Full Refresh (Simple, recommended for small datasets)
-- -----------------------------------------------------------------
-- Run periodically via cron/scheduler:
--
--   PostgreSQL:
--     REFRESH MATERIALIZED VIEW mv_tx_summary;
--
--   SQLite (recreate table):
--     DROP TABLE IF EXISTS mv_tx_summary;
--     CREATE TABLE mv_tx_summary AS SELECT ...;
--
-- Frequency: Every 15 minutes or on-demand after bulk imports
--
--
-- Option 2: Concurrent Refresh (PostgreSQL, no locking)
-- -----------------------------------------------------------------
-- Requires unique index on materialized view:
--
--   CREATE UNIQUE INDEX ix_mv_tx_summary_unique 
--   ON mv_tx_summary(day, tag);
--
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary;
--
-- Benefits: Allows reads during refresh
-- Tradeoff: Slower refresh, requires unique index
--
--
-- Option 3: Incremental/Trigger-based (Advanced)
-- -----------------------------------------------------------------
-- Not implemented here. Would require:
-- - Tracking last refresh timestamp
-- - Only processing new transactions since last refresh
-- - More complex but efficient for high-volume systems
--
-- ============================================================

-- ============================================================
-- Sample Refresh Script (for cron job)
-- ============================================================
--
-- File: refresh_mv.sql
--
-- BEGIN;
-- 
-- -- For PostgreSQL:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tx_summary;
--
-- -- Log refresh timestamp
-- INSERT INTO mv_refresh_log (view_name, refreshed_at, row_count)
-- SELECT 'mv_tx_summary', NOW(), COUNT(*) FROM mv_tx_summary;
--
-- COMMIT;
--
-- ============================================================

-- ============================================================
-- Monitoring Table for Refresh History
-- ============================================================

CREATE TABLE IF NOT EXISTS mv_refresh_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    view_name TEXT NOT NULL,
    refreshed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    duration_ms INTEGER
);
