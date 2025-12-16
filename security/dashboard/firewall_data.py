"""
Firewall Data Provider
Manages IP blacklist/whitelist and blocked request tracking
"""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text, Column, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.settings import DATABASE_URL, LOGS_DIR

# Create database engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    DB_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not connect to database: {e}")
    DB_AVAILABLE = False
    engine = None
    SessionLocal = None

# Local storage for IP lists (JSON file backup)
IP_LISTS_FILE = LOGS_DIR / "ip_lists.json"
BLOCKED_REQUESTS_FILE = LOGS_DIR / "blocked_requests.json"


def _load_ip_lists() -> Dict[str, List[Dict]]:
    """Load IP lists from JSON file"""
    if IP_LISTS_FILE.exists():
        try:
            with open(IP_LISTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"blacklist": [], "whitelist": []}


def _save_ip_lists(data: Dict[str, List[Dict]]):
    """Save IP lists to JSON file"""
    LOGS_DIR.mkdir(exist_ok=True)
    with open(IP_LISTS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _load_blocked_requests() -> List[Dict]:
    """Load blocked requests from JSON file"""
    if BLOCKED_REQUESTS_FILE.exists():
        try:
            with open(BLOCKED_REQUESTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def _save_blocked_requests(data: List[Dict]):
    """Save blocked requests to JSON file"""
    LOGS_DIR.mkdir(exist_ok=True)
    # Keep only last 1000 entries
    data = data[-1000:]
    with open(BLOCKED_REQUESTS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# =============================================================================
# IP LIST MANAGEMENT
# =============================================================================

def get_blacklist() -> List[Dict[str, Any]]:
    """Get all blacklisted IPs"""
    data = _load_ip_lists()
    return data.get("blacklist", [])


def get_whitelist() -> List[Dict[str, Any]]:
    """Get all whitelisted IPs"""
    data = _load_ip_lists()
    return data.get("whitelist", [])


def add_to_blacklist(ip: str, reason: str = "Manual block", added_by: str = "admin") -> bool:
    """Add an IP to the blacklist"""
    data = _load_ip_lists()
    
    # Check if already in blacklist
    for entry in data["blacklist"]:
        if entry["ip"] == ip:
            return False  # Already exists
    
    # Remove from whitelist if present
    data["whitelist"] = [e for e in data["whitelist"] if e["ip"] != ip]
    
    data["blacklist"].append({
        "ip": ip,
        "reason": reason,
        "added_by": added_by,
        "added_at": datetime.now().isoformat(),
        "expires_at": None  # Permanent by default
    })
    
    _save_ip_lists(data)
    _log_security_event("ip_blacklisted", {"ip": ip, "reason": reason, "added_by": added_by})
    return True


def add_to_whitelist(ip: str, reason: str = "Trusted IP", added_by: str = "admin") -> bool:
    """Add an IP to the whitelist"""
    data = _load_ip_lists()
    
    # Check if already in whitelist
    for entry in data["whitelist"]:
        if entry["ip"] == ip:
            return False  # Already exists
    
    # Remove from blacklist if present
    data["blacklist"] = [e for e in data["blacklist"] if e["ip"] != ip]
    
    data["whitelist"].append({
        "ip": ip,
        "reason": reason,
        "added_by": added_by,
        "added_at": datetime.now().isoformat()
    })
    
    _save_ip_lists(data)
    _log_security_event("ip_whitelisted", {"ip": ip, "reason": reason, "added_by": added_by})
    return True


def remove_from_blacklist(ip: str) -> bool:
    """Remove an IP from the blacklist"""
    data = _load_ip_lists()
    original_len = len(data["blacklist"])
    data["blacklist"] = [e for e in data["blacklist"] if e["ip"] != ip]
    
    if len(data["blacklist"]) < original_len:
        _save_ip_lists(data)
        _log_security_event("ip_unblacklisted", {"ip": ip})
        return True
    return False


def remove_from_whitelist(ip: str) -> bool:
    """Remove an IP from the whitelist"""
    data = _load_ip_lists()
    original_len = len(data["whitelist"])
    data["whitelist"] = [e for e in data["whitelist"] if e["ip"] != ip]
    
    if len(data["whitelist"]) < original_len:
        _save_ip_lists(data)
        _log_security_event("ip_unwhitelisted", {"ip": ip})
        return True
    return False


def is_ip_blocked(ip: str) -> bool:
    """Check if an IP is blocked"""
    data = _load_ip_lists()
    for entry in data["blacklist"]:
        if entry["ip"] == ip:
            # Check expiry
            if entry.get("expires_at"):
                if datetime.fromisoformat(entry["expires_at"]) < datetime.now():
                    remove_from_blacklist(ip)
                    return False
            return True
    return False


def is_ip_whitelisted(ip: str) -> bool:
    """Check if an IP is whitelisted"""
    data = _load_ip_lists()
    for entry in data["whitelist"]:
        if entry["ip"] == ip:
            return True
    return False


# =============================================================================
# BLOCKED REQUESTS TRACKING
# =============================================================================

def record_blocked_request(ip: str, reason: str, endpoint: str = "", user_agent: str = ""):
    """Record a blocked request"""
    requests = _load_blocked_requests()
    requests.append({
        "timestamp": datetime.now().isoformat(),
        "ip": ip,
        "reason": reason,
        "endpoint": endpoint,
        "user_agent": user_agent
    })
    _save_blocked_requests(requests)


def get_blocked_requests(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent blocked requests"""
    requests = _load_blocked_requests()
    return list(reversed(requests[-limit:]))


def get_blocked_requests_by_ip(ip: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get blocked requests for a specific IP"""
    requests = _load_blocked_requests()
    return [r for r in requests if r["ip"] == ip][-limit:]


def get_blocked_stats() -> Dict[str, Any]:
    """Get blocking statistics"""
    requests = _load_blocked_requests()
    
    # Count by reason
    reason_counts = {}
    ip_counts = {}
    
    # Only count last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent = [r for r in requests if datetime.fromisoformat(r["timestamp"]) > cutoff]
    
    for r in recent:
        reason = r.get("reason", "Unknown")
        ip = r.get("ip", "Unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    # Top blocked IPs
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_blocked_24h": len(recent),
        "total_blocked_all": len(requests),
        "by_reason": reason_counts,
        "top_blocked_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
        "blacklist_size": len(get_blacklist()),
        "whitelist_size": len(get_whitelist())
    }


# =============================================================================
# RATE LIMITING STATS
# =============================================================================

def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics"""
    # In production, this would come from Redis or a rate limit store
    # For now, generate from blocked requests with rate_limit reason
    requests = _load_blocked_requests()
    
    rate_limited = [r for r in requests if "rate" in r.get("reason", "").lower()]
    
    return {
        "total_rate_limited": len(rate_limited),
        "rate_limited_24h": len([
            r for r in rate_limited 
            if datetime.fromisoformat(r["timestamp"]) > datetime.now() - timedelta(hours=24)
        ]),
        "endpoints": {}  # Would be populated from actual rate limit middleware
    }


# =============================================================================
# SECURITY EVENT LOGGING
# =============================================================================

SECURITY_LOG_FILE = LOGS_DIR / "security_events.jsonl"


def _log_security_event(event_type: str, details: Dict[str, Any]):
    """Log a security event"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    
    with open(SECURITY_LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")


def get_security_events(limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recent security events"""
    if not SECURITY_LOG_FILE.exists():
        return []
    
    events = []
    with open(SECURITY_LOG_FILE, 'r') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                if event_type is None or event.get("event_type") == event_type:
                    events.append(event)
            except:
                continue
    
    return list(reversed(events[-limit:]))


# =============================================================================
# SAMPLE DATA FOR TESTING
# =============================================================================

def seed_sample_data():
    """Add sample data for testing"""
    # Add some sample IPs
    if not get_blacklist():
        add_to_blacklist("192.168.1.100", "Brute force attempt", "system")
        add_to_blacklist("10.0.0.50", "Suspicious activity", "admin")
    
    if not get_whitelist():
        add_to_whitelist("127.0.0.1", "Localhost", "system")
        add_to_whitelist("192.168.1.1", "Office gateway", "admin")
    
    # Add some sample blocked requests
    if not get_blocked_requests():
        for i in range(10):
            record_blocked_request(
                f"192.168.{i}.{i*10}",
                "Rate limit exceeded" if i % 2 == 0 else "Blacklisted IP",
                f"/api/v{i % 3}/endpoint",
                "Mozilla/5.0"
            )
