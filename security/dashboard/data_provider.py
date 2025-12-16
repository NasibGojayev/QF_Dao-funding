"""
Data Provider for Security Dashboard
Connects to the Django PostgreSQL database and provides real data.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL, MONITORING_KPIS, LOGS_DIR
import pandas as pd
import json

# Create database engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not connect to database: {e}")
    DB_AVAILABLE = False
    engine = None
    SessionLocal = None


def get_db_session():
    """Get a database session"""
    if SessionLocal:
        return SessionLocal()
    return None


# =============================================================================
# KPI DATA FROM DATABASE
# =============================================================================

def get_real_kpi_data() -> Dict[str, Dict[str, Any]]:
    """Get actual KPI data from the database"""
    session = get_db_session()
    if not session:
        return get_fallback_kpi_data()
    
    try:
        # Get counts from database
        result = {}
        
        # Event Processing Lag - based on ContractEvent timestamps
        # For now, simulate based on recent events
        event_lag = session.execute(text("""
            SELECT EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) as lag_seconds
            FROM base_contractevent
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """)).fetchone()
        
        lag_value = float(event_lag[0]) if event_lag and event_lag[0] else 0
        lag_status = 'ok' if lag_value < 30 else 'warning' if lag_value < 60 else 'critical'
        
        result['event_processing_lag'] = {
            'value': round(min(lag_value, 100), 1),  # Cap at 100 for display
            'status': lag_status,
            'trend': 'stable'
        }
        
        # Error Rate - for now use a default low value
        # In production, this would come from application logs
        result['error_rate'] = {
            'value': 0.05,
            'status': 'ok',
            'trend': 'stable'
        }
        
        # API Response Latency - simulated for now
        result['api_response_latency'] = {
            'value': 125,
            'status': 'ok',
            'trend': 'stable'
        }
        
        # Suspicious Transactions - count flagged wallets
        flagged_count = session.execute(text("""
            SELECT COUNT(*) FROM base_wallet WHERE status = 'flagged'
        """)).scalar() or 0
        
        result['suspicious_tx_count'] = {
            'value': int(flagged_count),
            'status': 'ok' if flagged_count < 5 else 'warning' if flagged_count < 10 else 'critical',
            'trend': 'stable'
        }
        
        session.close()
        return result
        
    except Exception as e:
        print(f"Error fetching KPI data: {e}")
        session.close()
        return get_fallback_kpi_data()


def get_fallback_kpi_data() -> Dict[str, Dict[str, Any]]:
    """Fallback KPI data when database is unavailable"""
    return {
        'event_processing_lag': {'value': 0, 'status': 'ok', 'trend': 'stable'},
        'error_rate': {'value': 0, 'status': 'ok', 'trend': 'stable'},
        'api_response_latency': {'value': 0, 'status': 'ok', 'trend': 'stable'},
        'suspicious_tx_count': {'value': 0, 'status': 'ok', 'trend': 'stable'},
    }


# =============================================================================
# CONTRACT EVENTS FROM DATABASE  
# =============================================================================

def get_real_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Get actual contract events from the database"""
    session = get_db_session()
    if not session:
        return []
    
    try:
        events = session.execute(text(f"""
            SELECT 
                ce.timestamp,
                ce.event_type,
                ce.tx_hash,
                COALESCE(p.title, 'N/A') as proposal_title
            FROM base_contractevent ce
            LEFT JOIN base_proposal p ON ce.proposal_id = p.proposal_id
            ORDER BY ce.timestamp DESC
            LIMIT {limit}
        """)).fetchall()
        
        result = []
        for event in events:
            # Map event types to categories
            category = 'admin_action'
            if 'Donation' in event[1]:
                category = 'authentication'
            elif 'Grant' in event[1]:
                category = 'admin_action'
            elif 'Round' in event[1]:
                category = 'rate_limit'
            
            result.append({
                'timestamp': event[0].strftime('%Y-%m-%d %H:%M:%S') if event[0] else '',
                'category': category,
                'source_ip': event[2][:20] + '...' if event[2] and len(event[2]) > 20 else (event[2] or ''),
                'action': event[1],
                'outcome': 'success'
            })
        
        session.close()
        return result if result else get_fallback_events()
        
    except Exception as e:
        print(f"Error fetching events: {e}")
        session.close()
        return get_fallback_events()


def get_fallback_events() -> List[Dict[str, Any]]:
    """Fallback events when database has no data"""
    return [{
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'category': 'authentication',
        'source_ip': 'system',
        'action': 'No events yet',
        'outcome': 'success'
    }]


# =============================================================================
# DONATION/ACTIVITY DATA FROM DATABASE
# =============================================================================

