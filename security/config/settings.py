"""
Security Module Configuration
Central configuration for security, monitoring, and alerting.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "name": os.getenv("DB_NAME", "doncoin"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['name']}"

# =============================================================================
# REDIS CONFIGURATION (for rate limiting)
# =============================================================================

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
}

REDIS_URL = f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

AUTH_CONFIG = {
    "secret_key": os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
}

# Default admin credentials (CHANGE IN PRODUCTION!)
DEFAULT_ADMIN = {
    "username": os.getenv("ADMIN_USERNAME", "admin"),
    "password": os.getenv("ADMIN_PASSWORD", "admin123"),  # Will be hashed
    "email": os.getenv("ADMIN_EMAIL", "admin@doncoin.dao"),
}

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

RATE_LIMIT_CONFIG = {
    # Default limits
    "default_limit": "100/minute",
    
    # Endpoint-specific limits
    "auth_limit": "5/minute",  # Login attempts
    "api_limit": "200/minute",  # General API
    "admin_limit": "50/minute",  # Admin endpoints
    "webhook_limit": "10/minute",  # Webhooks
    
    # Storage backend
    "storage_uri": REDIS_URL,
    
    # Enable/disable
    "enabled": True,
}

# =============================================================================
# MONITORING KPI CONFIGURATION
# =============================================================================

MONITORING_KPIS = {
    "event_processing_lag": {
        "name": "Event Processing Lag",
        "description": "Time between blockchain event and database persistence",
        "unit": "seconds",
        "warning_threshold": 30,
        "critical_threshold": 60,
        "target": 5,
    },
    "error_rate": {
        "name": "Error Rate",
        "description": "Percentage of failed API requests",
        "unit": "%",
        "warning_threshold": 1,
        "critical_threshold": 2,
        "target": 0.1,
    },
    "api_response_latency": {
        "name": "API Response Latency (P95)",
        "description": "95th percentile API response time",
        "unit": "ms",
        "warning_threshold": 500,
        "critical_threshold": 1000,
        "target": 200,
    },
    "suspicious_tx_count": {
        "name": "Suspicious Transactions",
        "description": "Number of transactions flagged as suspicious",
        "unit": "count/hour",
        "warning_threshold": 5,
        "critical_threshold": 10,
        "target": 0,
    },
}

# =============================================================================
# ALERTING CONFIGURATION
# =============================================================================

ALERT_CONFIG = {
    "enabled": True,
    
    # Alert channels
    "channels": {
        "email": {
            "enabled": os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", 587)),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "recipients": os.getenv("ALERT_RECIPIENTS", "").split(","),
        },
        "webhook": {
            "enabled": os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
            "url": os.getenv("ALERT_WEBHOOK_URL", ""),
        },
        "log": {
            "enabled": True,  # Always log alerts
        },
    },
    
    # Alert rules
    "rules": [
        {
            "name": "High Event Processing Lag",
            "kpi": "event_processing_lag",
            "condition": "value > 60",
            "severity": "critical",
            "cooldown_minutes": 5,
        },
        {
            "name": "Elevated Error Rate",
            "kpi": "error_rate",
            "condition": "value > 2",
            "severity": "critical",
            "cooldown_minutes": 10,
        },
        {
            "name": "Slow API Response",
            "kpi": "api_response_latency",
            "condition": "value > 1000",
            "severity": "warning",
            "cooldown_minutes": 15,
        },
        {
            "name": "Suspicious Activity Spike",
            "kpi": "suspicious_tx_count",
            "condition": "value > 10",
            "severity": "critical",
            "cooldown_minutes": 5,
        },
    ],
}

# =============================================================================
# DATA RETENTION CONFIGURATION
# =============================================================================

DATA_RETENTION_CONFIG = {
    # On-chain data (immutable, reference only)
    "on_chain": {
        "retention_days": None,  # Forever (blockchain is immutable)
        "description": "Transaction hashes, block numbers for verification",
    },
    
    # Off-chain operational data
    "off_chain_operational": {
        "retention_days": 90,
        "archive_after_days": 30,
        "description": "User sessions, API logs, request metadata",
    },
    
    # Analytics data
    "analytics": {
        "retention_days": 365,
        "archive_after_days": 90,
        "description": "Aggregated metrics, KPI history",
    },
    
    # Security logs
    "security_logs": {
        "retention_days": 730,  # 2 years
        "archive_after_days": 365,
        "description": "Auth events, admin access, security alerts",
    },
    
    # Model artifacts
    "model_artifacts": {
        "retention_days": 180,
        "archive_after_days": 60,
        "description": "Model predictions, feature logs",
    },
}

# =============================================================================
# SIEM/SOAR CONFIGURATION
# =============================================================================

SIEM_CONFIG = {
    "enabled": True,
    "log_format": "json",
    "log_file": str(LOGS_DIR / "siem_events.jsonl"),
    
    # Event categories
    "event_categories": [
        "authentication",
        "authorization",
        "data_access",
        "admin_action",
        "security_alert",
        "rate_limit",
        "suspicious_activity",
    ],
    
    # Correlation rules
    "correlation_rules": [
        {
            "name": "Brute Force Detection",
            "pattern": "5 failed logins from same IP in 5 minutes",
            "severity": "high",
            "action": "block_ip",
        },
        {
            "name": "Rate Limit Abuse",
            "pattern": "10 rate limit events from same IP in 1 minute",
            "severity": "medium",
            "action": "alert",
        },
    ],
}

# =============================================================================
# DASHBOARD CONFIGURATION
# =============================================================================

DASHBOARD_CONFIG = {
    "host": os.getenv("SECURITY_DASHBOARD_HOST", "0.0.0.0"),
    "port": int(os.getenv("SECURITY_DASHBOARD_PORT", 8060)),
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "refresh_interval_ms": 5000,  # Auto-refresh every 5 seconds
}
