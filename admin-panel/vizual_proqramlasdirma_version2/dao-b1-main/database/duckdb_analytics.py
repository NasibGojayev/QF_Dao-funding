"""
DuckDB Analytics Layer for DAO Platform
=========================================
OLAP database for fast analytical queries, KPI calculations, and ML feature extraction.
Works alongside PostgreSQL (OLTP) for the best of both worlds.

Architecture:
- PostgreSQL: Real-time transactions (OLTP)
- DuckDB: Analytics, dashboards, ML features (OLAP)
"""
import os
import duckdb
import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


# =============================================================================
# DUCKDB CONNECTION MANAGER
# =============================================================================

class DuckDBManager:
    """
    Manages DuckDB connection for analytical queries.
    Supports both in-memory and persistent storage.
    """
    
    def __init__(self, db_path: str = "analytics.duckdb"):
        """
        Initialize DuckDB connection.
        
        Args:
            db_path: Path to DuckDB file. Use ":memory:" for in-memory.
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._setup_extensions()
    
    def _setup_extensions(self):
        """Load useful DuckDB extensions."""
        try:
            self.conn.execute("INSTALL httpfs; LOAD httpfs;")
        except:
            pass  # Extension may already be installed
    
    def execute(self, query: str, params: Optional[tuple] = None) -> duckdb.DuckDBPyRelation:
        """Execute a query and return result."""
        if params:
            return self.conn.execute(query, params)
        return self.conn.execute(query)
    
    def query_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return as pandas DataFrame."""
        result = self.execute(query, params)
        return result.fetchdf()
    
    def close(self):
        """Close connection."""
        self.conn.close()


# =============================================================================
# SCHEMA FOR ANALYTICAL TABLES
# =============================================================================

ANALYTICS_SCHEMA = """
-- ============================================================
-- DUCKDB ANALYTICS SCHEMA
-- ============================================================
-- Optimized for OLAP: aggregations, time-series, ML features

-- Transactions fact table (synced from PostgreSQL)
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id INTEGER PRIMARY KEY,
    tx_hash VARCHAR(66) UNIQUE,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    gas_used INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    block_number INTEGER,
    
    -- Denormalized for fast analytics
    user_wallet VARCHAR(42),
    project_name VARCHAR(255),
    project_category VARCHAR(100),
    
    -- Pre-computed features
    amount_usd DECIMAL(20, 2),
    is_first_donation BOOLEAN DEFAULT FALSE,
    donation_rank INTEGER
);

-- User aggregates (materialized)
CREATE TABLE IF NOT EXISTS dim_user_stats (
    user_id INTEGER PRIMARY KEY,
    wallet_address VARCHAR(42),
    first_tx_date TIMESTAMP,
    last_tx_date TIMESTAMP,
    total_transactions INTEGER DEFAULT 0,
    total_donated DECIMAL(20, 8) DEFAULT 0,
    avg_donation DECIMAL(20, 8) DEFAULT 0,
    unique_projects INTEGER DEFAULT 0,
    is_whale BOOLEAN DEFAULT FALSE,
    user_segment VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project aggregates (materialized)
CREATE TABLE IF NOT EXISTS dim_project_stats (
    project_id INTEGER PRIMARY KEY,
    project_name VARCHAR(255),
    category VARCHAR(100),
    total_raised DECIMAL(20, 8) DEFAULT 0,
    donor_count INTEGER DEFAULT 0,
    avg_donation DECIMAL(20, 8) DEFAULT 0,
    funding_velocity DECIMAL(10, 4),  -- ETH per day
    days_active INTEGER DEFAULT 0,
    qf_matching_estimate DECIMAL(20, 8),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily KPI snapshots (time-series)
CREATE TABLE IF NOT EXISTS kpi_daily (
    date DATE PRIMARY KEY,
    total_transactions INTEGER,
    total_volume_eth DECIMAL(20, 8),
    total_volume_usd DECIMAL(20, 2),
    active_users INTEGER,
    new_users INTEGER,
    returning_users INTEGER,
    avg_tx_amount DECIMAL(20, 8),
    median_tx_amount DECIMAL(20, 8),
    tx_success_rate DECIMAL(5, 2),
    avg_gas_used INTEGER,
    unique_projects_funded INTEGER,
    conversion_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hourly metrics for real-time dashboards
CREATE TABLE IF NOT EXISTS metrics_hourly (
    hour_start TIMESTAMP PRIMARY KEY,
    tx_count INTEGER,
    volume_eth DECIMAL(20, 8),
    unique_users INTEGER,
    avg_latency_ms INTEGER,
    error_count INTEGER,
    event_lag_seconds INTEGER
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fact_tx_date ON fact_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_fact_tx_user ON fact_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_fact_tx_project ON fact_transactions(project_id);
CREATE INDEX IF NOT EXISTS idx_kpi_date ON kpi_daily(date);
"""


