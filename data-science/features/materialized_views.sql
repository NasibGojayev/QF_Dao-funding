-- Materialized Views for DonCoin DAO Data Science
-- These views aggregate data for ML model inputs and dashboard KPIs

-- ============================================================
-- 1. DONOR STATISTICS MATERIALIZED VIEW
-- Aggregates donation patterns per donor for clustering/risk models
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_donor_stats AS
SELECT 
    d.donor_id,
    do.wallet_id,
    w.address as wallet_address,
    COUNT(*) as donation_count,
    SUM(d.amount) as total_donated,
    AVG(d.amount) as avg_donation,
    MAX(d.amount) as max_donation,
    MIN(d.amount) as min_donation,
    STDDEV(d.amount) as std_donation,
    COUNT(DISTINCT d.proposal_id) as unique_proposals,
    MIN(d.created_at) as first_donation,
    MAX(d.created_at) as last_donation,
    EXTRACT(DAY FROM NOW() - MIN(d.created_at)) as account_age_days,
    EXTRACT(DAY FROM NOW() - MAX(d.created_at)) as days_since_last_donation,
    COUNT(*) / NULLIF(GREATEST(1, EXTRACT(DAY FROM NOW() - MIN(d.created_at))), 0) as avg_donations_per_day,
    -- Time window aggregates
    COUNT(*) FILTER (WHERE d.created_at >= NOW() - INTERVAL '1 day') as donations_last_1d,
    COUNT(*) FILTER (WHERE d.created_at >= NOW() - INTERVAL '7 days') as donations_last_7d,
    COUNT(*) FILTER (WHERE d.created_at >= NOW() - INTERVAL '30 days') as donations_last_30d,
    SUM(d.amount) FILTER (WHERE d.created_at >= NOW() - INTERVAL '7 days') as amount_last_7d,
    SUM(d.amount) FILTER (WHERE d.created_at >= NOW() - INTERVAL '30 days') as amount_last_30d
FROM base_donation d
JOIN base_donor do ON d.donor_id = do.donor_id
JOIN base_wallet w ON do.wallet_id = w.wallet_id
GROUP BY d.donor_id, do.wallet_id, w.address
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_donor_stats_donor_id ON mv_donor_stats(donor_id);
CREATE INDEX IF NOT EXISTS idx_mv_donor_stats_wallet ON mv_donor_stats(wallet_id);

-- Refresh command (run hourly via cron or scheduler)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_donor_stats;

-- ============================================================
-- 2. PROPOSAL PERFORMANCE MATERIALIZED VIEW
-- Tracks proposal funding progress for recommender and forecasting
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_proposal_performance AS
SELECT 
    p.proposal_id,
    p.on_chain_id,
    p.title,
    p.status,
    p.funding_goal,
    p.total_donations,
    p.created_at,
    r.round_id,
    r.status as round_status,
    COUNT(DISTINCT d.donor_id) as unique_donors,
    COUNT(d.donation_id) as donation_count,
    AVG(d.amount) as avg_donation,
    MAX(d.amount) as max_donation,
    MIN(d.created_at) as first_donation_at,
    MAX(d.created_at) as last_donation_at,
    EXTRACT(DAY FROM NOW() - p.created_at) as days_since_creation,
    EXTRACT(DAY FROM MAX(d.created_at) - MIN(d.created_at)) as funding_duration_days,
    -- Funding metrics
    p.total_donations / NULLIF(p.funding_goal, 0) * 100 as funding_pct,
    CASE 
        WHEN p.total_donations >= p.funding_goal THEN 'funded'
        WHEN p.status = 'rejected' THEN 'failed'
        ELSE 'in_progress'
    END as funding_status,
    -- Velocity metrics
    SUM(d.amount) FILTER (WHERE d.created_at >= NOW() - INTERVAL '7 days') as amount_last_7d,
    COUNT(*) FILTER (WHERE d.created_at >= NOW() - INTERVAL '7 days') as donations_last_7d
