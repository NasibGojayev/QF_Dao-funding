"""
Sprint 3: Complete Security Controls Module
- Admin Authentication and Access Logging
- Rate Limiting Enforcement
- Data Retention Module
- Fault Simulation for Alert Testing
- Metrics Endpoints
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== ADMIN AUTHENTICATION ====================

class AdminAuthManager:
    """Basic authentication for admin dashboard and privileged endpoints"""
    
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.access_log: List[Dict] = []
        self.failed_attempts: Dict[str, List] = defaultdict(list)
        self.lock = Lock()
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
        # Initialize default admin (should be changed in production)
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        self._hash_and_store('admin', 'dao_admin_2024', role='superadmin')
        self._hash_and_store('operator', 'operator_2024', role='operator')
        logger.info("Default admin users created")
    
    def _hash_and_store(self, username: str, password: str, role: str = 'admin'):
        """Hash password and store user"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'role': role,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None
        }
    
    def authenticate(self, username: str, password: str, ip_address: str = 'unknown') -> Optional[str]:
        """Authenticate user and return session token"""
        with self.lock:
            # Check if account is locked
            if self._is_locked(username):
                self._log_access(username, ip_address, 'LOGIN_FAILED', 'Account locked')
                return None
            
            if username not in self.users:
                self._log_access(username, ip_address, 'LOGIN_FAILED', 'User not found')
                self._record_failed_attempt(username)
                return None
            
            user = self.users[username]
            password_hash = hashlib.sha256((password + user['salt']).encode()).hexdigest()
            
            if password_hash != user['password_hash']:
                self._log_access(username, ip_address, 'LOGIN_FAILED', 'Invalid password')
                self._record_failed_attempt(username)
                return None
            
            # Successful login
            token = secrets.token_urlsafe(32)
            self.sessions[token] = {
                'username': username,
                'role': user['role'],
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                'ip_address': ip_address
            }
            
            user['last_login'] = datetime.utcnow().isoformat()
            self._log_access(username, ip_address, 'LOGIN_SUCCESS', f'Role: {user["role"]}')
            self.failed_attempts[username] = []  # Clear failed attempts
            
            return token
    
    def validate_session(self, token: str) -> Optional[Dict]:
        """Validate session token"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        if datetime.fromisoformat(session['expires_at']) < datetime.utcnow():
            del self.sessions[token]
            return None
        
        return session
    
    def logout(self, token: str, ip_address: str = 'unknown'):
        """Invalidate session"""
        if token in self.sessions:
            username = self.sessions[token]['username']
            del self.sessions[token]
            self._log_access(username, ip_address, 'LOGOUT', 'Session terminated')
    
    def _is_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        attempts = self.failed_attempts.get(username, [])
        recent = [a for a in attempts if (datetime.utcnow() - datetime.fromisoformat(a)).seconds < self.lockout_duration]
        return len(recent) >= self.max_failed_attempts
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        self.failed_attempts[username].append(datetime.utcnow().isoformat())
    
    def _log_access(self, username: str, ip_address: str, action: str, details: str):
        """Log all admin access"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'username': username,
            'ip_address': ip_address,
            'action': action,
            'details': details
        }
        self.access_log.append(log_entry)
        logger.info(f"ADMIN_ACCESS: {json.dumps(log_entry)}")
        
        # Keep only last 10000 entries
        if len(self.access_log) > 10000:
            self.access_log = self.access_log[-10000:]
    
    def get_access_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent access logs"""
        return self.access_log[-limit:]


# ==================== RATE LIMITING ====================

class RateLimiter:
    """Token bucket rate limiting with monitoring hooks"""
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 20):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.buckets: Dict[str, Dict] = {}
        self.violations: List[Dict] = []
        self.lock = Lock()
    
    def check_rate_limit(self, identifier: str, endpoint: str = '/') -> tuple:
        """
        Check if request is allowed under rate limit
        Returns: (allowed: bool, remaining: int, reset_time: int)
        """
        with self.lock:
            now = time.time()
            
            if identifier not in self.buckets:
                self.buckets[identifier] = {
                    'tokens': self.burst_size,
                    'last_update': now
                }
            
            bucket = self.buckets[identifier]
            
            # Refill tokens based on time elapsed
            elapsed = now - bucket['last_update']
            refill = (elapsed / 60) * self.requests_per_minute
            bucket['tokens'] = min(self.burst_size, bucket['tokens'] + refill)
            bucket['last_update'] = now
            
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return (True, int(bucket['tokens']), 60)
            else:
                # Rate limit exceeded
                self._record_violation(identifier, endpoint)
                return (False, 0, 60)
    
    def _record_violation(self, identifier: str, endpoint: str):
        """Record rate limit violation"""
        violation = {
            'timestamp': datetime.utcnow().isoformat(),
            'identifier': identifier,
            'endpoint': endpoint
        }
        self.violations.append(violation)
        logger.warning(f"RATE_LIMIT_EXCEEDED: {json.dumps(violation)}")
        
        # Keep only last 10000 violations
        if len(self.violations) > 10000:
            self.violations = self.violations[-10000:]
    
    def get_violations(self, limit: int = 100) -> List[Dict]:
        """Get recent rate limit violations"""
        return self.violations[-limit:]
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        recent_violations = len([v for v in self.violations 
                                if (datetime.utcnow() - datetime.fromisoformat(v['timestamp'])).seconds < 600])
        return {
            'total_violations': len(self.violations),
            'violations_last_10_min': recent_violations,
            'active_buckets': len(self.buckets)
        }


# ==================== DATA RETENTION ====================

class DataRetentionManager:
    """Manage data retention and archival"""
    
    def __init__(self, retention_days: int = 90, archive_enabled: bool = True):
        self.retention_days = retention_days
        self.archive_enabled = archive_enabled
        self.archival_log: List[Dict] = []
    
    def check_retention(self, data_type: str, created_at: datetime) -> Dict:
        """Check if data should be retained, archived, or deleted"""
        age_days = (datetime.utcnow() - created_at).days
        
        if age_days <= self.retention_days:
            return {'action': 'retain', 'age_days': age_days}
        elif self.archive_enabled and age_days <= self.retention_days * 2:
            return {'action': 'archive', 'age_days': age_days}
        else:
            return {'action': 'delete', 'age_days': age_days}
    
    def execute_retention_policy(self, data_items: List[Dict]) -> Dict:
        """Execute retention policy on data items"""
        results = {'retained': 0, 'archived': 0, 'deleted': 0}
        
        for item in data_items:
            if 'created_at' not in item:
                continue
            
            created_at = datetime.fromisoformat(item['created_at']) if isinstance(item['created_at'], str) else item['created_at']
            action = self.check_retention(item.get('type', 'unknown'), created_at)
            results[action['action'] + 'd'] = results.get(action['action'] + 'd', 0) + 1
        
        self.archival_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        })
        
        return results


# ==================== FAULT SIMULATION ====================

class FaultSimulator:
    """Simulate faults to test alert triggers"""
    
    def __init__(self, kpi_tracker, alert_manager):
        self.kpi_tracker = kpi_tracker
        self.alert_manager = alert_manager
        self.simulation_log: List[Dict] = []
    
    def simulate_high_event_lag(self, lag_seconds: float = 90):
        """Simulate high event processing lag (>60s threshold)"""
        logger.info(f"FAULT_SIMULATION: Simulating event lag of {lag_seconds}s")
        
        self.kpi_tracker.update_event_lag(lag_seconds)
        alert = self.alert_manager.check_and_alert(
            'event_lag',
            lag_seconds,
            self.alert_manager.thresholds.get('event_lag_critical', 60)
        )
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'simulation_type': 'high_event_lag',
            'value': lag_seconds,
            'alert_triggered': alert is not None,
            'alert_details': alert
        }
        self.simulation_log.append(result)
        return result
    
    def simulate_high_error_rate(self, error_rate: float = 0.05):
        """Simulate high error rate (>2% threshold)"""
        logger.info(f"FAULT_SIMULATION: Simulating error rate of {error_rate*100}%")
        
        # Simulate with 100 total requests
        error_count = int(error_rate * 100)
        self.kpi_tracker.update_error_rate(error_count, 100)
        
        alert = self.alert_manager.check_and_alert(
            'error_rate',
            error_rate * 100,  # Convert to percentage
            self.alert_manager.thresholds.get('error_rate_critical', 2.0)
        )
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'simulation_type': 'high_error_rate',
            'value': error_rate,
            'alert_triggered': alert is not None,
            'alert_details': alert
        }
        self.simulation_log.append(result)
        return result
    
    def simulate_suspicious_transactions(self, count: int = 60):
        """Simulate suspicious transaction spike"""
        logger.info(f"FAULT_SIMULATION: Simulating {count} suspicious transactions")
        
        self.kpi_tracker.update_suspicious_count(count)
        alert = self.alert_manager.check_and_alert(
            'suspicious_transactions',
            count,
            self.alert_manager.thresholds.get('suspicious_transactions_critical', 50)
        )
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'simulation_type': 'suspicious_transactions',
            'value': count,
            'alert_triggered': alert is not None,
            'alert_details': alert
        }
        self.simulation_log.append(result)
        return result
    
    def simulate_rate_limit_attack(self, rate_limiter, num_requests: int = 200):
        """Simulate rate limit bypass attempt"""
        logger.info(f"FAULT_SIMULATION: Simulating {num_requests} requests from single IP")
        
        violations = 0
        for i in range(num_requests):
            allowed, _, _ = rate_limiter.check_rate_limit('attacker_ip_192.168.1.100', '/api/projects/')
            if not allowed:
                violations += 1
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'simulation_type': 'rate_limit_attack',
            'total_requests': num_requests,
            'violations': violations,
            'rate_limiter_stats': rate_limiter.get_stats()
        }
        self.simulation_log.append(result)
        return result
    
    def get_simulation_log(self) -> List[Dict]:
        """Get simulation history"""
        return self.simulation_log


# ==================== METRICS ENDPOINT ====================

def create_metrics_response(kpi_tracker, alert_manager, rate_limiter) -> str:
    """Create Prometheus-compatible metrics response"""
    metrics = []
    
    # KPI Summary
    summary = kpi_tracker.get_summary()
    
    # Event processing lag
    metrics.append(f'# HELP event_processing_lag_seconds Current event processing lag')
    metrics.append(f'# TYPE event_processing_lag_seconds gauge')
    metrics.append(f'event_processing_lag_seconds {summary["event_processing_lag"]["current"]:.2f}')
    
    # Error rate
    metrics.append(f'# HELP error_rate_percent Current error rate percentage')
    metrics.append(f'# TYPE error_rate_percent gauge')
    metrics.append(f'error_rate_percent {summary["error_rate"]["current"]:.2f}')
    
    # API latency
    metrics.append(f'# HELP api_response_latency_ms API response latency in milliseconds')
    metrics.append(f'# TYPE api_response_latency_ms gauge')
    metrics.append(f'api_response_latency_ms {summary["api_response_latency"]["current"]:.2f}')
    
    # Suspicious transactions
    metrics.append(f'# HELP suspicious_transactions_total Total suspicious transactions flagged')
    metrics.append(f'# TYPE suspicious_transactions_total counter')
    metrics.append(f'suspicious_transactions_total {summary["suspicious_transactions"]["current"]}')
    
    # Alerts
    recent_alerts = alert_manager.get_recent_alerts(100)
    critical_count = len([a for a in recent_alerts if a.get('severity') == 'critical'])
    warning_count = len([a for a in recent_alerts if a.get('severity') == 'warning'])
    
    metrics.append(f'# HELP alerts_total Total alerts by severity')
    metrics.append(f'# TYPE alerts_total counter')
    metrics.append(f'alerts_total{{severity="critical"}} {critical_count}')
    metrics.append(f'alerts_total{{severity="warning"}} {warning_count}')
    
    # Rate limiting
    rate_stats = rate_limiter.get_stats()
    metrics.append(f'# HELP rate_limit_violations_total Total rate limit violations')
    metrics.append(f'# TYPE rate_limit_violations_total counter')
    metrics.append(f'rate_limit_violations_total {rate_stats["total_violations"]}')
    
    return '\n'.join(metrics)


# ==================== GLOBAL INSTANCES ====================

admin_auth = AdminAuthManager()
rate_limiter = RateLimiter(requests_per_minute=100, burst_size=20)
data_retention = DataRetentionManager(retention_days=90)


# ==================== DECORATOR FOR AUTH ====================

def require_admin_auth(func):
    """Decorator to require admin authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In real implementation, extract token from request headers
        token = kwargs.pop('auth_token', None)
        
        if not token:
            raise PermissionError("Authentication required")
        
        session = admin_auth.validate_session(token)
        if not session:
            raise PermissionError("Invalid or expired session")
        
        kwargs['admin_session'] = session
        return func(*args, **kwargs)
    
    return wrapper