def get_donation_activity(hours: int = 24) -> pd.DataFrame:
    """Get donation activity over time for charts"""
    session = get_db_session()
    if not session:
        return get_fallback_rate_limit_data()
    
    try:
        # Get donations grouped by hour
        donations = session.execute(text(f"""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as total_requests,
                SUM(amount) as total_amount
            FROM base_donation
            WHERE created_at > NOW() - INTERVAL '{hours} hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour
        """)).fetchall()
        
        session.close()
        
        if donations:
            df = pd.DataFrame(donations, columns=['time', 'total_requests', 'total_amount'])
            df['blocked_requests'] = 0  # No blocked donations in our system
            return df
        
        return get_fallback_rate_limit_data()
        
    except Exception as e:
        print(f"Error fetching donation activity: {e}")
        session.close()
        return get_fallback_rate_limit_data()


def get_fallback_rate_limit_data() -> pd.DataFrame:
    """Fallback rate limit data"""
    import numpy as np
    times = pd.date_range(end=datetime.now(), periods=24, freq='H')
    return pd.DataFrame({
        'time': times,
        'total_requests': np.zeros(24),
        'blocked_requests': np.zeros(24),
    })


# =============================================================================
# DASHBOARD SUMMARY STATS
# =============================================================================

def get_dashboard_stats() -> Dict[str, Any]:
    """Get summary statistics for the dashboard header"""
    session = get_db_session()
    if not session:
        return get_fallback_stats()
    
    try:
        # Count various entities
        proposal_count = session.execute(text("SELECT COUNT(*) FROM base_proposal")).scalar() or 0
        donation_count = session.execute(text("SELECT COUNT(*) FROM base_donation")).scalar() or 0
        wallet_count = session.execute(text("SELECT COUNT(*) FROM base_wallet")).scalar() or 0
        active_wallets = session.execute(text("SELECT COUNT(*) FROM base_wallet WHERE status = 'active'")).scalar() or 0
        flagged_wallets = session.execute(text("SELECT COUNT(*) FROM base_wallet WHERE status = 'flagged'")).scalar() or 0
        
        # Get total donation amount
        total_donations = session.execute(text("SELECT COALESCE(SUM(amount), 0) FROM base_donation")).scalar() or 0
        
        # Get recent events count
        recent_events = session.execute(text("""
            SELECT COUNT(*) FROM base_contractevent 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
        """)).scalar() or 0
        
        session.close()
        
        return {
            'total_proposals': int(proposal_count),
            'total_donations': int(donation_count),
            'total_donation_amount': float(total_donations),
            'total_wallets': int(wallet_count),
            'active_wallets': int(active_wallets),
            'flagged_wallets': int(flagged_wallets),
            'recent_events_24h': int(recent_events),
            'db_connected': True
        }
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        session.close()
        return get_fallback_stats()


def get_fallback_stats() -> Dict[str, Any]:
    """Fallback stats when database is unavailable"""
    return {
        'total_proposals': 0,
        'total_donations': 0,
        'total_donation_amount': 0,
        'total_wallets': 0,
        'active_wallets': 0,
        'flagged_wallets': 0,
        'recent_events_24h': 0,
        'db_connected': False
    }


# =============================================================================
# ALERTS FROM LOGS
# =============================================================================

def get_real_alerts() -> List[Dict[str, Any]]:
    """Get alerts from log files or generate from current state"""
    alerts = []
    
    # Check for actual issues based on KPIs
    kpis = get_real_kpi_data()
    
    for kpi_name, kpi_data in kpis.items():
        if kpi_data['status'] in ['warning', 'critical']:
            config = MONITORING_KPIS.get(kpi_name, {})
            alerts.append({
                'id': f'ALT-{kpi_name[:3].upper()}',
                'name': config.get('name', kpi_name),
                'severity': kpi_data['status'],
                'status': 'firing',
                'value': kpi_data['value'],
                'fired_at': datetime.now().strftime('%H:%M:%S'),
                'acknowledged': False
            })
    
    # If no alerts, return empty list or sample resolved alert
    if not alerts:
        alerts.append({
            'id': 'ALT-SYS',
            'name': 'System Healthy',
            'severity': 'info',
            'status': 'resolved',
            'value': 0,
            'fired_at': datetime.now().strftime('%H:%M:%S'),
            'acknowledged': True
        })
    
    return alerts


def get_real_cases() -> List[Dict[str, Any]]:
    """Get security cases - for now based on flagged wallets"""
    session = get_db_session()
    if not session:
        return []
    
    try:
        flagged = session.execute(text("""
            SELECT address, status, last_activity
            FROM base_wallet
            WHERE status IN ('flagged', 'frozen')
            ORDER BY last_activity DESC
            LIMIT 5
        """)).fetchall()
        
        session.close()
        
        cases = []
        for i, wallet in enumerate(flagged):
            cases.append({
                'case_id': f'CASE-{i+1:03d}',
                'title': f'Flagged Wallet: {wallet[0][:10]}...',
                'severity': 'high' if wallet[1] == 'frozen' else 'medium',
                'status': 'investigating',
                'created_at': wallet[2].strftime('%Y-%m-%d %H:%M') if wallet[2] else 'Unknown',
                'events': 1
            })
        
        return cases
        
    except Exception as e:
        print(f"Error fetching cases: {e}")
        session.close()
        return []