FROM base_proposal p
LEFT JOIN base_donation d ON p.proposal_id = d.proposal_id
LEFT JOIN base_round r ON p.round_id = r.round_id
GROUP BY p.proposal_id, p.on_chain_id, p.title, p.status, p.funding_goal, 
         p.total_donations, p.created_at, r.round_id, r.status
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_proposal_perf_id ON mv_proposal_performance(proposal_id);
CREATE INDEX IF NOT EXISTS idx_mv_proposal_perf_status ON mv_proposal_performance(status);
CREATE INDEX IF NOT EXISTS idx_mv_proposal_perf_round ON mv_proposal_performance(round_id);

-- ============================================================
-- 3. DAILY METRICS MATERIALIZED VIEW
-- Time-series data for forecasting and trend analysis
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_metrics AS
SELECT 
    DATE(d.created_at) as date,
    COUNT(*) as donation_count,
    SUM(d.amount) as total_amount,
    AVG(d.amount) as avg_amount,
    STDDEV(d.amount) as std_amount,
    COUNT(DISTINCT d.donor_id) as unique_donors,
    COUNT(DISTINCT d.proposal_id) as unique_proposals,
    -- New donor count (first donation on this day)
    COUNT(*) FILTER (
        WHERE d.donor_id IN (
            SELECT donor_id FROM base_donation 
            GROUP BY donor_id 
            HAVING MIN(DATE(created_at)) = DATE(d.created_at)
        )
    ) as new_donors,
    -- Proposal creation count
    (SELECT COUNT(*) FROM base_proposal p WHERE DATE(p.created_at) = DATE(d.created_at)) as proposals_created
FROM base_donation d
GROUP BY DATE(d.created_at)
ORDER BY date
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_metrics_date ON mv_daily_metrics(date);

-- ============================================================
-- 4. EVENT PROCESSING LAG METRICS
-- For system monitoring KPI (event processing lag)
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_event_lag_metrics AS
SELECT 
    DATE(timestamp) as date,
    event_type,
    COUNT(*) as event_count,
    -- Assuming there's a way to track when event was persisted
    AVG(EXTRACT(EPOCH FROM (timestamp - timestamp))) as avg_lag_seconds,  -- Placeholder
    MAX(EXTRACT(EPOCH FROM (timestamp - timestamp))) as max_lag_seconds,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (timestamp - timestamp))) as p95_lag_seconds
FROM base_contractevent
WHERE timestamp IS NOT NULL
GROUP BY DATE(timestamp), event_type
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_event_lag_date ON mv_event_lag_metrics(date);
CREATE INDEX IF NOT EXISTS idx_mv_event_lag_type ON mv_event_lag_metrics(event_type);

-- ============================================================
-- 5. WALLET RISK SCORE CACHE
-- Pre-computed risk scores for quick lookup
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wallet_risk_cache AS
SELECT 
    w.wallet_id,
    w.address,
    w.status as wallet_status,
    COALESCE(ss.score, 0.5) as sybil_score,
    ds.donation_count,
    ds.total_donated,
    ds.unique_proposals,
    ds.avg_donations_per_day,
    -- Risk indicators
    CASE 
        WHEN ds.avg_donations_per_day > 10 THEN 0.3
        WHEN ds.avg_donations_per_day > 5 THEN 0.2
        ELSE 0
    END as high_frequency_indicator,
    CASE
        WHEN ds.unique_proposals = 1 AND ds.donation_count > 5 THEN 0.2
        ELSE 0
    END as single_target_indicator
FROM base_wallet w
LEFT JOIN mv_donor_stats ds ON w.wallet_id = ds.wallet_id
LEFT JOIN base_sybilscore ss ON w.wallet_id = ss.wallet_id
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_wallet_risk_id ON mv_wallet_risk_cache(wallet_id);
CREATE INDEX IF NOT EXISTS idx_mv_wallet_risk_address ON mv_wallet_risk_cache(address);

-- ============================================================
-- REFRESH SCHEDULE RECOMMENDATIONS
-- ============================================================
-- Run these via cron or Django management command:
--
-- Every hour:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_donor_stats;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_proposal_performance;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_wallet_risk_cache;
--
-- Every day at midnight:
--   REFRESH MATERIALIZED VIEW mv_daily_metrics;
--   REFRESH MATERIALIZED VIEW mv_event_lag_metrics;
--
-- Note: CONCURRENTLY requires a unique index on the view.