def create_analytics_schema(conn: duckdb.DuckDBPyConnection):
    """Create analytical schema in DuckDB."""
    conn.execute(ANALYTICS_SCHEMA)


# =============================================================================
# ETL: SYNC FROM POSTGRESQL TO DUCKDB
# =============================================================================

class PostgresToDuckDBSync:
    """
    Sync data from PostgreSQL (OLTP) to DuckDB (OLAP).
    Supports incremental and full sync modes.
    """
    
    def __init__(self, duck_manager: DuckDBManager, pg_connection_string: str = None):
        self.duck = duck_manager
        self.pg_conn_str = pg_connection_string
    
    def sync_from_dataframe(self, df: pd.DataFrame, table_name: str, 
                            mode: str = "replace"):
        """
        Sync data from pandas DataFrame to DuckDB table.
        
        Args:
            df: Source DataFrame
            table_name: Target table name
            mode: 'replace' or 'append'
        """
        if mode == "replace":
            self.duck.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        self.duck.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
    
    def sync_transactions(self, transactions_df: pd.DataFrame):
        """Sync transactions from PostgreSQL export."""
        # Ensure correct types
        if 'created_at' in transactions_df.columns:
            transactions_df['created_at'] = pd.to_datetime(transactions_df['created_at'])
        
        self.duck.conn.execute("""
            INSERT OR REPLACE INTO fact_transactions 
            SELECT * FROM transactions_df
        """)
    
    def compute_user_stats(self):
        """Compute user statistics from transactions."""
        self.duck.conn.execute("""
            INSERT OR REPLACE INTO dim_user_stats
            SELECT 
                user_id,
                MAX(user_wallet) as wallet_address,
                MIN(created_at) as first_tx_date,
                MAX(created_at) as last_tx_date,
                COUNT(*) as total_transactions,
                SUM(amount) as total_donated,
                AVG(amount) as avg_donation,
                COUNT(DISTINCT project_id) as unique_projects,
                CASE WHEN SUM(amount) > 10 THEN TRUE ELSE FALSE END as is_whale,
                CASE 
                    WHEN COUNT(*) >= 10 THEN 'power_user'
                    WHEN COUNT(*) >= 3 THEN 'active'
                    ELSE 'casual'
                END as user_segment,
                CURRENT_TIMESTAMP as updated_at
            FROM fact_transactions
            GROUP BY user_id
        """)
    
    def compute_project_stats(self):
        """Compute project statistics."""
        self.duck.conn.execute("""
            INSERT OR REPLACE INTO dim_project_stats
            SELECT 
                project_id,
                MAX(project_name) as project_name,
                MAX(project_category) as category,
                SUM(amount) as total_raised,
                COUNT(DISTINCT user_id) as donor_count,
                AVG(amount) as avg_donation,
                SUM(amount) / GREATEST(1, DATE_DIFF('day', MIN(created_at), MAX(created_at))) as funding_velocity,
                DATE_DIFF('day', MIN(created_at), MAX(created_at)) as days_active,
                POWER(SUM(SQRT(amount)), 2) - SUM(amount) as qf_matching_estimate,
                CURRENT_TIMESTAMP as updated_at
            FROM fact_transactions
            GROUP BY project_id
        """)


