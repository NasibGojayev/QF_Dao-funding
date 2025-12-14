"""
Feature Engineering Pipeline for DonCoin DAO
Creates derived features for ML models and dashboards.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class FeatureDefinition:
    """Definition of a derived feature"""
    name: str
    description: str
    source_tables: List[str]
    refresh_frequency: str  # 'real_time', 'hourly', 'daily'
    sql_definition: Optional[str] = None


# Feature Definitions
FEATURE_DEFINITIONS = [
    FeatureDefinition(
        name='avg_tx_per_day',
        description='Average number of transactions per wallet per day',
        source_tables=['donations', 'wallets'],
        refresh_frequency='hourly',
        sql_definition="""
            SELECT 
                w.wallet_id,
                COUNT(d.donation_id) / NULLIF(
                    GREATEST(1, EXTRACT(DAY FROM NOW() - MIN(d.created_at))), 0
                ) as avg_tx_per_day
            FROM base_wallet w
            LEFT JOIN base_donor do ON w.wallet_id = do.wallet_id
            LEFT JOIN base_donation d ON do.donor_id = d.donor_id
            GROUP BY w.wallet_id
        """
    ),
    FeatureDefinition(
        name='proposal_category_freq',
        description='Distribution of donations across proposal categories',
        source_tables=['donations', 'proposals'],
        refresh_frequency='hourly',
        sql_definition="""
            SELECT 
                d.donor_id,
                p.category,
                COUNT(*) as category_count,
                SUM(d.amount) as category_amount
            FROM base_donation d
            JOIN base_proposal p ON d.proposal_id = p.proposal_id
            GROUP BY d.donor_id, p.category
        """
    ),
    FeatureDefinition(
        name='event_lag_seconds',
        description='Time between blockchain event and database persistence',
        source_tables=['contract_events'],
        refresh_frequency='real_time',
        sql_definition="""
            SELECT 
                event_id,
                EXTRACT(EPOCH FROM (created_at - timestamp)) as lag_seconds
            FROM base_contractevent
            WHERE timestamp IS NOT NULL
        """
    ),
    FeatureDefinition(
        name='donation_velocity',
        description='Rate of donations over rolling time windows',
        source_tables=['donations'],
        refresh_frequency='hourly',
        sql_definition="""
            SELECT 
                donor_id,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as donations_1d,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as donations_7d,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as donations_30d,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as amount_1d,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as amount_7d,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as amount_30d
            FROM base_donation
            GROUP BY donor_id
        """
    ),
    FeatureDefinition(
        name='wallet_age_days',
        description='Days since wallet first activity',
        source_tables=['wallets', 'donations'],
        refresh_frequency='daily',
        sql_definition="""
            SELECT 
                w.wallet_id,
                EXTRACT(DAY FROM NOW() - MIN(d.created_at)) as wallet_age_days
            FROM base_wallet w
            LEFT JOIN base_donor do ON w.wallet_id = do.wallet_id
            LEFT JOIN base_donation d ON do.donor_id = d.donor_id
            GROUP BY w.wallet_id
        """
    ),
    FeatureDefinition(
        name='unique_recipients',
        description='Number of unique proposals a donor has contributed to',
        source_tables=['donations'],
        refresh_frequency='hourly',
        sql_definition="""
            SELECT 
                donor_id,
                COUNT(DISTINCT proposal_id) as unique_recipients
            FROM base_donation
            GROUP BY donor_id
        """
    ),
]


class FeatureEngineer:
    """
    Feature Engineering pipeline for creating derived features.
    
    Can work with:
    - pandas DataFrames (in-memory)
    - PostgreSQL (via SQL)
    - Real-time event streams
    """
    
    def __init__(self, db_connection=None):
        self.db_connection = db_connection
        self.feature_definitions = {f.name: f for f in FEATURE_DEFINITIONS}
        self.feature_cache: Dict[str, pd.DataFrame] = {}
        self.last_refresh: Dict[str, datetime] = {}
    
    def compute_wallet_features(self, 
                                 wallets: pd.DataFrame,
                                 donations: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all wallet-level features.
        
        Args:
            wallets: DataFrame with wallet_id, address
            donations: DataFrame with donor_id, wallet_id, amount, timestamp, proposal_id
        """
        # Initialize result DataFrame
        result = wallets[['wallet_id', 'address']].copy()
        
        # Merge donations with wallets
        if 'wallet_id' in donations.columns:
            donation_with_wallet = donations.copy()
        else:
            # Assume donations have donor_id and we need to map through donors
            donation_with_wallet = donations.copy()
            donation_with_wallet['wallet_id'] = donation_with_wallet['donor_id']  # Simplified
        
        # Convert timestamp
        if 'timestamp' in donation_with_wallet.columns:
            donation_with_wallet['timestamp'] = pd.to_datetime(donation_with_wallet['timestamp'])
        elif 'created_at' in donation_with_wallet.columns:
            donation_with_wallet['timestamp'] = pd.to_datetime(donation_with_wallet['created_at'])
        
        current_time = datetime.now()
        
        # Calculate features per wallet
        features_list = []
        
        for wallet_id in result['wallet_id'].unique():
            wallet_donations = donation_with_wallet[
                donation_with_wallet['wallet_id'] == wallet_id
            ]
            
            if len(wallet_donations) == 0:
                features_list.append({
                    'wallet_id': wallet_id,
                    'total_donations': 0,
                    'donation_count': 0,
                    'avg_donation': 0,
                    'max_donation': 0,
                    'min_donation': 0,
                    'std_donation': 0,
                    'unique_proposals': 0,
                    'wallet_age_days': 0,
                    'avg_tx_per_day': 0,
                    'donations_1d': 0,
                    'donations_7d': 0,
                    'donations_30d': 0,
                    'amount_1d': 0,
                    'amount_7d': 0,
                    'amount_30d': 0,
                    'days_since_last_tx': 365,
                    'recency_score': 0
                })
                continue
            
            amounts = wallet_donations['amount'].values
            timestamps = wallet_donations['timestamp']
            
            first_tx = timestamps.min()
            last_tx = timestamps.max()
            wallet_age = (current_time - first_tx.to_pydatetime().replace(tzinfo=None)).days
            days_since_last = (current_time - last_tx.to_pydatetime().replace(tzinfo=None)).days
            
            # Time-windowed features
            donations_1d = len(wallet_donations[
                timestamps >= current_time - timedelta(days=1)
            ])
            donations_7d = len(wallet_donations[
                timestamps >= current_time - timedelta(days=7)
            ])
            donations_30d = len(wallet_donations[
                timestamps >= current_time - timedelta(days=30)
            ])
            
            amount_1d = wallet_donations[
                timestamps >= current_time - timedelta(days=1)
            ]['amount'].sum()
            amount_7d = wallet_donations[
                timestamps >= current_time - timedelta(days=7)
            ]['amount'].sum()
            amount_30d = wallet_donations[
                timestamps >= current_time - timedelta(days=30)
            ]['amount'].sum()
            
            features_list.append({
                'wallet_id': wallet_id,
                'total_donations': float(np.sum(amounts)),
                'donation_count': len(amounts),
                'avg_donation': float(np.mean(amounts)),
                'max_donation': float(np.max(amounts)),
                'min_donation': float(np.min(amounts)),
                'std_donation': float(np.std(amounts)) if len(amounts) > 1 else 0,
                'unique_proposals': wallet_donations['proposal_id'].nunique() if 'proposal_id' in wallet_donations.columns else 0,
                'wallet_age_days': wallet_age,
                'avg_tx_per_day': len(amounts) / max(wallet_age, 1),
                'donations_1d': donations_1d,
                'donations_7d': donations_7d,
                'donations_30d': donations_30d,
                'amount_1d': float(amount_1d),
                'amount_7d': float(amount_7d),
                'amount_30d': float(amount_30d),
                'days_since_last_tx': days_since_last,
                'recency_score': max(0, 1 - days_since_last / 365)
            })
        
        features_df = pd.DataFrame(features_list)
        result = result.merge(features_df, on='wallet_id', how='left')
        
        return result
    
    def compute_proposal_features(self,
                                   proposals: pd.DataFrame,
                                   donations: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all proposal-level features.
        """
        result = proposals.copy()
        
        # Convert timestamps
        if 'created_at' in donations.columns:
            donations['timestamp'] = pd.to_datetime(donations['created_at'])
        
        current_time = datetime.now()
        
        # Aggregate donation features per proposal
        proposal_stats = donations.groupby('proposal_id').agg({
            'amount': ['sum', 'mean', 'std', 'count', 'max', 'min'],
            'donor_id': 'nunique',
            'timestamp': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        proposal_stats.columns = [
            'proposal_id', 
            'total_donated', 'avg_donation', 'std_donation', 'donation_count', 'max_donation', 'min_donation',
            'unique_donors',
            'first_donation', 'last_donation'
        ]
        
        # Calculate time-based features
        proposal_stats['days_active'] = (
            proposal_stats['last_donation'] - proposal_stats['first_donation']
        ).dt.days
        
        proposal_stats['days_since_last_donation'] = (
            current_time - proposal_stats['last_donation']
        ).dt.days
        
        proposal_stats['donations_per_day'] = (
            proposal_stats['donation_count'] / proposal_stats['days_active'].clip(lower=1)
        )
        
        # Merge with proposals
        result = result.merge(proposal_stats, on='proposal_id', how='left')
        
        # Calculate funding progress
        if 'funding_goal' in result.columns:
            result['funding_pct'] = (
                result['total_donated'] / result['funding_goal'].clip(lower=1) * 100
            ).clip(upper=100)
        
        # Fill NaN values
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        result[numeric_cols] = result[numeric_cols].fillna(0)
        
        return result
    
    def compute_real_time_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute features for a single transaction in real-time.
        
        Args:
            transaction: Dict with amount, timestamp, donor_id, proposal_id
        
        Returns:
            Dict of computed features
        """
        amount = transaction.get('amount', 0)
        timestamp = pd.to_datetime(transaction.get('timestamp', datetime.now()))
        
        features = {
            'amount': amount,
            'amount_log': np.log1p(amount),
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
            'is_night': 1 if timestamp.hour >= 22 or timestamp.hour <= 6 else 0,
            'is_business_hours': 1 if 9 <= timestamp.hour <= 17 else 0,
            'month': timestamp.month,
            'day_of_month': timestamp.day
        }
        
        return features
    
    def get_materialized_view_sql(self) -> Dict[str, str]:
        """Get SQL for creating materialized views"""
        views = {}
        
        # Donor aggregates
        views['mv_donor_stats'] = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_donor_stats AS
        SELECT 
            d.donor_id,
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
            COUNT(*) / NULLIF(GREATEST(1, EXTRACT(DAY FROM NOW() - MIN(d.created_at))), 0) as avg_donations_per_day
        FROM base_donation d
        GROUP BY d.donor_id
        WITH DATA;
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_donor_stats_donor_id ON mv_donor_stats(donor_id);
        """
        
        # Proposal performance
        views['mv_proposal_performance'] = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_proposal_performance AS
        SELECT 
            p.proposal_id,
            p.title,
            p.status,
            p.funding_goal,
            p.total_donations,
            p.created_at,
            COUNT(DISTINCT d.donor_id) as unique_donors,
            COUNT(d.donation_id) as donation_count,
            AVG(d.amount) as avg_donation,
            MAX(d.amount) as max_donation,
            MIN(d.created_at) as first_donation_at,
            MAX(d.created_at) as last_donation_at,
            (p.total_donations / NULLIF(p.funding_goal, 0) * 100) as funding_pct
        FROM base_proposal p
        LEFT JOIN base_donation d ON p.proposal_id = d.proposal_id
        GROUP BY p.proposal_id, p.title, p.status, p.funding_goal, p.total_donations, p.created_at
        WITH DATA;
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_proposal_perf_proposal_id ON mv_proposal_performance(proposal_id);
        """
        
        # Daily metrics
        views['mv_daily_metrics'] = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_metrics AS
        SELECT 
            DATE(d.created_at) as date,
            COUNT(*) as donation_count,
            SUM(d.amount) as total_amount,
            AVG(d.amount) as avg_amount,
            COUNT(DISTINCT d.donor_id) as unique_donors,
            COUNT(DISTINCT d.proposal_id) as unique_proposals
        FROM base_donation d
        GROUP BY DATE(d.created_at)
        ORDER BY date
        WITH DATA;
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_metrics_date ON mv_daily_metrics(date);
        """
        
        # Event processing metrics
        views['mv_event_lag_metrics'] = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_event_lag_metrics AS
        SELECT 
            DATE(timestamp) as date,
            event_type,
            COUNT(*) as event_count,
            AVG(EXTRACT(EPOCH FROM (created_at - timestamp))) as avg_lag_seconds,
            MAX(EXTRACT(EPOCH FROM (created_at - timestamp))) as max_lag_seconds,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (created_at - timestamp))) as p95_lag_seconds
        FROM base_contractevent
        WHERE timestamp IS NOT NULL
        GROUP BY DATE(timestamp), event_type
        WITH DATA;
        
        CREATE INDEX IF NOT EXISTS idx_mv_event_lag_date ON mv_event_lag_metrics(date);
        """
        
        return views
    
    def get_refresh_commands(self) -> Dict[str, str]:
        """Get SQL commands to refresh materialized views"""
        return {
            'mv_donor_stats': 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_donor_stats;',
            'mv_proposal_performance': 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_proposal_performance;',
            'mv_daily_metrics': 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_metrics;',
            'mv_event_lag_metrics': 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_event_lag_metrics;',
        }


if __name__ == "__main__":
    # Demo feature engineering
    print("Feature Engineering Demo")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    
    # Sample wallets
    wallets = pd.DataFrame({
        'wallet_id': [f'wallet_{i}' for i in range(10)],
        'address': [f'0x{i:040x}' for i in range(10)]
    })
    
    # Sample donations
    donations = []
    for i in range(100):
        donations.append({
            'donation_id': f'don_{i}',
            'donor_id': f'donor_{np.random.randint(0, 10)}',
            'wallet_id': f'wallet_{np.random.randint(0, 10)}',
            'proposal_id': f'proposal_{np.random.randint(0, 5)}',
            'amount': np.random.lognormal(5, 1),
            'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 90))
        })
    donations = pd.DataFrame(donations)
    
    # Sample proposals
    proposals = pd.DataFrame({
        'proposal_id': [f'proposal_{i}' for i in range(5)],
        'title': [f'Proposal {i}' for i in range(5)],
        'funding_goal': np.random.uniform(1000, 10000, 5)
    })
    
    # Compute features
    engineer = FeatureEngineer()
    
    print("\n1. Wallet Features:")
    wallet_features = engineer.compute_wallet_features(wallets, donations)
    print(wallet_features[['wallet_id', 'total_donations', 'donation_count', 'avg_tx_per_day', 'recency_score']].head())
    
    print("\n2. Proposal Features:")
    proposal_features = engineer.compute_proposal_features(proposals, donations)
    print(proposal_features[['proposal_id', 'title', 'total_donated', 'unique_donors', 'funding_pct']].head())
    
    print("\n3. Real-time Features for a transaction:")
    tx = {
        'amount': 150.0,
        'timestamp': datetime.now(),
        'donor_id': 'donor_1',
        'proposal_id': 'proposal_1'
    }
    rt_features = engineer.compute_real_time_features(tx)
    for k, v in rt_features.items():
        print(f"  {k}: {v}")
    
    print("\n4. Materialized View SQL:")
    views = engineer.get_materialized_view_sql()
    for name in views:
        print(f"  - {name}")
