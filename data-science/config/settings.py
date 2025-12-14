"""
Data Science Configuration Settings for DonCoin DAO
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'doncoin'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
}

# API Configuration
API_HOST = os.getenv('DS_API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('DS_API_PORT', 8051))

# Dashboard Configuration
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8050))

# Model Configuration
MODEL_CONFIG = {
    'risk_scorer': {
        'threshold': 0.7,  # Risk score threshold for flagging
        'model_path': 'models/saved/risk_scorer.pkl',
    },
    'recommender': {
        'n_recommendations': 5,
        'min_similarity': 0.3,
    },
    'clustering': {
        'n_clusters': 4,  # High-Value, Frequent, One-Time, At-Risk
        'random_state': 42,
    },
    'time_series': {
        'forecast_days': 30,
        'seasonality_mode': 'multiplicative',
    },
    'outlier_detection': {
        'contamination': 0.05,  # Expected anomaly rate
        'random_state': 42,
    }
}

# Logging Configuration
LOG_CONFIG = {
    'log_dir': 'logs/',
    'model_log_file': 'logs/model_predictions.jsonl',
    'experiment_log_file': 'logs/experiments.jsonl',
    'max_log_size_mb': 100,
}

# Experimentation Configuration
EXPERIMENT_CONFIG = {
    'default_traffic_split': [0.5, 0.5],  # Control vs Treatment
    'min_sample_size': 100,
    'significance_level': 0.05,
}

# KPI Thresholds for Alerts
KPI_THRESHOLDS = {
    'event_processing_lag_seconds': 5.0,  # Alert if > 5 seconds
    'api_response_latency_p95_ms': 200,   # Alert if > 200ms
    'error_rate_percent': 0.1,            # Alert if > 0.1%
    'suspicious_tx_daily_count': 10,      # Alert if > 10 per day
}

# Feature Engineering Configuration
FEATURE_CONFIG = {
    'time_windows': [1, 7, 30],  # Days for rolling features
    'refresh_interval_hours': 1,  # Materialized view refresh
}