# =============================================================================
# ANALYTICAL QUERIES
# =============================================================================

class AnalyticsQueries:
    """
    Pre-built analytical queries for dashboards and reporting.
    All queries are optimized for DuckDB's columnar storage.
    """
    
    def __init__(self, manager: DuckDBManager):
        self.db = manager
    
    # -------------------------------------------------------------------------
    # KPI CALCULATIONS
    # -------------------------------------------------------------------------
    
    def get_daily_kpis(self, date: datetime = None) -> Dict:
        """Get KPIs for a specific date."""
        date = date or datetime.now().date()
        
        result = self.db.query_df("""
            SELECT 
                COUNT(*) as total_tx,
                SUM(amount) as total_volume,
                COUNT(DISTINCT user_id) as active_users,
                AVG(amount) as avg_tx_amount,
                MEDIAN(amount) as median_tx_amount,
                COUNT(DISTINCT project_id) as projects_funded
            FROM fact_transactions
            WHERE DATE_TRUNC('day', created_at) = ?
        """, (date,))
        
        if len(result) > 0:
            return result.iloc[0].to_dict()
        return {}
    
    def get_kpi_trends(self, days: int = 30) -> pd.DataFrame:
        """Get KPI trends over time."""
        return self.db.query_df("""
            SELECT 
                DATE_TRUNC('day', created_at) as date,
                COUNT(*) as transactions,
                SUM(amount) as volume,
                COUNT(DISTINCT user_id) as users,
                AVG(amount) as avg_amount
            FROM fact_transactions
            WHERE created_at >= CURRENT_DATE - INTERVAL ? DAY
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY date
        """, (days,))
    
    # -------------------------------------------------------------------------
    # USER ANALYTICS
    # -------------------------------------------------------------------------
    
    def get_user_segments(self) -> pd.DataFrame:
        """Get user segmentation breakdown."""
        return self.db.query_df("""
            SELECT 
                user_segment,
                COUNT(*) as user_count,
                SUM(total_donated) as total_donated,
                AVG(total_transactions) as avg_transactions
            FROM dim_user_stats
            GROUP BY user_segment
            ORDER BY total_donated DESC
        """)
    
    def get_top_donors(self, limit: int = 10) -> pd.DataFrame:
        """Get top donors by total donated."""
        return self.db.query_df("""
            SELECT 
                user_id,
                wallet_address,
                total_donated,
                total_transactions,
                unique_projects,
                user_segment
            FROM dim_user_stats
            ORDER BY total_donated DESC
            LIMIT ?
        """, (limit,))
    
    def get_user_cohort_analysis(self) -> pd.DataFrame:
        """Cohort analysis by first transaction month."""
        return self.db.query_df("""
            SELECT 
                DATE_TRUNC('month', first_tx_date) as cohort_month,
                COUNT(*) as cohort_size,
                AVG(total_transactions) as avg_tx,
                AVG(total_donated) as avg_donated,
                SUM(CASE WHEN is_whale THEN 1 ELSE 0 END) as whales
            FROM dim_user_stats
            GROUP BY DATE_TRUNC('month', first_tx_date)
            ORDER BY cohort_month
        """)
    
    # -------------------------------------------------------------------------
    # PROJECT ANALYTICS
    # -------------------------------------------------------------------------
    
    def get_project_leaderboard(self, limit: int = 20) -> pd.DataFrame:
        """Top projects by funding."""
        return self.db.query_df("""
            SELECT 
                project_id,
                project_name,
                category,
                total_raised,
                donor_count,
                avg_donation,
                qf_matching_estimate,
                funding_velocity
            FROM dim_project_stats
            ORDER BY total_raised DESC
            LIMIT ?
        """, (limit,))
    
    def get_category_breakdown(self) -> pd.DataFrame:
        """Funding by category."""
        return self.db.query_df("""
            SELECT 
                category,
                COUNT(*) as project_count,
                SUM(total_raised) as total_raised,
                AVG(donor_count) as avg_donors,
                SUM(qf_matching_estimate) as total_qf_match
            FROM dim_project_stats
            GROUP BY category
            ORDER BY total_raised DESC
        """)
    
    # -------------------------------------------------------------------------
    # QUADRATIC FUNDING ANALYTICS
    # -------------------------------------------------------------------------
    
    def calculate_qf_distribution(self, pool_amount: float) -> pd.DataFrame:
        """
        Calculate quadratic funding distribution.
        
        Uses the formula: match_i = (pool * match_i_raw) / sum(match_raw)
        """
        return self.db.query_df("""
            WITH qf_raw AS (
                SELECT 
                    project_id,
                    project_name,
                    total_raised,
                    donor_count,
                    qf_matching_estimate as raw_match
                FROM dim_project_stats
            ),
            qf_normalized AS (
                SELECT 
                    *,
                    SUM(raw_match) OVER () as total_raw_match
                FROM qf_raw
            )
            SELECT 
                project_id,
                project_name,
                total_raised,
                donor_count,
                raw_match,
                (? * raw_match / NULLIF(total_raw_match, 0)) as final_match
            FROM qf_normalized
            ORDER BY final_match DESC
        """, (pool_amount,))
    
    # -------------------------------------------------------------------------
    # TIME-SERIES ANALYTICS
    # -------------------------------------------------------------------------
    
    def get_hourly_volume(self, hours: int = 24) -> pd.DataFrame:
        """Get hourly transaction volume."""
        return self.db.query_df("""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as tx_count,
                SUM(amount) as volume,
                COUNT(DISTINCT user_id) as unique_users
            FROM fact_transactions
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL ? HOUR
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour
        """, (hours,))
    
    def detect_volume_anomalies(self, std_threshold: float = 2.0) -> pd.DataFrame:
        """Detect unusual volume patterns."""
        return self.db.query_df("""
            WITH daily_stats AS (
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    SUM(amount) as daily_volume
                FROM fact_transactions
                GROUP BY DATE_TRUNC('day', created_at)
            ),
            stats AS (
                SELECT 
                    AVG(daily_volume) as avg_vol,
                    STDDEV(daily_volume) as std_vol
                FROM daily_stats
            )
            SELECT 
                date,
                daily_volume,
                (daily_volume - avg_vol) / NULLIF(std_vol, 0) as z_score,
                CASE 
                    WHEN ABS((daily_volume - avg_vol) / NULLIF(std_vol, 0)) > ? THEN 'ANOMALY'
                    ELSE 'NORMAL'
                END as status
            FROM daily_stats, stats
            ORDER BY date DESC
            LIMIT 30
        """, (std_threshold,))


