"""
SIEM Data Provider
Log parsing, event correlation, and Splunk-like search functionality
"""
import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import LOGS_DIR, DATABASE_URL
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Create database engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not connect to database: {e}")
    DB_AVAILABLE = False

# Log file paths
SIEM_LOG_FILE = LOGS_DIR / "siem_events.jsonl"
DJANGO_LOG_FILE = LOGS_DIR / "django_requests.jsonl"
ACCESS_LOG_FILE = LOGS_DIR / "access.jsonl"


# =============================================================================
# LOG INGESTION
# =============================================================================

def log_event(category: str, action: str, source_ip: str = "", 
              user: str = "", outcome: str = "success", details: Dict = None):
    """Log a SIEM event"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "action": action,
        "source_ip": source_ip,
        "user": user,
        "outcome": outcome,
        "details": details or {}
    }
    
    with open(SIEM_LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")
    
    return event


def log_django_request(method: str, path: str, status_code: int, 
                       ip: str = "", user: str = "", response_time_ms: float = 0):
    """Log a Django request"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "path": path,
        "status_code": status_code,
        "ip": ip,
        "user": user,
        "response_time_ms": response_time_ms
    }
    
    with open(DJANGO_LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")
    
    return event


def log_access(resource: str, action: str, user: str, ip: str = "", allowed: bool = True):
    """Log directory/resource access"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "resource": resource,
        "action": action,
        "user": user,
        "ip": ip,
        "allowed": allowed
    }
    
    with open(ACCESS_LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")
    
    return event


# =============================================================================
# LOG READING
# =============================================================================

def _read_jsonl_file(filepath: Path, limit: int = 1000) -> List[Dict]:
    """Read a JSONL file and return last N entries"""
    if not filepath.exists():
        return []
    
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                continue
    
    return events[-limit:]


def get_siem_events(limit: int = 500) -> List[Dict[str, Any]]:
    """Get SIEM events"""
    return list(reversed(_read_jsonl_file(SIEM_LOG_FILE, limit)))


def get_django_logs(limit: int = 500) -> List[Dict[str, Any]]:
    """Get Django request logs"""
    return list(reversed(_read_jsonl_file(DJANGO_LOG_FILE, limit)))


def get_access_logs(limit: int = 500) -> List[Dict[str, Any]]:
    """Get access logs"""
    return list(reversed(_read_jsonl_file(ACCESS_LOG_FILE, limit)))


# =============================================================================
# SEARCH FUNCTIONALITY (Splunk-like)
# =============================================================================

def search_logs(query: str = "", category: str = "", 
                source_ip: str = "", outcome: str = "",
                start_time: datetime = None, end_time: datetime = None,
                limit: int = 200) -> List[Dict[str, Any]]:
    """
    Search logs with multiple filters (Splunk-like)
    
    Args:
        query: Free text search across all fields
        category: Filter by category (authentication, admin_action, etc.)
        source_ip: Filter by source IP
        outcome: Filter by outcome (success, failure, blocked)
        start_time: Start of time range
        end_time: End of time range
        limit: Max results
    """
    # Combine all log sources
    all_events = []
    
    # SIEM events
    for event in get_siem_events(1000):
        event["source"] = "siem"
        all_events.append(event)
    
    # Django logs
    for event in get_django_logs(1000):
        event["source"] = "django"
        event["category"] = "api_request"
        event["action"] = f"{event.get('method', '')} {event.get('path', '')}"
        event["outcome"] = "success" if event.get("status_code", 0) < 400 else "failure"
        all_events.append(event)
    
    # Access logs
    for event in get_access_logs(1000):
        event["source"] = "access"
        event["category"] = "data_access"
        event["outcome"] = "success" if event.get("allowed") else "blocked"
        all_events.append(event)
    
    # Contract events from database
    if DB_AVAILABLE:
        try:
            session = SessionLocal()
            db_events = session.execute(text("""
                SELECT 
                    timestamp, event_type, tx_hash,
                    COALESCE(p.title, 'N/A') as proposal
                FROM base_contractevent ce
                LEFT JOIN base_proposal p ON ce.proposal_id = p.proposal_id
                ORDER BY timestamp DESC
                LIMIT 200
            """)).fetchall()
            
            for event in db_events:
                all_events.append({
                    "timestamp": event[0].isoformat() if event[0] else "",
                    "source": "blockchain",
                    "category": "smart_contract",
                    "action": event[1],
                    "tx_hash": event[2],
                    "proposal": event[3],
                    "outcome": "success"
                })
            session.close()
        except Exception as e:
            print(f"Error fetching blockchain events: {e}")
    
    # Sort by timestamp (newest first)
    all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Apply filters
    filtered = []
    for event in all_events:
        # Time filter
        if start_time or end_time:
            try:
                event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", ""))
                if start_time and event_time < start_time:
                    continue
                if end_time and event_time > end_time:
                    continue
            except:
                pass
        
        # Category filter
        if category and event.get("category", "").lower() != category.lower():
            continue
        
        # Source IP filter
        if source_ip:
            event_ip = event.get("source_ip", "") or event.get("ip", "")
            if source_ip.lower() not in event_ip.lower():
                continue
        
        # Outcome filter
        if outcome and event.get("outcome", "").lower() != outcome.lower():
            continue
        
        # Free text search
        if query:
            query_lower = query.lower()
            event_str = json.dumps(event).lower()
            if query_lower not in event_str:
                continue
        
        filtered.append(event)
        
        if len(filtered) >= limit:
            break
    
    return filtered


# =============================================================================
# TRANSACTION HISTORY
# =============================================================================

def get_transaction_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get blockchain transaction history from database"""
    if not DB_AVAILABLE:
        return []
    
    try:
        session = SessionLocal()
        
        # Get donations (transactions)
        donations = session.execute(text(f"""
            SELECT 
                d.created_at,
                d.amount,
                w.address as donor_address,
                p.title as proposal,
                d.donation_id
            FROM base_donation d
            JOIN base_donor dn ON d.donor_id = dn.donor_id
            JOIN base_wallet w ON dn.wallet_id = w.wallet_id
            JOIN base_proposal p ON d.proposal_id = p.proposal_id
            ORDER BY d.created_at DESC
            LIMIT {limit}
        """)).fetchall()
        
        result = []
        for d in donations:
            result.append({
                "timestamp": d[0].isoformat() if d[0] else "",
                "type": "donation",
                "amount": float(d[1]),
                "from_address": d[2],
                "to": d[3],
                "tx_id": str(d[4])[:8]
            })
        
        session.close()
        return result
        
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []


# =============================================================================
# EVENT CORRELATION
# =============================================================================

def get_event_summary(hours: int = 24) -> Dict[str, Any]:
    """Get event summary for dashboard"""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    all_events = search_logs(limit=10000)
    
    # Filter to time range
    recent = [
        e for e in all_events 
        if e.get("timestamp") and datetime.fromisoformat(e["timestamp"].replace("Z", "")) > cutoff
    ]
    
    # Count by category
    by_category = defaultdict(int)
    by_outcome = defaultdict(int)
    by_source = defaultdict(int)
    
    for event in recent:
        by_category[event.get("category", "unknown")] += 1
        by_outcome[event.get("outcome", "unknown")] += 1
        by_source[event.get("source", "unknown")] += 1
    
    return {
        "total_events": len(recent),
        "by_category": dict(by_category),
        "by_outcome": dict(by_outcome),
        "by_source": dict(by_source),
        "time_range_hours": hours
    }


def get_security_alerts() -> List[Dict[str, Any]]:
    """Detect security alerts from event patterns"""
    alerts = []
    
    # Check for brute force (many failures from same IP)
    events = search_logs(outcome="failure", limit=500)
    ip_failures = defaultdict(int)
    
    cutoff = datetime.now() - timedelta(minutes=15)
    for event in events:
        try:
            if datetime.fromisoformat(event["timestamp"]) > cutoff:
                ip = event.get("source_ip") or event.get("ip", "")
                if ip:
                    ip_failures[ip] += 1
        except:
            pass
    
    for ip, count in ip_failures.items():
        if count >= 5:
            alerts.append({
                "id": f"BRUTE-{ip[:8]}",
                "type": "brute_force",
                "severity": "high",
                "message": f"Possible brute force from {ip}: {count} failures in 15 min",
                "ip": ip,
                "count": count,
                "detected_at": datetime.now().isoformat()
            })
    
    return alerts


# =============================================================================
# EXPORT
# =============================================================================

def export_logs(format: str = "json", **search_params) -> str:
    """Export logs to JSON or CSV format"""
    events = search_logs(**search_params)
    
    if format == "csv":
        if not events:
            return "timestamp,source,category,action,outcome\n"
        
        # Get all unique keys
        all_keys = set()
        for e in events:
            all_keys.update(e.keys())
        keys = sorted(all_keys)
        
        lines = [",".join(keys)]
        for e in events:
            row = [str(e.get(k, "")).replace(",", ";").replace("\n", " ") for k in keys]
            lines.append(",".join(row))
        
        return "\n".join(lines)
    
    else:  # JSON
        return json.dumps(events, indent=2, default=str)


# =============================================================================
# SAMPLE DATA
# =============================================================================

def seed_sample_logs():
    """Generate sample log data for testing"""
    categories = ["authentication", "admin_action", "data_access", "api_request"]
    actions = ["login", "logout", "create", "delete", "update", "view"]
    outcomes = ["success", "success", "success", "failure", "blocked"]
    
    for i in range(50):
        log_event(
            category=categories[i % len(categories)],
            action=actions[i % len(actions)],
            source_ip=f"192.168.1.{i % 255}",
            user=f"user{i % 5}",
            outcome=outcomes[i % len(outcomes)],
            details={"request_id": f"req-{i}"}
        )
    
    # Sample Django requests
    for i in range(30):
        log_django_request(
            method=["GET", "POST", "PUT", "DELETE"][i % 4],
            path=f"/api/v1/{['proposals', 'donations', 'rounds', 'wallets'][i % 4]}/",
            status_code=[200, 201, 400, 401, 500][i % 5],
            ip=f"10.0.0.{i % 255}",
            user=f"user{i % 3}",
            response_time_ms=50 + (i * 10)
        )
    
    # Sample access logs
    for i in range(20):
        log_access(
            resource=f"/data/{['contracts', 'users', 'logs', 'config'][i % 4]}/",
            action=["read", "write", "delete"][i % 3],
            user=f"admin{i % 2}",
            ip=f"172.16.0.{i % 255}",
            allowed=i % 5 != 0
        )