def require_rate_limit(func):
    """Decorator to enforce rate limiting"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In real implementation, extract IP from request
        identifier = kwargs.pop('client_ip', 'unknown')
        endpoint = kwargs.pop('endpoint', '/')
        
        allowed, remaining, reset = rate_limiter.check_rate_limit(identifier, endpoint)
        
        if not allowed:
            raise Exception(f"Rate limit exceeded. Try again in {reset} seconds")
        
        kwargs['rate_limit_remaining'] = remaining
        return func(*args, **kwargs)
    
    return wrapper


# ==================== DEMO ====================

if __name__ == '__main__':
    from monitoring import kpi_tracker, alert_manager
    
    print("=== Security Controls Demo ===\n")
    
    # Test admin auth
    print("1. Admin Authentication:")
    token = admin_auth.authenticate('admin', 'dao_admin_2024', '192.168.1.1')
    print(f"   Login successful: {token is not None}")
    print(f"   Session valid: {admin_auth.validate_session(token) is not None}")
    
    # Test rate limiting
    print("\n2. Rate Limiting:")
    for i in range(25):
        allowed, remaining, _ = rate_limiter.check_rate_limit('test_ip', '/api/test')
        if not allowed:
            print(f"   Rate limited after {i+1} requests")
            break
    print(f"   Violations: {len(rate_limiter.get_violations())}")
    
    # Test fault simulation
    print("\n3. Fault Simulation:")
    fault_sim = FaultSimulator(kpi_tracker, alert_manager)
    
    # Simulate high event lag
    result = fault_sim.simulate_high_event_lag(90)
    print(f"   Event lag alert: {result['alert_triggered']}")
    
    # Simulate high error rate
    result = fault_sim.simulate_high_error_rate(0.05)
    print(f"   Error rate alert: {result['alert_triggered']}")
    
    # Simulate rate limit attack
    result = fault_sim.simulate_rate_limit_attack(rate_limiter, 150)
    print(f"   Rate limit violations: {result['violations']}")
    
    # Test metrics endpoint
    print("\n4. Metrics Endpoint:")
    metrics = create_metrics_response(kpi_tracker, alert_manager, rate_limiter)
    print(f"   Metrics lines: {len(metrics.split(chr(10)))}")
    
    # Access logs
    print("\n5. Access Logs:")
    logs = admin_auth.get_access_logs(5)
    for log in logs:
        print(f"   {log['timestamp']}: {log['action']} - {log['username']}")
    
    print("\n✅ Security controls operational")