# =============================================================================
# FEATURE EXTRACTION FOR ML
# =============================================================================

class MLFeatureExtractor:
    """
    Extract features for machine learning models.
    DuckDB is ideal for fast feature computation.
    """
    
    def __init__(self, manager: DuckDBManager):
        self.db = manager
    
    def extract_user_features(self) -> pd.DataFrame:
        """Extract user-level features for ML models."""
        return self.db.query_df("""
            SELECT 
                user_id,
                total_transactions,
                total_donated,
                avg_donation,
                unique_projects,
                DATE_DIFF('day', first_tx_date, CURRENT_DATE) as account_age_days,
                DATE_DIFF('day', last_tx_date, CURRENT_DATE) as days_since_last_tx,
                CASE WHEN is_whale THEN 1 ELSE 0 END as is_whale_flag,
                CASE user_segment
                    WHEN 'power_user' THEN 2
                    WHEN 'active' THEN 1
                    ELSE 0
                END as segment_score
            FROM dim_user_stats
        """)
    
    def extract_transaction_features(self) -> pd.DataFrame:
        """Extract transaction-level features."""
        return self.db.query_df("""
            SELECT 
                tx_id,
                user_id,
                project_id,
                amount,
                LOG(amount + 1) as log_amount,
                EXTRACT(HOUR FROM created_at) as tx_hour,
                EXTRACT(DOW FROM created_at) as tx_dow,
                CASE WHEN is_first_donation THEN 1 ELSE 0 END as is_first,
                donation_rank,
                -- Window features
                LAG(amount) OVER (PARTITION BY user_id ORDER BY created_at) as prev_amount,
                COUNT(*) OVER (PARTITION BY user_id ORDER BY created_at ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as tx_last_7
            FROM fact_transactions
            ORDER BY created_at
        """)
    
    def extract_project_features(self) -> pd.DataFrame:
        """Extract project-level features."""
        return self.db.query_df("""
            SELECT 
                project_id,
                total_raised,
                donor_count,
                avg_donation,
                LOG(donor_count + 1) as log_donors,
                funding_velocity,
                days_active,
                qf_matching_estimate,
                total_raised / NULLIF(donor_count, 0) as donation_concentration
            FROM dim_project_stats
        """)


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    import numpy as np
    
    print("=" * 60)
    print("DUCKDB ANALYTICS LAYER DEMO")
    print("=" * 60)
    
    # Create in-memory DuckDB
    manager = DuckDBManager(":memory:")
    create_analytics_schema(manager.conn)
    
    print("\n[1] Creating synthetic data...")
    
    # Generate synthetic transactions
    np.random.seed(42)
    n_transactions = 1000
    
    transactions = pd.DataFrame({
        'tx_id': range(1, n_transactions + 1),
        'tx_hash': [f"0x{''.join(np.random.choice(list('0123456789abcdef'), 64))}" for _ in range(n_transactions)],
        'user_id': np.random.randint(1, 101, n_transactions),
        'project_id': np.random.randint(1, 31, n_transactions),
        'amount': np.random.exponential(0.5, n_transactions),
        'gas_used': np.random.randint(21000, 100000, n_transactions),
        'status': np.random.choice(['success', 'pending', 'failed'], n_transactions, p=[0.95, 0.03, 0.02]),
        'created_at': pd.date_range('2024-01-01', periods=n_transactions, freq='h'),
        'block_number': np.random.randint(1000000, 2000000, n_transactions),
        'user_wallet': [f"0x{''.join(np.random.choice(list('0123456789abcdef'), 40))}" for _ in range(n_transactions)],
        'project_name': [f"Project {i % 30 + 1}" for i in range(n_transactions)],
        'project_category': np.random.choice(['environment', 'education', 'tech', 'health'], n_transactions),
        'amount_usd': None,
        'is_first_donation': np.random.choice([True, False], n_transactions, p=[0.3, 0.7]),
        'donation_rank': np.random.randint(1, 100, n_transactions)
    })
    
    # Load into DuckDB
    manager.conn.execute("INSERT INTO fact_transactions SELECT * FROM transactions")
    
    print(f"   Loaded {n_transactions} transactions")
    
    # Compute aggregates
    print("\n[2] Computing aggregates...")
    sync = PostgresToDuckDBSync(manager)
    sync.compute_user_stats()
    sync.compute_project_stats()
    print("   User and project stats computed")
    
    # Run analytics
    print("\n[3] Running analytical queries...")
    analytics = AnalyticsQueries(manager)
    
    # User segments
    segments = analytics.get_user_segments()
    print(f"\n   User Segments:")
    print(segments.to_string(index=False))
    
    # Category breakdown
    categories = analytics.get_category_breakdown()
    print(f"\n   Category Breakdown:")
    print(categories.to_string(index=False))
    
    # QF Distribution
    print("\n[4] Quadratic Funding Distribution (100 ETH pool)...")
    qf = analytics.calculate_qf_distribution(100.0)
    print(qf.head(5).to_string(index=False))
    
    # ML Features
    print("\n[5] Extracting ML Features...")
    ml = MLFeatureExtractor(manager)
    user_features = ml.extract_user_features()
    print(f"   Extracted {len(user_features)} user features")
    print(f"   Columns: {list(user_features.columns)}")
    
    print("\n[OK] DuckDB Analytics Layer Ready!")
    
    manager.close()
